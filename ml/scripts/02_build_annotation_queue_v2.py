"""Build a diverse, blinded annotation queue from processed_data_v2.

EAR and MAR are used only to prioritize a broad range of visual examples. They
are never copied into the human labels. The queue retains hidden audit metadata
for later analysis, while the annotation UI exposes only the crops and task
instructions to the annotator.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_ROOT = Path("ml/processed_data_v2")


def metric_deciles(df: pd.DataFrame, metric: str) -> pd.Series:
    """Return stable 0..9 ranks within each source dataset."""

    def rank_group(values: pd.Series) -> pd.Series:
        percentile = values.rank(method="average", pct=True)
        return np.minimum((percentile * 10).astype(int), 9)

    return df.groupby("dataset", group_keys=False)[metric].transform(
        rank_group
    )


def quality_multiplier(df: pd.DataFrame) -> pd.Series:
    """Keep hard lighting/blur examples present without letting them dominate."""
    brightness_hard = (df["brightness"] < 45) | (df["brightness"] > 190)
    blur_hard = df["blur_score"] < 12
    return pd.Series(
        np.where(brightness_hard | blur_hard, 1.35, 1.0),
        index=df.index,
        dtype=float,
    )


def inverse_person_frequency(df: pd.DataFrame) -> pd.Series:
    counts = df.groupby("person_id")["person_id"].transform("size")
    return 1.0 / np.sqrt(counts.astype(float))


def sample_partition(
    df: pd.DataFrame,
    count: int,
    weights: pd.Series,
    seed: int,
) -> pd.DataFrame:
    count = min(count, len(df))
    if count <= 0:
        return df.iloc[0:0].copy()
    return df.sample(
        n=count,
        replace=False,
        weights=weights.loc[df.index],
        random_state=seed,
    ).copy()


def allocate_counts(total: int, shares: dict[str, float]) -> dict[str, int]:
    raw = {name: total * share for name, share in shares.items()}
    allocated = {name: int(value) for name, value in raw.items()}
    remainder = total - sum(allocated.values())
    order = sorted(
        shares,
        key=lambda name: raw[name] - allocated[name],
        reverse=True,
    )
    for name in order[:remainder]:
        allocated[name] += 1
    return allocated


def build_eye_queue(
    manifest: pd.DataFrame,
    total: int,
    seed: int,
) -> pd.DataFrame:
    eye = manifest[manifest["region"] == "eye"].copy()
    eye["selection_metric"] = "ear_mean"
    eye["selection_metric_value"] = eye["ear_mean"]
    eye["selection_decile"] = metric_deciles(eye, "ear_mean")

    # Lower EAR ranks receive more sampling weight so true closures and
    # transitional eyelid positions are not drowned out by ordinary open eyes.
    decile_weight = eye["selection_decile"].map(
        {
            0: 5.0,
            1: 3.0,
            2: 1.8,
            3: 1.3,
            4: 1.0,
            5: 1.0,
            6: 1.0,
            7: 1.0,
            8: 1.0,
            9: 1.0,
        }
    )
    weights = (
        decile_weight
        * quality_multiplier(eye)
        * inverse_person_frequency(eye)
    )

    # Equal dataset representation prevents the larger YawDD portion from
    # overwhelming UTA-RLDD's lower-light and varied-pose examples.
    quotas = allocate_counts(
        total,
        {"uta_rldd": 0.50, "yawdd": 0.50},
    )
    chunks = []
    for offset, (dataset, quota) in enumerate(quotas.items()):
        partition = eye[eye["dataset"] == dataset]
        chunks.append(
            sample_partition(
                partition,
                quota,
                weights,
                seed + offset,
            )
        )

    return pd.concat(chunks, ignore_index=True)


def build_mouth_queue(
    manifest: pd.DataFrame,
    total: int,
    seed: int,
) -> pd.DataFrame:
    mouth = manifest[manifest["region"] == "mouth"].copy()
    mouth["selection_metric"] = "mar"
    mouth["selection_metric_value"] = mouth["mar"]
    mouth["selection_decile"] = metric_deciles(mouth, "mar")

    # High MAR ranks are deliberately enriched because yawns are rare in the
    # uniformly sampled source frames. Session/clip labels remain weak hints,
    # never human targets.
    decile_weight = mouth["selection_decile"].map(
        {
            0: 1.0,
            1: 1.0,
            2: 1.0,
            3: 1.0,
            4: 1.0,
            5: 1.0,
            6: 1.2,
            7: 1.8,
            8: 3.0,
            9: 5.0,
        }
    )
    weak_label_weight = mouth["source_label"].map(
        {
            "yawning": 1.8,
            "talking_yawning": 1.8,
            "talking": 1.2,
            "normal": 1.0,
            "alert": 1.0,
            "low_vigilance": 1.0,
            "drowsy": 1.1,
        }
    ).fillna(1.0)
    weights = (
        decile_weight
        * weak_label_weight
        * quality_multiplier(mouth)
        * inverse_person_frequency(mouth)
    )

    # YawDD contains explicit yawn/talking clips. UTA remains valuable for
    # negatives, low light, pose, and real-life domain coverage.
    quotas = allocate_counts(
        total,
        {"uta_rldd": 0.30, "yawdd": 0.70},
    )
    chunks = []
    for offset, (dataset, quota) in enumerate(quotas.items()):
        partition = mouth[mouth["dataset"] == dataset]
        chunks.append(
            sample_partition(
                partition,
                quota,
                weights,
                seed + 100 + offset,
            )
        )

    selected = pd.concat(chunks, ignore_index=True)
    return attach_temporal_context(selected, mouth)


def attach_temporal_context(
    selected: pd.DataFrame,
    all_mouth: pd.DataFrame,
) -> pd.DataFrame:
    context_lookup: dict[str, list[str]] = {}
    for _, group in all_mouth.groupby("video_id", sort=False):
        group = group.sort_values("frame_idx").reset_index(drop=True)
        paths = group["filepath"].tolist()
        for index, filepath in enumerate(paths):
            context_lookup[filepath] = [
                paths[position]
                for position in range(max(0, index - 2), min(len(paths), index + 3))
            ]

    selected["context_paths"] = selected["filepath"].map(
        lambda filepath: json.dumps(context_lookup[filepath])
    )
    return selected


def finalize_queue(
    eye: pd.DataFrame,
    mouth: pd.DataFrame,
    seed: int,
) -> pd.DataFrame:
    eye = eye.copy()
    mouth = mouth.copy()
    eye["task"] = "eye"
    mouth["task"] = "mouth"
    eye["context_paths"] = eye["filepath"].map(
        lambda filepath: json.dumps([filepath])
    )

    eye = eye.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    mouth = mouth.sample(frac=1.0, random_state=seed + 1).reset_index(drop=True)
    eye["annotation_id"] = [
        f"eye_{index:06d}" for index in range(1, len(eye) + 1)
    ]
    mouth["annotation_id"] = [
        f"mouth_{index:06d}" for index in range(1, len(mouth) + 1)
    ]

    queue = pd.concat([eye, mouth], ignore_index=True)
    queue["queue_version"] = 1

    columns = [
        "annotation_id",
        "task",
        "filepath",
        "context_paths",
        "dataset",
        "person_id",
        "video_id",
        "frame_idx",
        "timestamp_ms",
        "source_label",
        "selection_metric",
        "selection_metric_value",
        "selection_decile",
        "brightness",
        "blur_score",
        "rotation_metadata",
        "queue_version",
    ]
    return queue[columns]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--eye-count", type=int, default=6000)
    parser.add_argument("--mouth-count", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.eye_count <= 0 or args.mouth_count <= 0:
        raise ValueError("Annotation counts must be positive")

    manifest_path = args.root / "manifest.csv"
    output_dir = args.root / "annotations"
    queue_path = output_dir / "queue.csv"
    labels_path = output_dir / "labels.csv"

    if queue_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"{queue_path} already exists; pass --overwrite only if no labeling "
            "work needs to be preserved."
        )
    if labels_path.exists() and labels_path.stat().st_size > 0:
        raise FileExistsError(
            f"Refusing to replace a queue while {labels_path} exists."
        )

    manifest = pd.read_csv(manifest_path)
    eye = build_eye_queue(manifest, args.eye_count, args.seed)
    mouth = build_mouth_queue(manifest, args.mouth_count, args.seed)
    queue = finalize_queue(eye, mouth, args.seed)

    output_dir.mkdir(parents=True, exist_ok=True)
    queue.to_csv(queue_path, index=False)

    print(f"Queue: {queue_path}")
    print(f"Total items: {len(queue)}")
    print("\nTask/dataset counts:")
    print(queue.groupby(["task", "dataset"]).size().to_string())
    print("\nHidden source-label audit counts:")
    print(
        queue.groupby(["task", "dataset", "source_label"])
        .size()
        .to_string()
    )
    print("\nSelection-decile counts:")
    print(
        queue.groupby(["task", "selection_decile"])
        .size()
        .to_string()
    )


if __name__ == "__main__":
    main()
