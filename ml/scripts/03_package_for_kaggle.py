import re
import pandas as pd
import zipfile
from pathlib import Path

SPLITS = [
    "train.csv", "val.csv", "test.csv",
    "train_eye_binary.csv", "val_eye_binary.csv", "test_eye_binary.csv",
]
PROCESSED_DIR = Path("ml/processed_data")
ZIP_PATH = PROCESSED_DIR / "drivealert_processed.zip"


def sanitize_filename(name: str) -> str:
    """Replace anything that isn't a letter/digit/dot/underscore/hyphen with '_'.

    Applied to the basename only (not the 'images/' prefix), so this is safe
    to call on both the zip arcname and the CSV filepath string -- as long as
    both are derived from this same function, they stay in sync.
    """
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


# Load all three splits, rewrite filepath -> "images/<sanitized_basename>.jpg",
# and collect the actual local file to copy for each row.
rewritten = {}
files_to_add = {}  # sanitized_basename -> original local path

for split in SPLITS:
    df = pd.read_csv(PROCESSED_DIR / split)
    new_paths = []
    for fp in df["filepath"]:
        raw_basename = Path(fp).name
        safe_basename = sanitize_filename(raw_basename)

        if safe_basename in files_to_add and files_to_add[safe_basename] != fp:
            # Two different original files sanitized to the same name -- extremely
            # unlikely given unique_id/frame_idx, but fail loudly instead of
            # silently overwriting one image with another in the zip.
            raise ValueError(
                f"Filename collision after sanitizing: '{raw_basename}' and "
                f"'{Path(files_to_add[safe_basename]).name}' both map to "
                f"'{safe_basename}'"
            )

        files_to_add[safe_basename] = fp
        new_paths.append(f"images/{safe_basename}")
    df["filepath"] = new_paths
    rewritten[split] = df

total_files = len(files_to_add)
print(f"Zipping {total_files} referenced images (train+val+test, deduplicated)...")

with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for i, (safe_basename, local_path) in enumerate(files_to_add.items()):
        zf.write(local_path, arcname=f"images/{safe_basename}")
        if i % 20000 == 0 and i > 0:
            print(f"  {i}/{total_files}")

    for split, df in rewritten.items():
        zf.writestr(split, df.to_csv(index=False))

print(f"Done -> {ZIP_PATH}")
