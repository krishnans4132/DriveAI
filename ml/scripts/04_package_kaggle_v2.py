"""Build and verify a space-efficient Kaggle archive for DriveAlert v2."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

import pandas as pd


DEFAULT_ROOT = Path("ml/processed_data_v2")
DEFAULT_OUTPUT = Path("ml/artifacts/drivealert_v2_provisional_kaggle.zip")
SPLIT_NAMES = (
    "eye_train_provisional.csv",
    "eye_val_provisional.csv",
    "eye_test_provisional.csv",
    "mouth_train_provisional.csv",
    "mouth_val_provisional.csv",
    "mouth_test_provisional.csv",
)
SUPPORT_NAMES = (
    "person_splits.csv",
    "split_summary.csv",
    "weak_label_metadata.json",
)


README = """# DriveAlert v2 provisional training dataset

This archive contains corrected eye and mouth crops plus driver-disjoint CSV
splits for bootstrapping DriveAlert models.

## Layout

- `images/eye/`: aspect-preserving 192x96 eye crops
- `images/mouth/`: aspect-preserving 160x96 mouth crops
- `splits/eye_*_provisional.csv`: open/closed weak labels
- `splits/mouth_*_provisional.csv`: not_yawn/talking/yawn weak labels
- `splits/person_splits.csv`: locked participant assignments
- `splits/split_summary.csv`: label and participant counts
- `splits/weak_label_metadata.json`: exact automatic-label policies

Every CSV `filepath` is relative to the archive root. Join it directly to the
Kaggle dataset directory.

## Critical evaluation warning

The frame labels are conservative provisional weak labels derived from temporal
face-landmark geometry and source video tags. They are not independent human
ground truth. The splits prevent participant leakage, but metrics calculated
against these labels must be reported as provisional. A separately verified
test set and real driving-domain validation are required before production use.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_images(root: Path) -> tuple[list[str], dict[str, int]]:
    image_paths: set[str] = set()
    split_rows: dict[str, int] = {}
    for name in SPLIT_NAMES:
        csv_path = root / "splits" / name
        if not csv_path.is_file():
            raise FileNotFoundError(f"Missing split: {csv_path}")
        frame = pd.read_csv(csv_path, usecols=["filepath"])
        split_rows[name] = len(frame)
        image_paths.update(frame["filepath"].astype(str))

    missing = [path for path in image_paths if not (root / path).is_file()]
    if missing:
        raise FileNotFoundError(f"{len(missing)} referenced images are missing")
    return sorted(image_paths), split_rows


def write_package(
    root: Path,
    output: Path,
    image_paths: list[str],
    split_rows: dict[str, int],
    overwrite: bool,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".partial")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}")
    if partial.exists():
        partial.unlink()

    source_bytes = sum((root / path).stat().st_size for path in image_paths)
    contents = {
        "package_version": 1,
        "image_count": len(image_paths),
        "source_image_bytes": source_bytes,
        "split_rows": split_rows,
        "labels_are_ground_truth": False,
    }

    with zipfile.ZipFile(partial, "w", allowZip64=True) as archive:
        for path in image_paths:
            # JPEGs are already compressed; storing them avoids wasted CPU and
            # usually produces a package as small as re-compressing them.
            archive.write(root / path, arcname=path, compress_type=zipfile.ZIP_STORED)

        for name in (*SPLIT_NAMES, *SUPPORT_NAMES):
            archive.write(
                root / "splits" / name,
                arcname=f"splits/{name}",
                compress_type=zipfile.ZIP_DEFLATED,
            )

        archive.writestr(
            "README.md",
            README,
            compress_type=zipfile.ZIP_DEFLATED,
        )
        archive.writestr(
            "PACKAGE_CONTENTS.json",
            json.dumps(contents, indent=2) + "\n",
            compress_type=zipfile.ZIP_DEFLATED,
        )

    partial.replace(output)


def verify_package(
    root: Path,
    output: Path,
    image_paths: list[str],
) -> None:
    expected = set(image_paths)
    expected.update(f"splits/{name}" for name in (*SPLIT_NAMES, *SUPPORT_NAMES))
    expected.update({"README.md", "PACKAGE_CONTENTS.json"})

    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Archive contains duplicate entry names")
        if set(names) != expected:
            raise ValueError(
                f"Archive entry mismatch: expected {len(expected)}, got {len(names)}"
            )
        broken = archive.testzip()
        if broken is not None:
            raise ValueError(f"Archive CRC check failed at: {broken}")

        archived_paths: set[str] = set()
        for name in SPLIT_NAMES:
            data = archive.read(f"splits/{name}")
            frame = pd.read_csv(io.BytesIO(data), usecols=["filepath"])
            archived_paths.update(frame["filepath"].astype(str))
        if archived_paths != set(image_paths):
            raise ValueError("Archived CSV paths do not match archived images")

    checksum = sha256_file(output)
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    checksum_path.write_text(f"{checksum}  {output.name}\n", encoding="utf-8")

    print(f"Archive: {output.resolve()}")
    print(f"Images: {len(image_paths)}")
    print(f"Entries: {len(expected)}")
    print(f"Size: {output.stat().st_size / 1024**2:.2f} MiB")
    print(f"SHA-256: {checksum}")
    print("ZIP CRC validation: passed")
    print("CSV-to-image validation: passed")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    image_paths, split_rows = collect_images(root)
    write_package(root, output, image_paths, split_rows, args.overwrite)
    verify_package(root, output, image_paths)


if __name__ == "__main__":
    main()
