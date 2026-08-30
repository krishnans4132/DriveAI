"""PyTorch runtime for the trained DriveAlert MobileNetV3-Small models."""

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
EYE_CHECKPOINT = PROJECT_ROOT / "ml/models/eye_v3/drivealert_eye_v3_best.pth"
MOUTH_CHECKPOINT = PROJECT_ROOT / "ml/models/mouth_v1/drivealert_mouth_v1_best.pth"

IMAGE_NET_MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
IMAGE_NET_STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)
EYE_THRESHOLD = 0.060
YAWN_THRESHOLD = 0.355
MOUTH_CLASSES = ("not_yawn", "talking", "yawn")


def _build_model(output_features: int) -> nn.Module:
    model = models.mobilenet_v3_small(weights=None)
    input_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(input_features, output_features)
    return model


def _load_model(path: Path, output_features: int) -> nn.Module:
    if not path.is_file():
        raise FileNotFoundError(f"Model checkpoint is missing: {path}")
    checkpoint: dict[str, Any] = torch.load(
        path,
        map_location="cpu",
        weights_only=False,
    )
    model = _build_model(output_features)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()
    return model


def preprocess_bgr(crop: np.ndarray, width: int, height: int) -> torch.Tensor:
    """Match the RGB/ImageNet preprocessing used in both training notebooks."""
    if crop is None or crop.size == 0:
        raise ValueError("Cannot preprocess an empty crop")
    if crop.shape[:2] != (height, width):
        interpolation = cv2.INTER_AREA if crop.shape[1] > width else cv2.INTER_CUBIC
        crop = cv2.resize(crop, (width, height), interpolation=interpolation)
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    normalized = (rgb - IMAGE_NET_MEAN) / IMAGE_NET_STD
    nchw = np.ascontiguousarray(normalized.transpose(2, 0, 1)[None, ...])
    return torch.from_numpy(nchw)


class MobileNetFatigueRuntime:
    """Load both trained heads once and safely reuse them across HTTP requests."""

    def __init__(self) -> None:
        torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
        self.eye_model = _load_model(EYE_CHECKPOINT, 1)
        self.mouth_model = _load_model(MOUTH_CHECKPOINT, len(MOUTH_CLASSES))
        self._lock = Lock()

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "architecture": "MobileNetV3-Small",
            "member_id": "CB.SC.U4CSE23628",
            "eye_threshold": EYE_THRESHOLD,
            "yawn_threshold": YAWN_THRESHOLD,
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
        if yawn_probability >= YAWN_THRESHOLD:
            mouth_label = "yawn"
        else:
            mouth_label = MOUTH_CLASSES[int(np.argmax(mouth_probabilities[:2]))]

        return {
            "eye_closed_probability": eye_probability,
            "eye_state": "closed" if eye_probability >= EYE_THRESHOLD else "open",
            "mouth_state": mouth_label,
            "mouth_probabilities": {
                label: float(probability)
                for label, probability in zip(MOUTH_CLASSES, mouth_probabilities)
            },
            "yawn_probability": yawn_probability,
        }
