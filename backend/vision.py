"""Live face-region extraction matching the training-data crop pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Sequence

import cv2
import mediapipe as mp
import numpy as np


RIGHT_EAR = (33, 160, 158, 133, 153, 144)
LEFT_EAR = (362, 385, 387, 263, 373, 380)
LEFT_EYE_CONTOUR = (263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466)
RIGHT_EYE_CONTOUR = (33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246)
MOUTH_CONTOUR = (61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78)
MOUTH_VERTICAL = (13, 14)
MOUTH_HORIZONTAL = (78, 308)


@dataclass(frozen=True)
class RegionCrop:
    image: np.ndarray
    box: dict[str, float]


@dataclass(frozen=True)
class FaceRegions:
    face_detected: bool
    eye: RegionCrop | None = None
    mouth: RegionCrop | None = None
    ear: float | None = None
    mar: float | None = None


def _points(landmarks, indices: Sequence[int], width: int, height: int) -> np.ndarray:
    return np.asarray(
        [(landmarks[index].x * width, landmarks[index].y * height) for index in indices],
        dtype=np.float32,
    )


def _eye_aspect_ratio(landmarks, indices: Sequence[int], width: int, height: int) -> float:
    points = _points(landmarks, indices, width, height)
    horizontal = np.linalg.norm(points[0] - points[3])
    if horizontal <= 1e-6:
        return float("nan")
    return float((np.linalg.norm(points[1] - points[5]) + np.linalg.norm(points[2] - points[4])) / (2.0 * horizontal))


def _mouth_aspect_ratio(landmarks, width: int, height: int) -> float:
    vertical = _points(landmarks, MOUTH_VERTICAL, width, height)
    horizontal = _points(landmarks, MOUTH_HORIZONTAL, width, height)
    horizontal_distance = np.linalg.norm(horizontal[0] - horizontal[1])
    if horizontal_distance <= 1e-6:
        return float("nan")
    return float(np.linalg.norm(vertical[0] - vertical[1]) / horizontal_distance)


def _crop_region(
    frame: np.ndarray,
    landmarks,
    indices: Sequence[int],
    *,
    output_width: int,
    output_height: int,
    horizontal_padding: float,
    vertical_padding: float,
    minimum_vertical_padding_from_width: float,
) -> RegionCrop | None:
    height, width = frame.shape[:2]
    points = _points(landmarks, indices, width, height)
    x_min, y_min = np.floor(points.min(axis=0)).astype(int)
    x_max, y_max = np.ceil(points.max(axis=0)).astype(int)
    box_width = max(1, x_max - x_min)
    box_height = max(1, y_max - y_min)
    pad_x = max(2, int(round(box_width * horizontal_padding)))
    pad_y = max(2, int(round(box_height * vertical_padding)), int(round(box_width * minimum_vertical_padding_from_width)))
    x_min, x_max = max(0, x_min - pad_x), min(width, x_max + pad_x)
    y_min, y_max = max(0, y_min - pad_y), min(height, y_max + pad_y)
    crop = frame[y_min:y_max, x_min:x_max]
    if crop.size == 0:
        return None

    crop_height, crop_width = crop.shape[:2]
    scale = min(output_width / crop_width, output_height / crop_height)
    resized_width = max(1, int(round(crop_width * scale)))
    resized_height = max(1, int(round(crop_height * scale)))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    resized = cv2.resize(crop, (resized_width, resized_height), interpolation=interpolation)
    fill_color = np.median(resized.reshape(-1, 3), axis=0).astype(np.uint8)
    canvas = np.empty((output_height, output_width, 3), dtype=np.uint8)
    canvas[:] = fill_color
    x_offset = (output_width - resized_width) // 2
    y_offset = (output_height - resized_height) // 2
    canvas[y_offset:y_offset + resized_height, x_offset:x_offset + resized_width] = resized
    return RegionCrop(
        image=canvas,
        box={
            "x": x_min / width,
            "y": y_min / height,
            "width": (x_max - x_min) / width,
            "height": (y_max - y_min) / height,
        },
    )


def _letterbox_box(
    frame: np.ndarray,
    x_min: int,
    y_min: int,
    x_max: int,
    y_max: int,
    output_width: int,
    output_height: int,
) -> RegionCrop | None:
    """Create a model-ready crop for the OpenCV fallback detector."""
    height, width = frame.shape[:2]
    x_min, y_min = max(0, x_min), max(0, y_min)
    x_max, y_max = min(width, x_max), min(height, y_max)
    crop = frame[y_min:y_max, x_min:x_max]
    if crop.size == 0:
        return None
    crop_height, crop_width = crop.shape[:2]
    scale = min(output_width / crop_width, output_height / crop_height)
    resized_width = max(1, int(round(crop_width * scale)))
    resized_height = max(1, int(round(crop_height * scale)))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    resized = cv2.resize(crop, (resized_width, resized_height), interpolation=interpolation)
    canvas = np.empty((output_height, output_width, 3), dtype=np.uint8)
    canvas[:] = np.median(resized.reshape(-1, 3), axis=0).astype(np.uint8)
    x_offset = (output_width - resized_width) // 2
    y_offset = (output_height - resized_height) // 2
    canvas[y_offset:y_offset + resized_height, x_offset:x_offset + resized_width] = resized
    return RegionCrop(
        image=canvas,
        box={
            "x": x_min / width,
            "y": y_min / height,
            "width": (x_max - x_min) / width,
            "height": (y_max - y_min) / height,
        },
    )


class FaceRegionExtractor:
    def __init__(self) -> None:
        self._lock = Lock()
        self._mesh = None
        self.backend = "MediaPipe Face Mesh"
        try:
            self._mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.60,
                min_tracking_confidence=0.60,
            )
        except RuntimeError:
            # Some headless macOS sessions cannot create MediaPipe's GL service.
            # The offline demo remains operational using OpenCV's bundled cascade.
            self.backend = "OpenCV face-region fallback"
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def extract(self, frame: np.ndarray) -> FaceRegions:
        if self._mesh is None:
            return self._extract_with_opencv(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        with self._lock:
            result = self._mesh.process(rgb)
        if not result.multi_face_landmarks:
            return FaceRegions(face_detected=False)

        landmarks = result.multi_face_landmarks[0].landmark
        height, width = frame.shape[:2]
        eye = _crop_region(
            frame, landmarks, LEFT_EYE_CONTOUR + RIGHT_EYE_CONTOUR,
            output_width=192, output_height=96, horizontal_padding=0.08,
            vertical_padding=0.45, minimum_vertical_padding_from_width=0.18,
        )
        mouth = _crop_region(
            frame, landmarks, MOUTH_CONTOUR,
            output_width=160, output_height=96, horizontal_padding=0.18,
            vertical_padding=0.35, minimum_vertical_padding_from_width=0.20,
        )
        if eye is None or mouth is None:
            return FaceRegions(face_detected=False)

        ear = float(np.nanmean([
            _eye_aspect_ratio(landmarks, LEFT_EAR, width, height),
            _eye_aspect_ratio(landmarks, RIGHT_EAR, width, height),
        ]))
        mar = _mouth_aspect_ratio(landmarks, width, height)
        return FaceRegions(
            face_detected=True,
            eye=eye,
            mouth=mouth,
            ear=ear if np.isfinite(ear) else None,
            mar=mar if np.isfinite(mar) else None,
        )

    def _extract_with_opencv(self, frame: np.ndarray) -> FaceRegions:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        with self._lock:
            faces = self._face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(90, 90),
            )
        if len(faces) == 0:
            return FaceRegions(face_detected=False)
        x, y, width, height = max(faces, key=lambda box: box[2] * box[3])
        eye = _letterbox_box(
            frame,
            x + int(width * 0.08),
            y + int(height * 0.12),
            x + int(width * 0.92),
            y + int(height * 0.53),
            192,
            96,
        )
        mouth = _letterbox_box(
            frame,
            x + int(width * 0.14),
            y + int(height * 0.52),
            x + int(width * 0.86),
            y + int(height * 0.91),
            160,
            96,
        )
        if eye is None or mouth is None:
            return FaceRegions(face_detected=False)
        return FaceRegions(face_detected=True, eye=eye, mouth=mouth)

    def close(self) -> None:
        if self._mesh is not None:
            self._mesh.close()
