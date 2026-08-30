import cv2
import mediapipe as mp
import numpy as np
import csv
from pathlib import Path

mp_face_mesh = mp.solutions.face_mesh
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_EYE  = [362, 385, 387, 263, 373, 380]
MOUTH_V   = (13, 14)
MOUTH_H   = (78, 308)

FRAME_SAMPLE_RATE = 5  # process every 5th frame

# --- Paths matched to your actual folder layout ---
RAW_ROOT = Path("ml/raw_data")
UTA_ROOT = RAW_ROOT                                   # Fold1_part1, Fold1_part2, ... live directly here
YAWDD_MIRROR_ROOT = RAW_ROOT / "YawDD dataset" / "Mirror"  # Dash is intentionally excluded for now

OUT_DIR = Path("ml/processed_data/crops")
MANIFEST_PATH = Path("ml/processed_data/manifest.csv")


def eye_aspect_ratio(landmarks, eye_idx, w, h):
    pts = np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in eye_idx])
    A = np.linalg.norm(pts[1] - pts[5])
    B = np.linalg.norm(pts[2] - pts[4])
    C = np.linalg.norm(pts[0] - pts[3])
    return (A + B) / (2.0 * C)


def mouth_aspect_ratio(landmarks, w, h):
    v = np.linalg.norm(
        np.array([landmarks[MOUTH_V[0]].x * w, landmarks[MOUTH_V[0]].y * h]) -
        np.array([landmarks[MOUTH_V[1]].x * w, landmarks[MOUTH_V[1]].y * h])
    )
    h_dist = np.linalg.norm(
        np.array([landmarks[MOUTH_H[0]].x * w, landmarks[MOUTH_H[0]].y * h]) -
        np.array([landmarks[MOUTH_H[1]].x * w, landmarks[MOUTH_H[1]].y * h])
    )
    return v / h_dist


def crop_region(frame, landmarks, idx_list, w, h, pad=15, size=64):
    xs = [landmarks[i].x * w for i in idx_list]
    ys = [landmarks[i].y * h for i in idx_list]
    x1, x2 = int(min(xs)) - pad, int(max(xs)) + pad
    y1, y2 = int(min(ys)) - pad, int(max(ys)) + pad
    x1, y1 = max(0, x1), max(0, y1)
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return None
    return cv2.resize(crop, (size, size))


def process_video(video_path, label, unique_id, dataset_name, out_dir, manifest_writer):
    """unique_id must already encode participant/fold identity — see caller."""
    cap = cv2.VideoCapture(str(video_path))
    frame_idx = 0

    with mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                                min_detection_confidence=0.5) as face_mesh:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % FRAME_SAMPLE_RATE == 0:
                h, w = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)
                if results.multi_face_landmarks:
                    lm = results.multi_face_landmarks[0].landmark
                    ear = (eye_aspect_ratio(lm, LEFT_EYE, w, h) +
                           eye_aspect_ratio(lm, RIGHT_EYE, w, h)) / 2.0
                    mar = mouth_aspect_ratio(lm, w, h)

                    eye_crop = crop_region(frame, lm, LEFT_EYE + RIGHT_EYE, w, h)
                    mouth_crop = crop_region(frame, lm, [61, 291, 13, 14], w, h, pad=25)

                    if eye_crop is not None:
                        eye_path = out_dir / f"{unique_id}_{frame_idx}_eye.jpg"
                        cv2.imwrite(str(eye_path), eye_crop)
                        manifest_writer.writerow(
                            [str(eye_path), "eye", label, ear, mar, dataset_name, unique_id])

                    if mouth_crop is not None:
                        mouth_path = out_dir / f"{unique_id}_{frame_idx}_mouth.jpg"
                        cv2.imwrite(str(mouth_path), mouth_crop)
                        manifest_writer.writerow(
                            [str(mouth_path), "mouth", label, ear, mar, dataset_name, unique_id])
            frame_idx += 1
    cap.release()


def uta_label_from_stem(stem):
    # handles "0", "5", "10", and split files "10_1" / "10_2"
    prefix = stem.split("_")[0]
    return {"0": "alert", "5": "low_vigilance", "10": "drowsy"}.get(prefix)


def yawdd_label_from_name(name):
    name = name.lower()
    for key, label in [("normal", "normal"), ("talking", "talking"), ("yawning", "yawning")]:
        if key in name:
            return label
    return None


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    counts = {}

    with open(MANIFEST_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filepath", "region", "label", "ear", "mar", "dataset", "group_id"])

        # --- UTA-RLDD: Fold*_part*/<participant>/<0|5|10>.mov ---
        for fold_dir in sorted(UTA_ROOT.glob("Fold*_part*")):
            for participant_dir in sorted(fold_dir.iterdir()):
                if not participant_dir.is_dir():
                    continue
                for video_path in sorted(participant_dir.glob("*")):
                    if video_path.suffix.lower() not in [".mov", ".mp4"]:
                        continue
                    label = uta_label_from_stem(video_path.stem)
                    if label is None:
                        print(f"SKIPPED (unrecognized filename): {video_path}")
                        continue
                    # unique_id encodes fold + participant so crops never collide across people
                    unique_id = f"uta_{fold_dir.name}_{participant_dir.name}_{video_path.stem}"
                    print(f"Processing {video_path} -> {label}")
                    process_video(video_path, label, unique_id, "uta_rldd", OUT_DIR, writer)
                    counts[label] = counts.get(label, 0) + 1

        # --- YawDD: Mirror subset only (Dash needs manual segmentation, handled later) ---
        for video_path in sorted(YAWDD_MIRROR_ROOT.rglob("*")):
            if video_path.suffix.lower() not in [".avi", ".mp4"]:
                continue
            label = yawdd_label_from_name(video_path.stem)
            if label is None:
                print(f"SKIPPED (unrecognized filename): {video_path}")
                continue
            unique_id = f"yawdd_{video_path.stem.replace(' ', '_')}"
            print(f"Processing {video_path} -> {label}")
            process_video(video_path, label, unique_id, "yawdd", OUT_DIR, writer)
            counts[label] = counts.get(label, 0) + 1

    print("\n=== Summary: videos processed per label ===")
    for label, n in counts.items():
        print(f"  {label}: {n}")
