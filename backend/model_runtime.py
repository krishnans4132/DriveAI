"""PyTorch runtimes for the three trained DriveAlert model families."""

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any

import cv2
import numpy as np
import torch
from torch import nn
from torchvision import models


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_NET_MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
IMAGE_NET_STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)
MOUTH_CLASSES = ("not_yawn", "talking", "yawn")

MODEL_CONFIGS: dict[str, dict[str, Any]] = {
    "mobilenet": {
        "name": "MobileNetV3-Small",
        "architecture": "mobilenet_v3_small",
        "member_id": "CB.SC.U4CSE23628",
        "eye_checkpoint": PROJECT_ROOT / "ml/models/eye_v3/drivealert_eye_v3_best.pth",
        "mouth_checkpoint": PROJECT_ROOT / "ml/models/mouth_v1/drivealert_mouth_v1_best.pth",
        "eye_threshold": 0.060,
        "yawn_threshold": 0.355,
    },
    "efficientnet": {
        "name": "EfficientNet-B0",
        "architecture": "efficientnet_b0",
        "member_id": "CB.SC.U4CSE23603",
        "eye_checkpoint": PROJECT_ROOT / "ml/models/efficientnet_b0/eye/eye_best.pth",
        "mouth_checkpoint": PROJECT_ROOT / "ml/models/efficientnet_b0/mouth/mouth_best.pth",
        "eye_threshold": 0.040,
        "yawn_threshold": 0.605,
    },
    "resnet": {
        "name": "ResNet-18",
        "architecture": "resnet18",
        "member_id": "CB.SC.U4CSE23717",
        "eye_checkpoint": PROJECT_ROOT / "ml/models/resnet18/eye/eye_best.pth",
        "mouth_checkpoint": PROJECT_ROOT / "ml/models/resnet18/mouth/mouth_best.pth",
        "eye_threshold": 0.025,
        "yawn_threshold": 0.650,
    },
}
DEFAULT_MODEL = "mobilenet"
EYE_CHECKPOINT = MODEL_CONFIGS[DEFAULT_MODEL]["eye_checkpoint"]
MOUTH_CHECKPOINT = MODEL_CONFIGS[DEFAULT_MODEL]["mouth_checkpoint"]


def _build_model(architecture: str, output_features: int) -> nn.Module:
    if architecture == "mobilenet_v3_small":
        model = models.mobilenet_v3_small(weights=None)
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, output_features)
    elif architecture == "efficientnet_b0":
        model = models.efficientnet_b0(weights=None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, output_features)
    elif architecture == "resnet18":
        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, output_features)
    else:
        raise ValueError(f"Unsupported model architecture: {architecture}")
    return model


def _load_model(path: Path, architecture: str, output_features: int) -> nn.Module:
    if not path.is_file():
        raise FileNotFoundError(f"Model checkpoint is missing: {path}")
    checkpoint: dict[str, Any] = torch.load(path, map_location="cpu", weights_only=False)
    model = _build_model(architecture, output_features)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()
    return model


def preprocess_bgr(crop: np.ndarray, width: int, height: int) -> torch.Tensor:
    """Match the RGB/ImageNet preprocessing used in the training notebooks."""
    if crop is None or crop.size == 0:
        raise ValueError("Cannot preprocess an empty crop")
    if crop.shape[:2] != (height, width):
        interpolation = cv2.INTER_AREA if crop.shape[1] > width else cv2.INTER_CUBIC
        crop = cv2.resize(crop, (width, height), interpolation=interpolation)
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    normalized = (rgb - IMAGE_NET_MEAN) / IMAGE_NET_STD
    nchw = np.ascontiguousarray(normalized.transpose(2, 0, 1)[None, ...])
    return torch.from_numpy(nchw)


def available_models() -> list[dict[str, object]]:
    return [
        {
            "key": key,
            "name": config["name"],
            "available": config["eye_checkpoint"].is_file() and config["mouth_checkpoint"].is_file(),
        }
        for key, config in MODEL_CONFIGS.items()
    ]


class FatigueModelRuntime:
    """Load the chosen architecture's eye and mouth heads on first use."""

    def __init__(self, model_key: str = DEFAULT_MODEL) -> None:
        if model_key not in MODEL_CONFIGS:
            raise ValueError(f"Unknown model: {model_key}")
        self.model_key = model_key
        self.config = MODEL_CONFIGS[model_key]
        torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
        self.eye_model = _load_model(self.config["eye_checkpoint"], self.config["architecture"], 1)
        self.mouth_model = _load_model(
            self.config["mouth_checkpoint"], self.config["architecture"], len(MOUTH_CLASSES)
        )
        self._lock = Lock()

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "model_key": self.model_key,
            "architecture": self.config["name"],
            "member_id": self.config["member_id"],
            "eye_threshold": self.config["eye_threshold"],
            "yawn_threshold": self.config["yawn_threshold"],
            "runtime": "PyTorch CPU",
            "models_loaded": True,
        }

    def predict(self, eye_crop: np.ndarray, mouth_crop: np.ndarray) -> dict[str, object]:
        eye_input = preprocess_bgr(eye_crop, width=192, height=96)
        mouth_input = preprocess_bgr(mouth_crop, width=160, height=96)
        with self._lock, torch.inference_mode():
            eye_logit = self.eye_model(eye_input).squeeze()
            mouth_logits = self.mouth_model(mouth_input).squeeze(0)
            eye_probability = float(torch.sigmoid(eye_logit).item())
            mouth_probabilities = torch.softmax(mouth_logits, dim=0).tolist()

        yawn_probability = float(mouth_probabilities[2])
        if yawn_probability >= self.config["yawn_threshold"]:
            mouth_label = "yawn"
        else:
            mouth_label = MOUTH_CLASSES[int(np.argmax(mouth_probabilities[:2]))]
        return {
            "eye_closed_probability": eye_probability,
            "eye_state": "closed" if eye_probability >= self.config["eye_threshold"] else "open",
            "mouth_state": mouth_label,
            "mouth_probabilities": {
                label: float(probability)
                for label, probability in zip(MOUTH_CLASSES, mouth_probabilities)
            },
            "yawn_probability": yawn_probability,
            "model_key": self.model_key,
            "architecture": self.config["name"],
        }


# Kept as a compatibility name for existing callers and tests.
MobileNetFatigueRuntime = FatigueModelRuntime
