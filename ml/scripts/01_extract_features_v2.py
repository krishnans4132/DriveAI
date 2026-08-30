"""Production-oriented preprocessing for DriveAlert AI.

This extractor intentionally does not create open/closed or yawn/not-yawn
targets. UTA-RLDD and YawDD provide video/session-level labels, not reliable
frame-level ground truth. The generated manifest keeps those weak source labels
separate from an empty ``manual_label`` column that is filled during the next
annotation phase.

Key differences from the original extractor:
* honors video rotation metadata through OpenCV;
* samples a bounded number of frames directly instead of saving 1M+ crops;
* uses aspect-preserving, high-resolution crops;
* records participant identity and quality measurements;
* keeps UTA and YawDD source labels semantically distinct;
* treats YawDD Talking&Yawning as its own weak clip label;
* writes to a new output directory and refuses accidental overwrite.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import cv2
import mediapipe as mp
import numpy as np


RAW_ROOT = Path("ml/raw_data")
DEFAULT_OUTPUT_ROOT = Path("ml/processed_data_v2")

VIDEO_EXTENSIONS = {".avi", ".mov", ".mp4", ".mkv"}

# Six landmarks used only for EAR calculation.
RIGHT_EAR = [33, 160, 158, 133, 153, 144]
LEFT_EAR = [362, 385, 387, 263, 373, 380]

# Full contours provide more stable crop bounds than the six EAR landmarks.
LEFT_EYE_CONTOUR = [
    263, 249, 390, 373, 374, 380, 381, 382, 362,
    398, 384, 385, 386, 387, 388, 466,
]
RIGHT_EYE_CONTOUR = [
    33, 7, 163, 144, 145, 153, 154, 155, 133,
    173, 157, 158, 159, 160, 161, 246,
]
MOUTH_CONTOUR = [
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291,
    308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78,
]

MOUTH_VERTICAL = (13, 14)
MOUTH_HORIZONTAL = (78, 308)

MANIFEST_FIELDS = [
    "filepath",
    "region",
    "crop_width",
    "crop_height",
    "dataset",
    "person_id",
    "video_id",
    "source_path",
    "frame_idx",
    "timestamp_ms",
    "source_label",
    "manual_label",
    "ear_left",
    "ear_right",
    "ear_mean",
    "mar",
    "brightness",
    "blur_score",
    "rotation_metadata",
]

SUMMARY_FIELDS = [
    "dataset",
    "person_id",
    "video_id",
    "source_path",
    "source_label",
    "rotation_metadata",
    "frame_count",
    "fps",
    "sample_stride",
    "frames_attempted",
    "faces_detected",
    "eye_crops_written",
    "mouth_crops_written",
    "status",
]


@dataclass(frozen=True)
class VideoRecord:
    path: Path
    dataset: str
    person_id: str
    video_id: str
    source_label: str


def sanitize_token(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("_")


def uta_label_from_stem(stem: str) -> str | None:
    prefix = stem.split("_")[0]
    return {
        "0": "alert",
        "5": "low_vigilance",
        "10": "drowsy",
    }.get(prefix)


def yawdd_source_label(stem: str) -> str | None:
    lower = stem.lower()
    has_talking = "talking" in lower
    has_yawning = "yawning" in lower

    if has_talking and has_yawning:
        return "talking_yawning"
    if has_yawning:
        return "yawning"
    if has_talking:
        return "talking"
    if "normal" in lower:
        return "normal"
    return None


def yawdd_person_id(stem: str) -> str:
    """Group the same YawDD person across state and glasses conditions."""
    match = re.match(r"^(\d+)-(male|female)", stem, flags=re.IGNORECASE)
    if match:
        return f"yawdd_{match.group(1)}_{match.group(2).lower()}"

    # Loudly recognizable fallback for unexpected archive naming.
    state_free = re.sub(
        r"-(talking&yawning|talking|yawning|normal)$",
        "",
        stem,
        flags=re.IGNORECASE,
    )
    return f"yawdd_unknown_{sanitize_token(state_free).lower()}"


def discover_videos(raw_root: Path) -> list[VideoRecord]:
    records: list[VideoRecord] = []

    for fold_dir in sorted(raw_root.glob("Fold*_part*")):
        for participant_dir in sorted(fold_dir.iterdir()):
            if not participant_dir.is_dir():
                continue

            for video_path in sorted(participant_dir.iterdir()):
                if video_path.suffix.lower() not in VIDEO_EXTENSIONS:
                    continue

                source_label = uta_label_from_stem(video_path.stem)
                if source_label is None:
                    continue

                person_id = f"uta_{participant_dir.name}"
                video_id = sanitize_token(
                    f"uta_{fold_dir.name}_{participant_dir.name}_{video_path.stem}"
                )
                records.append(
                    VideoRecord(
                        path=video_path,
                        dataset="uta_rldd",
                        person_id=person_id,
                        video_id=video_id,
                        source_label=source_label,
                    )
                )

    yawdd_root = raw_root / "YawDD dataset" / "Mirror"
    for video_path in sorted(yawdd_root.rglob("*")):
        if video_path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue

        source_label = yawdd_source_label(video_path.stem)
        if source_label is None:
            continue

        records.append(
            VideoRecord(
                path=video_path,
                dataset="yawdd",
                person_id=yawdd_person_id(video_path.stem),
                video_id=sanitize_token(f"yawdd_{video_path.stem}"),
                source_label=source_label,
            )
        )

    return records


def record_for_explicit_path(path: Path, raw_root: Path) -> VideoRecord:
    resolved = path.resolve()
    yawdd_root = (raw_root / "YawDD dataset" / "Mirror").resolve()

    if yawdd_root in resolved.parents:
        label = yawdd_source_label(path.stem)
        if label is None:
            raise ValueError(f"Cannot determine YawDD label from {path.name}")
        return VideoRecord(
            path=path,
            dataset="yawdd",
            person_id=yawdd_person_id(path.stem),
            video_id=sanitize_token(f"yawdd_{path.stem}"),
            source_label=label,
        )

    label = uta_label_from_stem(path.stem)
    if label is None:
        raise ValueError(f"Cannot determine UTA-RLDD label from {path.name}")

    try:
        fold_name = path.parents[1].name
        participant = path.parent.name
    except IndexError as exc:
        raise ValueError(f"Unexpected UTA-RLDD path: {path}") from exc

    return VideoRecord(
        path=path,
        dataset="uta_rldd",
        person_id=f"uta_{participant}",
        video_id=sanitize_token(
            f"uta_{fold_name}_{participant}_{path.stem}"
        ),
        source_label=label,
    )


def normalized_points(landmarks, indices: Sequence[int], width: int, height: int):
    return np.array(
        [
            (landmarks[index].x * width, landmarks[index].y * height)
            for index in indices
        ],
        dtype=np.float32,
    )


def eye_aspect_ratio(landmarks, indices: Sequence[int], width: int, height: int):
    points = normalized_points(landmarks, indices, width, height)
    horizontal = np.linalg.norm(points[0] - points[3])
    if horizontal <= 1e-6:
        return float("nan")

    vertical_1 = np.linalg.norm(points[1] - points[5])
    vertical_2 = np.linalg.norm(points[2] - points[4])
    return float((vertical_1 + vertical_2) / (2.0 * horizontal))


def mouth_aspect_ratio(landmarks, width: int, height: int):
    vertical = normalized_points(
        landmarks, MOUTH_VERTICAL, width, height
    )
    horizontal = normalized_points(
        landmarks, MOUTH_HORIZONTAL, width, height
    )

    horizontal_distance = np.linalg.norm(horizontal[0] - horizontal[1])
    if horizontal_distance <= 1e-6:
        return float("nan")

    vertical_distance = np.linalg.norm(vertical[0] - vertical[1])
    return float(vertical_distance / horizontal_distance)


def aspect_preserving_crop(
    frame: np.ndarray,
    landmarks,
    indices: Sequence[int],
    output_width: int,
    output_height: int,
    horizontal_padding: float,
    vertical_padding: float,
    minimum_vertical_padding_from_width: float,
) -> tuple[np.ndarray, np.ndarray] | None:
    height, width = frame.shape[:2]
    points = normalized_points(landmarks, indices, width, height)

    x_min, y_min = np.floor(points.min(axis=0)).astype(int)
    x_max, y_max = np.ceil(points.max(axis=0)).astype(int)

    box_width = max(1, x_max - x_min)
    box_height = max(1, y_max - y_min)

    pad_x = max(2, int(round(box_width * horizontal_padding)))
    # Eye contours are shallow; use width as a floor for vertical context.
    pad_y = max(
        2,
        int(round(box_height * vertical_padding)),
        int(round(box_width * minimum_vertical_padding_from_width)),
    )

    x_min = max(0, x_min - pad_x)
    x_max = min(width, x_max + pad_x)
    y_min = max(0, y_min - pad_y)
    y_max = min(height, y_max + pad_y)

    crop = frame[y_min:y_max, x_min:x_max]
    if crop.size == 0:
        return None

    crop_height, crop_width = crop.shape[:2]
    scale = min(
        output_width / crop_width,
        output_height / crop_height,
    )
    resized_width = max(1, int(round(crop_width * scale)))
    resized_height = max(1, int(round(crop_height * scale)))
    interpolation = (
        cv2.INTER_AREA
        if scale < 1.0
        else cv2.INTER_CUBIC
    )
    resized = cv2.resize(
        crop,
        (resized_width, resized_height),
        interpolation=interpolation,
    )

    # A flat, crop-derived background avoids the artificial streaks produced by
    # BORDER_REPLICATE while remaining less conspicuous than pure black bars.
    fill_color = np.median(
        resized.reshape(-1, 3), axis=0
    ).astype(np.uint8)
    canvas = np.empty(
        (output_height, output_width, 3), dtype=np.uint8
    )
    canvas[:] = fill_color

    x_offset = (output_width - resized_width) // 2
    y_offset = (output_height - resized_height) // 2
    canvas[
        y_offset:y_offset + resized_height,
        x_offset:x_offset + resized_width,
    ] = resized

    # Return the unpadded content too, so blur/brightness quality measurements
    # are not diluted by the letterbox area.
    return canvas, crop


def quality_metrics(crop: np.ndarray) -> tuple[float, float]:
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return brightness, blur_score


def sampled_frame_indices(
    frame_count: int,
    max_samples_per_video: int,
    minimum_stride: int,
) -> np.ndarray:
    if frame_count <= 0:
        return np.array([], dtype=np.int64)

    eligible_count = max(1, int(math.ceil(frame_count / minimum_stride)))
    sample_count = min(max_samples_per_video, eligible_count)
    if sample_count == 1:
        return np.array([0], dtype=np.int64)

    evenly_spaced = np.linspace(
        0,
        frame_count - 1,
        num=sample_count,
    )
    aligned = (
        np.rint(evenly_spaced / minimum_stride).astype(np.int64)
        * minimum_stride
    )
    aligned = np.clip(aligned, 0, frame_count - 1)
    return np.unique(aligned)


def relative_source_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def process_video(
    record: VideoRecord,
    face_mesh,
    output_root: Path,
    manifest_writer: csv.DictWriter,
    max_samples_per_video: int,
    minimum_stride: int,
    eye_width: int,
    eye_height: int,
    mouth_width: int,
    mouth_height: int,
) -> dict[str, object]:
    capture = cv2.VideoCapture(str(record.path))
    if not capture.isOpened():
        return {
            "dataset": record.dataset,
            "person_id": record.person_id,
            "video_id": record.video_id,
            "source_path": relative_source_path(record.path),
            "source_label": record.source_label,
            "rotation_metadata": 0.0,
            "frame_count": 0,
            "fps": 0.0,
            "sample_stride": 0,
            "frames_attempted": 0,
            "faces_detected": 0,
            "eye_crops_written": 0,
            "mouth_crops_written": 0,
            "status": "open_failed",
        }

    rotation_metadata = 0.0
    if hasattr(cv2, "CAP_PROP_ORIENTATION_META"):
        rotation_metadata = float(
            capture.get(cv2.CAP_PROP_ORIENTATION_META)
        )
    if hasattr(cv2, "CAP_PROP_ORIENTATION_AUTO"):
        capture.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    target_frames = sampled_frame_indices(
        frame_count,
        max_samples_per_video,
        minimum_stride,
    )
    if len(target_frames) > 1:
        stride = int(round(float(np.median(np.diff(target_frames)))))
    elif len(target_frames) == 1:
        stride = frame_count
    else:
        stride = 0

    source_path = relative_source_path(record.path)
    frames_attempted = 0
    faces_detected = 0
    eye_crops_written = 0
    mouth_crops_written = 0
    eye_dir = output_root / "images" / "eye"
    mouth_dir = output_root / "images" / "mouth"

    for frame_idx in target_frames:
        # Direct seeking avoids decoding every unused frame between samples.
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
        success, frame = capture.read()
        if not success:
            continue

        frames_attempted += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            continue

        faces_detected += 1
        landmarks = results.multi_face_landmarks[0].landmark
        height, width = frame.shape[:2]

        ear_left = eye_aspect_ratio(
            landmarks, LEFT_EAR, width, height
        )
        ear_right = eye_aspect_ratio(
            landmarks, RIGHT_EAR, width, height
        )
        ear_mean = float(np.nanmean([ear_left, ear_right]))
        mar = mouth_aspect_ratio(landmarks, width, height)

        timestamp_ms = (
            frame_idx / fps * 1000.0
            if fps > 0
            else float(capture.get(cv2.CAP_PROP_POS_MSEC))
        )

        regions = [
            (
                "eye",
                LEFT_EYE_CONTOUR + RIGHT_EYE_CONTOUR,
                eye_dir,
                eye_width,
                eye_height,
                0.08,
                0.45,
                0.18,
            ),
            (
                "mouth",
                MOUTH_CONTOUR,
                mouth_dir,
                mouth_width,
                mouth_height,
                0.18,
                0.35,
                0.20,
            ),
        ]

        for (
            region,
            indices,
            region_dir,
            output_width,
            output_height,
            pad_x,
            pad_y,
            vertical_width_padding,
        ) in regions:
            crop_result = aspect_preserving_crop(
                frame,
                landmarks,
                indices,
                output_width=output_width,
                output_height=output_height,
                horizontal_padding=pad_x,
                vertical_padding=pad_y,
                minimum_vertical_padding_from_width=vertical_width_padding,
            )
            if crop_result is None:
                continue
            crop, crop_content = crop_result

            filename = (
                f"{record.video_id}_{frame_idx:07d}_{region}.jpg"
            )
            output_path = region_dir / filename
            written = cv2.imwrite(
                str(output_path),
                crop,
                [cv2.IMWRITE_JPEG_QUALITY, 95],
            )
            if not written:
                continue

            brightness, blur_score = quality_metrics(crop_content)
            manifest_writer.writerow(
                {
                    "filepath": output_path.as_posix(),
                    "region": region,
                    "crop_width": output_width,
                    "crop_height": output_height,
                    "dataset": record.dataset,
                    "person_id": record.person_id,
                    "video_id": record.video_id,
                    "source_path": source_path,
                    "frame_idx": frame_idx,
                    "timestamp_ms": f"{timestamp_ms:.3f}",
                    "source_label": record.source_label,
                    "manual_label": "",
                    "ear_left": f"{ear_left:.8f}",
                    "ear_right": f"{ear_right:.8f}",
                    "ear_mean": f"{ear_mean:.8f}",
                    "mar": f"{mar:.8f}",
                    "brightness": f"{brightness:.3f}",
                    "blur_score": f"{blur_score:.3f}",
                    "rotation_metadata": f"{rotation_metadata:.1f}",
                }
            )

            if region == "eye":
                eye_crops_written += 1
            else:
                mouth_crops_written += 1

    capture.release()

    return {
        "dataset": record.dataset,
        "person_id": record.person_id,
        "video_id": record.video_id,
        "source_path": source_path,
        "source_label": record.source_label,
        "rotation_metadata": f"{rotation_metadata:.1f}",
        "frame_count": frame_count,
        "fps": f"{fps:.3f}",
        "sample_stride": stride,
        "frames_attempted": frames_attempted,
        "faces_detected": faces_detected,
        "eye_crops_written": eye_crops_written,
        "mouth_crops_written": mouth_crops_written,
        "status": "ok",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=RAW_ROOT)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument(
        "--max-samples-per-video",
        type=int,
        default=200,
    )
    parser.add_argument("--minimum-stride", type=int, default=5)
    parser.add_argument("--eye-width", type=int, default=192)
    parser.add_argument("--eye-height", type=int, default=96)
    parser.add_argument("--mouth-width", type=int, default=160)
    parser.add_argument("--mouth-height", type=int, default=96)
    parser.add_argument(
        "--video",
        type=Path,
        action="append",
        help="Process only this video; repeat for a pilot set.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow an existing manifest in the output directory.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.max_samples_per_video <= 0:
        raise ValueError("--max-samples-per-video must be positive")
    if args.minimum_stride <= 0:
        raise ValueError("--minimum-stride must be positive")
    if args.eye_width < 96 or args.eye_height < 64:
        raise ValueError("Eye crop dimensions are too small")
    if args.mouth_width < 96 or args.mouth_height < 64:
        raise ValueError("Mouth crop dimensions are too small")


def main() -> None:
    args = parse_args()
    validate_args(args)

    manifest_path = args.output_root / "manifest.csv"
    summary_path = args.output_root / "video_summary.csv"

    if manifest_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"{manifest_path} already exists. Choose a new output directory "
            "or pass --overwrite explicitly."
        )

    (args.output_root / "images" / "eye").mkdir(
        parents=True, exist_ok=True
    )
    (args.output_root / "images" / "mouth").mkdir(
        parents=True, exist_ok=True
    )

    if args.video:
        records = [
            record_for_explicit_path(path, args.raw_root)
            for path in args.video
        ]
    else:
        records = discover_videos(args.raw_root)

    if not records:
        raise RuntimeError("No recognized videos were found")

    print(f"Videos selected: {len(records)}")
    print(f"Output root: {args.output_root}")

    face_mesh_module = mp.solutions.face_mesh
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file, \
            summary_path.open("w", newline="", encoding="utf-8") as summary_file, \
            face_mesh_module.FaceMesh(
                # Samples are far apart in time, so each one must be detected
                # independently instead of using landmark tracking state.
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.60,
                min_tracking_confidence=0.60,
            ) as face_mesh:
        manifest_writer = csv.DictWriter(
            manifest_file, fieldnames=MANIFEST_FIELDS
        )
        summary_writer = csv.DictWriter(
            summary_file, fieldnames=SUMMARY_FIELDS
        )
        manifest_writer.writeheader()
        summary_writer.writeheader()

        for index, record in enumerate(records, start=1):
            print(
                f"[{index}/{len(records)}] {record.path} "
                f"-> {record.source_label}"
            )
            summary = process_video(
                record=record,
                face_mesh=face_mesh,
                output_root=args.output_root,
                manifest_writer=manifest_writer,
                max_samples_per_video=args.max_samples_per_video,
                minimum_stride=args.minimum_stride,
                eye_width=args.eye_width,
                eye_height=args.eye_height,
                mouth_width=args.mouth_width,
                mouth_height=args.mouth_height,
            )
            summary_writer.writerow(summary)
            manifest_file.flush()
            summary_file.flush()

    print(f"Manifest: {manifest_path}")
    print(f"Video summary: {summary_path}")


if __name__ == "__main__":
    main()
