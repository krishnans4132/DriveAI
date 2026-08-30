"""Local, blinded annotation server for DriveAlert AI crops."""

from __future__ import annotations

import argparse
import csv
import json
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "ml" / "processed_data_v2"
UI_PATH = Path(__file__).resolve().with_name("annotation_ui.html")

LABELS_BY_TASK = {
    "eye": {
        "open",
        "closed",
        "transitional",
        "uncertain",
        "unusable",
    },
    "mouth": {
        "not_yawn",
        "yawn",
        "talking",
        "uncertain",
        "unusable",
    },
}


class AnnotationStore:
    def __init__(self, data_root: Path):
        self.data_root = data_root.resolve()
        self.queue_path = self.data_root / "annotations" / "queue.csv"
        self.labels_path = self.data_root / "annotations" / "labels.csv"
        if not self.queue_path.exists():
            raise FileNotFoundError(
                f"Annotation queue not found: {self.queue_path}"
            )

        self.queue = pd.read_csv(self.queue_path).fillna("")
        if self.queue["annotation_id"].duplicated().any():
            raise ValueError("Annotation IDs must be unique")

        self.rows = {
            row["annotation_id"]: row
            for _, row in self.queue.iterrows()
        }
        self.order = {
            task: self.queue[self.queue["task"] == task][
                "annotation_id"
            ].tolist()
            for task in LABELS_BY_TASK
        }
        self.labels: dict[str, str] = {}
        self.action_stack: list[tuple[str, str | None]] = []
        self.lock = threading.Lock()
        self._load_labels()

    def _load_labels(self) -> None:
        self.labels_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.labels_path.exists():
            with self.labels_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["annotation_id", "task", "label", "annotated_at_utc"]
                )
            return

        history = pd.read_csv(self.labels_path).fillna("")
        for _, row in history.iterrows():
            annotation_id = row["annotation_id"]
            label = row["label"]
            if label == "__unlabeled__":
                self.labels.pop(annotation_id, None)
            else:
                self.labels[annotation_id] = label

    def _append_event(self, annotation_id: str, label: str) -> None:
        row = self.rows[annotation_id]
        with self.labels_path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    annotation_id,
                    row["task"],
                    label,
                    datetime.now(timezone.utc).isoformat(),
                ]
            )
            file.flush()

    def status(self) -> dict[str, object]:
        result: dict[str, object] = {}
        for task, ids in self.order.items():
            completed = sum(annotation_id in self.labels for annotation_id in ids)
            result[task] = {
                "completed": completed,
                "total": len(ids),
                "remaining": len(ids) - completed,
            }
        return result

    def next_item(self, task: str) -> dict[str, object] | None:
        if task not in LABELS_BY_TASK:
            raise ValueError(f"Unknown task: {task}")

        for annotation_id in self.order[task]:
            if annotation_id not in self.labels:
                return self.public_item(annotation_id)
        return None

    def public_item(self, annotation_id: str) -> dict[str, object]:
        row = self.rows.get(annotation_id)
        if row is None:
            raise KeyError(annotation_id)

        context_paths = json.loads(row["context_paths"])
        main_path = row["filepath"]
        try:
            current_index = context_paths.index(main_path)
        except ValueError:
            context_paths = [main_path]
            current_index = 0

        # Source label, EAR/MAR, dataset, and participant metadata are
        # deliberately omitted so annotations stay independent and blinded.
        return {
            "annotation_id": annotation_id,
            "task": row["task"],
            "context_count": len(context_paths),
            "current_index": current_index,
            "image_urls": [
                f"/api/image/{annotation_id}/{index}"
                for index in range(len(context_paths))
            ],
            "status": self.status(),
        }

    def label(self, annotation_id: str, label: str) -> dict[str, object]:
        row = self.rows.get(annotation_id)
        if row is None:
            raise KeyError(annotation_id)
        task = row["task"]
        if label not in LABELS_BY_TASK[task]:
            raise ValueError(f"Invalid {task} label: {label}")

        with self.lock:
            previous = self.labels.get(annotation_id)
            self.action_stack.append((annotation_id, previous))
            self.labels[annotation_id] = label
            self._append_event(annotation_id, label)
        return self.status()

    def undo(self) -> dict[str, object]:
        with self.lock:
            if not self.action_stack:
                return {"undone": False, "status": self.status()}
            annotation_id, previous = self.action_stack.pop()
            if previous is None:
                self.labels.pop(annotation_id, None)
                event_label = "__unlabeled__"
            else:
                self.labels[annotation_id] = previous
                event_label = previous
            self._append_event(annotation_id, event_label)
            return {
                "undone": True,
                "annotation_id": annotation_id,
                "status": self.status(),
            }

    def image_path(self, annotation_id: str, context_index: int) -> Path:
        row = self.rows.get(annotation_id)
        if row is None:
            raise KeyError(annotation_id)
        context_paths = json.loads(row["context_paths"])
        if context_index < 0 or context_index >= len(context_paths):
            raise IndexError(context_index)

        path = (PROJECT_ROOT / context_paths[context_index]).resolve()
        if self.data_root not in path.parents:
            raise ValueError("Crop path escapes the processed-data root")
        if not path.exists():
            raise FileNotFoundError(path)
        return path


def handler_class(store: AnnotationStore):
    class AnnotationHandler(BaseHTTPRequestHandler):
        server_version = "DriveAlertAnnotation/1.0"

        def log_message(self, format: str, *args) -> None:
            # Keep the terminal readable while hundreds of images are labeled.
            return

        def send_bytes(
            self,
            content: bytes,
            content_type: str,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

        def send_json(
            self,
            payload: dict[str, object],
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            self.send_bytes(
                json.dumps(payload).encode("utf-8"),
                "application/json; charset=utf-8",
                status,
            )

        def read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            try:
                return json.loads(self.rfile.read(length))
            except json.JSONDecodeError:
                return {}

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self.send_bytes(
                    UI_PATH.read_bytes(),
                    "text/html; charset=utf-8",
                )
                return

            if parsed.path == "/api/status":
                self.send_json(store.status())
                return

            if parsed.path == "/api/next":
                task = parse_qs(parsed.query).get("task", ["eye"])[0]
                try:
                    item = store.next_item(task)
                except ValueError as error:
                    self.send_json(
                        {"error": str(error)}, HTTPStatus.BAD_REQUEST
                    )
                    return
                self.send_json({"item": item, "status": store.status()})
                return

            if parsed.path == "/health":
                self.send_json({"ok": True, "status": store.status()})
                return

            if parsed.path.startswith("/api/image/"):
                parts = parsed.path.strip("/").split("/")
                if len(parts) != 4:
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                annotation_id = parts[2]
                try:
                    context_index = int(parts[3])
                    image_path = store.image_path(
                        annotation_id, context_index
                    )
                except (
                    KeyError,
                    IndexError,
                    FileNotFoundError,
                    ValueError,
                ):
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                self.send_bytes(image_path.read_bytes(), "image/jpeg")
                return

            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/label":
                payload = self.read_json()
                annotation_id = str(payload.get("annotation_id", ""))
                label = str(payload.get("label", ""))
                try:
                    status = store.label(annotation_id, label)
                except KeyError:
                    self.send_json(
                        {"error": "Unknown annotation ID"},
                        HTTPStatus.NOT_FOUND,
                    )
                    return
                except ValueError as error:
                    self.send_json(
                        {"error": str(error)}, HTTPStatus.BAD_REQUEST
                    )
                    return
                self.send_json({"saved": True, "status": status})
                return

            if parsed.path == "/api/undo":
                self.send_json(store.undo())
                return

            self.send_error(HTTPStatus.NOT_FOUND)

    return AnnotationHandler


def run_server(data_root: Path, host: str, port: int) -> None:
    store = AnnotationStore(data_root)
    server = ThreadingHTTPServer((host, port), handler_class(store))
    print(f"DriveAlert annotation tool: http://{host}:{port}")
    print(f"Queue: {store.queue_path}")
    print(f"Labels: {store.labels_path}")
    print("Press Control+C in this terminal to stop; progress is already saved.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_server(args.data_root, args.host, args.port)
