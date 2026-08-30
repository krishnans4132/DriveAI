"""Create conservative weak labels and driver-disjoint splits for DriveAlert v2.

The source datasets do not provide frame-level eye-state or mouth-event labels.
This script therefore keeps only visually unambiguous candidates selected from
temporal landmark geometry and source video tags. These labels are suitable for
bootstrapping a model, but they are not independent ground truth and must not be
used to claim production accuracy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_ROOT = Path("ml/processed_data_v2")
SPLIT_ORDER = ("train", "val", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--seed", type=int, default=20260829)
    return parser.parse_args()


def assign_people(manifest: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Split people within each dataset so identities never cross splits."""
    rng = np.random.default_rng(seed)
    rows: list[dict[str, str]] = []

    people = manifest[["dataset", "person_id"]].drop_duplicates()
    for dataset, group in people.groupby("dataset", sort=True):
        person_ids = np.array(sorted(group["person_id"].tolist()), dtype=object)
        rng.shuffle(person_ids)
        count = len(person_ids)
        validation_count = int(count * 0.15 + 0.5)
        test_count = int(count * 0.15 + 0.5)
        train_count = count - validation_count - test_count

        assignments = (
            ["train"] * train_count
            + ["val"] * validation_count
            + ["test"] * test_count
        )
        rows.extend(
            {
                "dataset": dataset,
                "person_id": person_id,
                "split": split,
            }
            for person_id, split in zip(person_ids, assignments, strict=True)
        )

    return pd.DataFrame(rows).sort_values(
        ["dataset", "split", "person_id"]
    ).reset_index(drop=True)


def add_split(df: pd.DataFrame, person_splits: pd.DataFrame) -> pd.DataFrame:
    result = df.merge(
        person_splits,
        on=["dataset", "person_id"],
        how="left",
        validate="many_to_one",
    )
    if result["split"].isna().any():
        raise ValueError("At least one row has no person split assignment")
    return result


def normalize_image_paths(manifest: pd.DataFrame, root: Path) -> pd.DataFrame:
    """Convert workspace-relative manifest paths to dataset-root-relative paths."""
    result = manifest.copy()

    def normalize(value: str) -> str:
        path = Path(value)
        absolute = path.resolve() if not path.is_absolute() else path.resolve()
        try:
            return absolute.relative_to(root).as_posix()
        except ValueError as error:
            raise ValueError(
                f"Image path is outside the processed dataset root: {value}"
            ) from error

    result["filepath"] = result["filepath"].map(normalize)
    return result


def build_eye_labels(
    manifest: pd.DataFrame,
    person_splits: pd.DataFrame,
) -> pd.DataFrame:
    eye = manifest[manifest["region"] == "eye"].copy()
    eye = eye.sort_values(["video_id", "frame_idx"]).reset_index(drop=True)

    eye["ear_temporal_median"] = eye.groupby("video_id")["ear_mean"].transform(
        lambda values: values.rolling(3, center=True, min_periods=1).median()
    )
    eye["ear_open_baseline"] = eye.groupby("video_id")[
        "ear_temporal_median"
    ].transform(lambda values: values.quantile(0.80)).clip(0.22, 0.42)
    eye["ear_baseline_ratio"] = (
        eye["ear_temporal_median"] / eye["ear_open_baseline"]
    )

    quality_ok = (eye["brightness"] >= 15) & (eye["blur_score"] >= 6)
    bilateral_agreement = (eye["ear_left"] - eye["ear_right"]).abs() <= 0.08
    closed = (
        quality_ok
        & bilateral_agreement
        & (eye["ear_baseline_ratio"] <= 0.60)
        & (eye["ear_mean"] <= 0.20)
    )
    opened = (
        quality_ok
        & bilateral_agreement
        & (eye["ear_baseline_ratio"] >= 0.82)
        & (eye["ear_mean"] >= 0.21)
    )

    eye["label"] = np.select(
        [closed, opened],
        ["closed", "open"],
        default="discard",
    )
    eye = eye[eye["label"] != "discard"].copy()
    eye["label_source"] = "temporal_bilateral_ear_weak_v1"
    eye["is_ground_truth"] = False
    eye = add_split(eye, person_splits)
    return eye


def build_mouth_labels(
    manifest: pd.DataFrame,
    person_splits: pd.DataFrame,
) -> pd.DataFrame:
    mouth = manifest[
        (manifest["region"] == "mouth")
        & (manifest["dataset"] == "yawdd")
    ].copy()
    mouth = mouth.sort_values(["video_id", "frame_idx"]).reset_index(drop=True)

    mouth["mar_temporal_median"] = mouth.groupby("video_id")["mar"].transform(
        lambda values: values.rolling(3, center=True, min_periods=1).median()
    )
    mouth["mar_video_q80"] = mouth.groupby("video_id")[
        "mar_temporal_median"
    ].transform(lambda values: values.quantile(0.80))

    quality_ok = (mouth["brightness"] >= 20) & (mouth["blur_score"] >= 7)
    neutral = (
        quality_ok
        & (mouth["source_label"] == "normal")
        & (mouth["mar_temporal_median"] <= 0.08)
    )
    talking = (
        quality_ok
        & (mouth["source_label"] == "talking")
        & mouth["mar_temporal_median"].between(0.08, 0.40)
    )
    yawn_threshold = np.maximum(0.25, mouth["mar_video_q80"])
    yawning = (
        quality_ok
        & (mouth["source_label"] == "yawning")
        & (mouth["mar_temporal_median"] >= yawn_threshold)
    )

    # Talking&Yawning clips are intentionally excluded: a mouth-opening metric
    # cannot reliably decide which event is visible in an individual frame.
    mouth["label"] = np.select(
        [neutral, talking, yawning],
        ["not_yawn", "talking", "yawn"],
        default="discard",
    )
    mouth = mouth[mouth["label"] != "discard"].copy()
    mouth["label_source"] = "source_tag_plus_temporal_mar_weak_v1"
    mouth["is_ground_truth"] = False
    mouth = add_split(mouth, person_splits)
    return mouth


def output_columns(task: str) -> list[str]:
    common = [
        "filepath",
        "label",
        "label_source",
        "is_ground_truth",
        "dataset",
        "person_id",
        "video_id",
        "frame_idx",
        "timestamp_ms",
        "source_label",
        "brightness",
        "blur_score",
    ]
    if task == "eye":
        return common + [
            "ear_left",
            "ear_right",
            "ear_mean",
            "ear_temporal_median",
            "ear_open_baseline",
            "ear_baseline_ratio",
        ]
    return common + [
        "mar",
        "mar_temporal_median",
        "mar_video_q80",
    ]


def verify_outputs(
    root: Path,
    eye: pd.DataFrame,
    mouth: pd.DataFrame,
    person_splits: pd.DataFrame,
) -> None:
    for task, frame, allowed in (
        ("eye", eye, {"open", "closed"}),
        ("mouth", mouth, {"not_yawn", "talking", "yawn"}),
    ):
        if frame.empty:
            raise ValueError(f"{task} labels are empty")
        if set(frame["label"]) != allowed:
            raise ValueError(f"{task} is missing one or more expected labels")
        if frame["filepath"].duplicated().any():
            raise ValueError(f"{task} contains duplicate filepaths")
        missing = [path for path in frame["filepath"] if not (root / path).is_file()]
        if missing:
            raise FileNotFoundError(f"{task} has {len(missing)} missing images")

    for dataset, group in person_splits.groupby("dataset"):
        split_people = {
            split: set(group.loc[group["split"] == split, "person_id"])
            for split in SPLIT_ORDER
        }
        for index, left in enumerate(SPLIT_ORDER):
            for right in SPLIT_ORDER[index + 1 :]:
                overlap = split_people[left] & split_people[right]
                if overlap:
                    raise ValueError(
                        f"Participant leakage in {dataset}: {left}/{right}: {overlap}"
                    )


def write_outputs(
    root: Path,
    eye: pd.DataFrame,
    mouth: pd.DataFrame,
    person_splits: pd.DataFrame,
    seed: int,
) -> None:
    output_dir = root / "splits"
    output_dir.mkdir(parents=True, exist_ok=True)
    person_splits.to_csv(output_dir / "person_splits.csv", index=False)

    summary_rows: list[dict[str, object]] = []
    for task, frame in (("eye", eye), ("mouth", mouth)):
        columns = output_columns(task)
        for split in SPLIT_ORDER:
            partition = frame[frame["split"] == split].copy()
            partition = partition.sample(frac=1.0, random_state=seed).reset_index(drop=True)
            partition[columns].to_csv(
                output_dir / f"{task}_{split}_provisional.csv",
                index=False,
            )
            for (dataset, label), count in partition.groupby(
                ["dataset", "label"]
            ).size().items():
                summary_rows.append(
                    {
                        "task": task,
                        "split": split,
                        "dataset": dataset,
                        "label": label,
                        "rows": int(count),
                        "people": int(
                            partition.loc[
                                (partition["dataset"] == dataset)
                                & (partition["label"] == label),
                                "person_id",
                            ].nunique()
                        ),
                    }
                )

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(output_dir / "split_summary.csv", index=False)

    metadata = {
        "version": 1,
        "seed": seed,
        "warning": (
            "All generated labels are provisional weak labels, not independent "
            "ground truth. Do not use them to claim production accuracy."
        ),
        "split_policy": "70/15/15 approximately, separated by person within dataset",
        "eye_policy": {
            "temporal_window": 3,
            "video_open_baseline_quantile": 0.80,
            "closed": "EAR ratio <= 0.60, EAR <= 0.20, bilateral and quality checks",
            "open": "EAR ratio >= 0.82, EAR >= 0.21, bilateral and quality checks",
        },
        "mouth_policy": {
            "temporal_window": 3,
            "not_yawn": "YawDD normal clips with temporal MAR <= 0.08",
            "talking": "YawDD talking clips with temporal MAR in [0.08, 0.40]",
            "yawn": "YawDD yawning clips above max(0.25, per-video MAR q80)",
            "excluded": "Talking&Yawning and all ambiguous frames",
        },
        "rows": {
            "eye": int(len(eye)),
            "mouth": int(len(mouth)),
        },
    }
    (output_dir / "weak_label_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )


def print_summary(
    eye: pd.DataFrame,
    mouth: pd.DataFrame,
    person_splits: pd.DataFrame,
) -> None:
    print("Participant assignments:")
    print(pd.crosstab(person_splits["dataset"], person_splits["split"]).to_string())
    for task, frame in (("eye", eye), ("mouth", mouth)):
        print(f"\n{task.title()} provisional labels: {len(frame)}")
        print(pd.crosstab(frame["split"], frame["label"]).to_string())
        print("People per split:")
        print(frame.groupby("split")["person_id"].nunique().to_string())


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    manifest_path = root / "manifest.csv"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = normalize_image_paths(pd.read_csv(manifest_path), root)
    person_splits = assign_people(manifest, args.seed)
    eye = build_eye_labels(manifest, person_splits)
    mouth = build_mouth_labels(manifest, person_splits)
    verify_outputs(root, eye, mouth, person_splits)
    write_outputs(root, eye, mouth, person_splits, args.seed)
    print_summary(eye, mouth, person_splits)
    print(f"\nWrote verified split files to: {root / 'splits'}")


if __name__ == "__main__":
    main()
