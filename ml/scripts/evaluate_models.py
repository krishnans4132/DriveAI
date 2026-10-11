#!/usr/bin/env python3
"""Evaluate all DriveAlert checkpoints on the untouched participant-disjoint test set.

Uses the same deterministic image resize and ImageNet normalization as the
training notebooks. Thresholds come from backend/model_runtime.py and are never
selected using test-set results. The resulting labels remain provisional weak
labels; see the output JSON and README for interpretation limits.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.model_runtime import MODEL_CONFIGS, MOUTH_CLASSES, _build_model  # noqa: E402


EYE_LABELS = {"open": 0, "closed": 1}
MOUTH_LABELS = {name: index for index, name in enumerate(MOUTH_CLASSES)}
NORMALIZE = transforms.Normalize(
    mean=(0.485, 0.456, 0.406),
    std=(0.229, 0.224, 0.225),
)
EYE_TRANSFORM = transforms.Compose([
    transforms.Resize((96, 192), antialias=True),
    transforms.ToTensor(),
    NORMALIZE,
])
MOUTH_TRANSFORM = transforms.Compose([
    transforms.Resize((96, 160), antialias=True),
    transforms.ToTensor(),
    NORMALIZE,
])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Back-to-back evaluation of all three DriveAlert model families."
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        required=True,
        help="Processed dataset folder containing splits/ and images/ (the v3 package).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "ml/evaluation",
        help="Directory for metrics JSON and row-level prediction CSVs.",
    )
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument(
        "--device",
        default="auto",
        choices=("auto", "cpu", "cuda"),
        help="Inference device. Defaults to CUDA when available, otherwise CPU.",
    )
    return parser.parse_args()


def read_split(dataset_dir: Path, task: str, split: str) -> list[dict[str, str]]:
    path = dataset_dir / "splits" / f"{task}_{split}_provisional.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Required split file not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"Split file has no rows: {path}")
    required = {"filepath", "label", "person_id", "dataset", "is_ground_truth"}
    missing = required - rows[0].keys()
    if missing:
        raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
    if len({row["filepath"] for row in rows}) != len(rows):
        raise ValueError(f"Duplicate image paths found in {path}")
    return rows


def verify_splits(dataset_dir: Path, task: str) -> dict[str, list[dict[str, str]]]:
    partitions = {name: read_split(dataset_dir, task, name) for name in ("train", "val", "test")}
    people = {
        name: {(row["dataset"], row["person_id"]) for row in rows}
        for name, rows in partitions.items()
    }
    for left, right in (("train", "val"), ("train", "test"), ("val", "test")):
        overlap = people[left] & people[right]
        if overlap:
            raise ValueError(
                f"Participant leakage in {task}: {left}/{right} share "
                f"{len(overlap)} dataset/person_id pair(s)."
            )
    test_rows = partitions["test"]
    allowed = EYE_LABELS if task == "eye" else MOUTH_LABELS
    unknown = sorted({row["label"] for row in test_rows} - allowed.keys())
    if unknown:
        raise ValueError(f"Unexpected {task} test labels: {unknown}")
    return partitions


def image_batch(rows: list[dict[str, str]], dataset_dir: Path, task: str) -> torch.Tensor:
    transform = EYE_TRANSFORM if task == "eye" else MOUTH_TRANSFORM
    tensors = []
    for row in rows:
        path = dataset_dir / row["filepath"]
        if not path.is_file():
            raise FileNotFoundError(f"Image listed in test CSV is missing: {path}")
        with Image.open(path) as image:
            tensors.append(transform(image.convert("RGB")))
    return torch.stack(tensors)


def load_checkpoint(path: Path, architecture: str, output_features: int) -> torch.nn.Module:
    if not path.is_file():
        raise FileNotFoundError(
            f"Checkpoint missing: {path}\n"
            "Read README.md for instructions to obtain/extract the model artifacts."
        )
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    model = _build_model(architecture, output_features)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    return model.eval()


def _binary_metrics(targets: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    predictions = (scores >= threshold).astype(np.int64)
    tp = int(np.sum((targets == 1) & (predictions == 1)))
    fp = int(np.sum((targets == 0) & (predictions == 1)))
    tn = int(np.sum((targets == 0) & (predictions == 0)))
    fn = int(np.sum((targets == 1) & (predictions == 0)))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    order = np.argsort(-scores, kind="mergesort")
    sorted_targets = targets[order]
    positive_count = int(targets.sum())
    if positive_count and positive_count < len(targets):
        sorted_scores = scores[order]
        tie_groups = []
        start = 0
        while start < len(order):
            end = start + 1
            while end < len(order) and sorted_scores[end] == sorted_scores[start]:
                end += 1
            tie_groups.append((start, end))
            start = end
        cumulative_tp = 0
        cumulative_fp = 0
        ap = 0.0
        for start, end in tie_groups:
            group_positives = int(sorted_targets[start:end].sum())
            group_size = end - start
            cumulative_tp += group_positives
            cumulative_fp += group_size - group_positives
            ap += (group_positives / positive_count) * (
                cumulative_tp / (cumulative_tp + cumulative_fp)
            )
        # Mann-Whitney AUC with average ranks for tied scores.
        rank_sum_positive = 0.0
        for start, end in tie_groups:
            average_rank = ((len(targets) - end + 1) + (len(targets) - start)) / 2
            rank_sum_positive += average_rank * float(sorted_targets[start:end].sum())
        negative_count = len(targets) - positive_count
        auc = (rank_sum_positive - positive_count * (positive_count + 1) / 2) / (positive_count * negative_count)
    else:
        ap = auc = None

    return {
        "samples": int(len(targets)),
        "threshold": float(threshold),
        "average_precision": ap,
        "roc_auc": auc,
        "balanced_accuracy": (recall + specificity) / 2,
        "positive_precision": precision,
        "positive_recall": recall,
        "negative_specificity": specificity,
        "positive_f1": f1,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


def _multiclass_metrics(
    targets: np.ndarray, probabilities: np.ndarray, predictions: np.ndarray
) -> dict[str, Any]:
    confusion = np.zeros((len(MOUTH_CLASSES), len(MOUTH_CLASSES)), dtype=np.int64)
    per_class: dict[str, Any] = {}
    aps, aucs, recalls = [], [], []
    for class_index, class_name in enumerate(MOUTH_CLASSES):
        binary = (targets == class_index).astype(np.int64)
        class_recall = float(np.mean(predictions[targets == class_index] == class_index)) if np.any(targets == class_index) else 0.0
        predicted_count = int(np.sum(predictions == class_index))
        true_positive_count = int(np.sum((targets == class_index) & (predictions == class_index)))
        class_precision = true_positive_count / predicted_count if predicted_count else 0.0
        class_metrics = _binary_metrics(binary, probabilities[:, class_index], 0.5)
        per_class[class_name] = {
            "support": int(binary.sum()),
            "average_precision": class_metrics["average_precision"],
            "precision": class_precision,
            "recall": class_recall,
            "f1": (2 * class_precision * class_recall /
                   (class_precision + class_recall))
                  if class_precision + class_recall else 0.0,
        }
        if class_metrics["average_precision"] is not None:
            aps.append(class_metrics["average_precision"])
        if class_metrics["roc_auc"] is not None:
            aucs.append(class_metrics["roc_auc"])
        recalls.append(class_recall)
    for target, prediction in zip(targets, predictions):
        confusion[int(target), int(prediction)] += 1
    accuracy = float(np.mean(targets == predictions))
    yawn_index = MOUTH_LABELS["yawn"]
    yawn_tp = int(confusion[yawn_index, yawn_index])
    yawn_fn = int(confusion[yawn_index, :].sum() - yawn_tp)
    yawn_fp = int(confusion[:, yawn_index].sum() - yawn_tp)
    yawn_tn = int(len(targets) - yawn_tp - yawn_fn - yawn_fp)
    yawn_precision = yawn_tp / (yawn_tp + yawn_fp) if yawn_tp + yawn_fp else 0.0
    yawn_recall = yawn_tp / (yawn_tp + yawn_fn) if yawn_tp + yawn_fn else 0.0
    yawn_specificity = yawn_tn / (yawn_tn + yawn_fp) if yawn_tn + yawn_fp else 0.0
    yawn_f1 = (
        2 * yawn_precision * yawn_recall / (yawn_precision + yawn_recall)
        if yawn_precision + yawn_recall else 0.0
    )
    return {
        "samples": int(len(targets)),
        "macro_average_precision": float(np.mean(aps)) if aps else None,
        "macro_roc_auc": float(np.mean(aucs)) if aucs else None,
        "macro_f1": float(np.mean([item["f1"] for item in per_class.values()])),
        "balanced_accuracy": float(np.mean(recalls)),
        "accuracy": accuracy,
        "per_class": per_class,
        "yawn_vs_rest": {
            "precision": yawn_precision,
            "recall": yawn_recall,
            "specificity": yawn_specificity,
            "f1": yawn_f1,
            "balanced_accuracy": (yawn_recall + yawn_specificity) / 2,
            "tp": yawn_tp,
            "fp": yawn_fp,
            "tn": yawn_tn,
            "fn": yawn_fn,
        },
        "confusion_matrix_rows_true_columns_predicted": confusion.tolist(),
    }


def _save_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    dataset_dir = args.dataset_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be a positive integer")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but PyTorch cannot access CUDA.")
    device = torch.device(
        "cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu"
    )
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
    output_dir.mkdir(parents=True, exist_ok=True)

    partitions = {task: verify_splits(dataset_dir, task) for task in ("eye", "mouth")}
    test_rows = {task: partitions[task]["test"] for task in partitions}
    ground_truth = all(row["is_ground_truth"].strip().lower() in {"true", "1", "yes"}
                       for rows in test_rows.values() for row in rows)
    results: dict[str, Any] = {
        "evaluation": "participant-disjoint held-out test; back-to-back comparison",
        "dataset_dir": str(dataset_dir),
        "device": str(device),
        "thresholds_selected_on_test": False,
        "labels_are_ground_truth": ground_truth,
        "label_status": "independent ground truth" if ground_truth else "provisional weak labels",
        "participant_disjoint_verified": True,
        "models": {},
    }
    csv_outputs: dict[str, list[dict[str, Any]]] = {}

    for model_key, config in MODEL_CONFIGS.items():
        print(f"Evaluating {config['name']} (eye + mouth)...", flush=True)
        eye_model = load_checkpoint(config["eye_checkpoint"], config["architecture"], 1).to(device)
        mouth_model = load_checkpoint(config["mouth_checkpoint"], config["architecture"], len(MOUTH_CLASSES)).to(device)

        model_result: dict[str, Any] = {"architecture": config["name"], "eye": {}, "mouth": {}}
        for task, model in (("eye", eye_model), ("mouth", mouth_model)):
            rows = test_rows[task]
            labels = EYE_LABELS if task == "eye" else MOUTH_LABELS
            targets = np.asarray([labels[row["label"]] for row in rows], dtype=np.int64)
            all_scores: list[np.ndarray] = []
            elapsed = 0.0
            count = 0
            with torch.inference_mode():
                for offset in range(0, len(rows), args.batch_size):
                    batch_rows = rows[offset:offset + args.batch_size]
                    batch = image_batch(batch_rows, dataset_dir, task).to(device)
                    start = time.perf_counter()
                    logits = model(batch)
                    if device.type == "cuda":
                        torch.cuda.synchronize(device)
                    elapsed += time.perf_counter() - start
                    count += len(batch_rows)
                    scores = torch.sigmoid(logits.reshape(-1, 1)) if task == "eye" else torch.softmax(logits, dim=1)
                    all_scores.append(scores.cpu().numpy())
            scores = np.concatenate(all_scores, axis=0)
            model_result[task]["inference_latency_ms_per_image"] = elapsed * 1000 / max(count, 1)
            model_result[task]["throughput_images_per_second"] = count / elapsed if elapsed else None

            prediction_rows: list[dict[str, Any]] = []
            if task == "eye":
                probability = scores[:, 0]
                threshold = float(config["eye_threshold"])
                model_result[task]["metrics"] = _binary_metrics(targets, probability, threshold)
                predictions = (probability >= threshold).astype(np.int64)
                for row, target, score, prediction in zip(rows, targets, probability, predictions):
                    prediction_rows.append({
                        "filepath": row["filepath"], "dataset": row["dataset"],
                        "person_id": row["person_id"], "true_label": row["label"],
                        "closed_probability": float(score), "threshold": threshold,
                        "predicted_label": "closed" if prediction else "open",
                    })
                by_dataset = {}
                for dataset_name in sorted({row["dataset"] for row in rows}):
                    indices = np.asarray([i for i, row in enumerate(rows) if row["dataset"] == dataset_name])
                    by_dataset[dataset_name] = _binary_metrics(targets[indices], probability[indices], threshold)
                model_result[task]["metrics_by_dataset"] = by_dataset
            else:
                threshold = float(config["yawn_threshold"])
                predictions = np.argmax(scores[:, :2], axis=1)
                yawn_mask = scores[:, MOUTH_LABELS["yawn"]] >= threshold
                predictions[yawn_mask] = MOUTH_LABELS["yawn"]
                model_result[task]["decision_threshold_yawn"] = threshold
                model_result[task]["metrics"] = _multiclass_metrics(targets, scores, predictions)
                for row, target, probabilities, prediction in zip(rows, targets, scores, predictions):
                    prediction_rows.append({
                        "filepath": row["filepath"], "dataset": row["dataset"],
                        "person_id": row["person_id"], "true_label": row["label"],
                        "not_yawn_probability": float(probabilities[0]),
                        "talking_probability": float(probabilities[1]),
                        "yawn_probability": float(probabilities[2]),
                        "yawn_threshold": threshold,
                        "predicted_label": MOUTH_CLASSES[int(prediction)],
                    })
            csv_outputs[f"{model_key}_{task}_predictions.csv"] = prediction_rows
        results["models"][model_key] = model_result

    results_path = output_dir / "model_evaluation_metrics.json"
    results_path.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for filename, rows in csv_outputs.items():
        _save_csv(output_dir / filename, rows)
    print(f"Done. Metrics and prediction CSVs saved to: {output_dir}")
    print(f"Labels used: {results['label_status']}. Do not describe weak-label metrics as ground-truth accuracy.")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Evaluation stopped: {exc}") from exc
