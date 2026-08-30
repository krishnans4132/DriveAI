"""Dependency-light local HTTP API for the DriveAlert live demonstration."""

from __future__ import annotations

import argparse
import base64
import binascii
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Lock
import time
from typing import Any
from urllib.parse import urlparse

import cv2
import numpy as np

try:
    from .detect_fatigue import FatigueDetector
    from .model_runtime import MobileNetFatigueRuntime
    from .vision import FaceRegionExtractor
except ImportError:
    from detect_fatigue import FatigueDetector
    from model_runtime import MobileNetFatigueRuntime
    from vision import FaceRegionExtractor


MAX_REQUEST_BYTES = 3 * 1024 * 1024


class DriveAlertService:
    def __init__(self) -> None:
        self.runtime = MobileNetFatigueRuntime()
        self.vision = FaceRegionExtractor()
        self._sessions: dict[str, FatigueDetector] = {}
        self._session_timestamps: dict[str, float] = {}
        self._lock = Lock()

    def status(self) -> dict[str, object]:
        return {
            "status": "running",
            "message": "DriveAlert AI local inference is online",
            "face_extractor": self.vision.backend,
            **self.runtime.metadata,
        }

    def reset(self, session_id: str) -> dict[str, object]:
        with self._lock:
            self._sessions.pop(session_id, None)
            self._session_timestamps.pop(session_id, None)
        return {"status": "reset", "session_id": session_id}

    def _detector_and_timestamp(self, session_id: str) -> tuple[FatigueDetector, float]:
        now = time.monotonic()
        with self._lock:
            detector = self._sessions.setdefault(session_id, FatigueDetector())
            previous = self._session_timestamps.get(session_id)
            timestamp = now if previous is None else max(now, previous + 0.001)
            self._session_timestamps[session_id] = timestamp
        return detector, timestamp

    def analyze(self, payload: dict[str, Any]) -> dict[str, object]:
        session_id = str(payload.get("session_id", "default"))[:100]
        speed_kph = _bounded_number(payload.get("speed_kph", 0), 0, 240, "speed_kph")
        drive_minutes = _bounded_number(
            payload.get("continuous_drive_minutes", 0), 0, 24 * 60,
            "continuous_drive_minutes",
        )
        frame = _decode_frame(payload.get("frame"))
        started = time.perf_counter()
        regions = self.vision.extract(frame)

        prediction: dict[str, object]
        if regions.face_detected and regions.eye and regions.mouth:
            prediction = self.runtime.predict(regions.eye.image, regions.mouth.image)
        else:
            prediction = {
                "eye_closed_probability": None,
                "eye_state": "unavailable",
                "mouth_state": "unavailable",
                "mouth_probabilities": None,
                "yawn_probability": None,
            }

        detector, timestamp = self._detector_and_timestamp(session_id)
        decision = detector.analyze_observation(
            timestamp_s=timestamp,
            eye_closed_probability=prediction["eye_closed_probability"],
            yawn_probability=prediction["yawn_probability"],
            face_detected=regions.face_detected,
            current_speed_kph=speed_kph,
            continuous_drive_minutes=drive_minutes,
        )
        return {
            "session_id": session_id,
            "face_detected": regions.face_detected,
            "eye_box": regions.eye.box if regions.eye else None,
            "mouth_box": regions.mouth.box if regions.mouth else None,
            "ear": regions.ear,
            "mar": regions.mar,
            "model": prediction,
            "decision": decision,
            "telemetry": {
                "speed_kph": speed_kph,
                "continuous_drive_minutes": drive_minutes,
            },
            "inference_ms": round((time.perf_counter() - started) * 1000.0, 1),
        }


def _bounded_number(value: object, minimum: float, maximum: float, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return number


def _decode_frame(value: object) -> np.ndarray:
    if not isinstance(value, str) or not value:
        raise ValueError("frame must be a non-empty base64 data URL")
    encoded = value.split(",", 1)[1] if "," in value else value
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("frame contains invalid base64 data") from exc
    frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("frame is not a supported image")
    return frame


def make_handler(service: DriveAlertService):
    class DriveAlertHandler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:
            self._send(204, {})

        def do_GET(self) -> None:
            if urlparse(self.path).path == "/api/status":
                self._send(200, service.status())
            else:
                self._send(404, {"error": "Endpoint not found"})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_REQUEST_BYTES:
                    raise ValueError("Request body is empty or too large")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("Request body must be a JSON object")
                if path == "/api/analyze_frame":
                    result = service.analyze(payload)
                elif path == "/api/session/reset":
                    result = service.reset(str(payload.get("session_id", "default"))[:100])
                else:
                    self._send(404, {"error": "Endpoint not found"})
                    return
                self._send(200, result)
            except (ValueError, json.JSONDecodeError) as exc:
                self._send(400, {"error": str(exc)})
            except Exception as exc:
                self._send(500, {"error": f"Inference failed: {exc}"})

        def log_message(self, format: str, *args: object) -> None:
            print(f"[DriveAlert] {self.address_string()} - {format % args}")

    return DriveAlertHandler


def create_server(host: str = "127.0.0.1", port: int = 5000) -> ThreadingHTTPServer:
    service = DriveAlertService()
    return ThreadingHTTPServer((host, port), make_handler(service))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    print("Loading DriveAlert MobileNetV3-Small eye and mouth checkpoints...")
    server = create_server(args.host, args.port)
    print(f"DriveAlert API ready at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
