import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("ml/processed_data")
SPLITS = ["train.csv", "val.csv", "test.csv"]

# --- Threshold chosen from the EAR histogram (04_ear_histogram.py) ---
# ~15th percentile of all eye-crop EAR values. Slightly above the pure-blink
# baseline (~10%) to account for extended closures in drowsy footage.
# Re-check this against a handful of crops near the boundary before trusting it.
EAR_CLOSED_THRESHOLD = 0.217

# Same mild outlier bounds used when building the histogram -- keep these in
# sync with 04_ear_histogram.py. If that script used different bounds, update
# here to match so row counts line up.
EAR_MIN, EAR_MAX = 0.05, 0.50


def add_eye_state_labels(df: pd.DataFrame) -> pd.DataFrame:
    eye_df = df[df["region"] == "eye"].copy()

    before = len(eye_df)
    eye_df = eye_df[eye_df["ear"].between(EAR_MIN, EAR_MAX)]
    dropped = before - len(eye_df)
    if dropped:
        print(f"    dropped {dropped} outlier eye rows (ear outside [{EAR_MIN}, {EAR_MAX}])")

    eye_df["eye_state"] = (eye_df["ear"] < EAR_CLOSED_THRESHOLD).map(
        {True: "closed", False: "open"}
    )
    return eye_df


for split in SPLITS:
    in_path = PROCESSED_DIR / split
    df = pd.read_csv(in_path)
    print(f"{split}: {len(df)} rows total")

    eye_labeled = add_eye_state_labels(df)

    counts = eye_labeled["eye_state"].value_counts()
    total = len(eye_labeled)
    pct_closed = counts.get("closed", 0) / total * 100 if total else 0
    print(f"  eye rows: {total}  (closed={counts.get('closed', 0)}, "
          f"open={counts.get('open', 0)}, {pct_closed:.1f}% closed)")

    out_name = split.replace(".csv", "_eye_binary.csv")
    out_path = PROCESSED_DIR / out_name
    eye_labeled.to_csv(out_path, index=False)
    print(f"  -> {out_path}")

print("\nDone. Use the *_eye_binary.csv files for the binary open/closed model.")
