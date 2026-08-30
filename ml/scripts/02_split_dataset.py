import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

MAX_PER_GROUP = 200  # max crops kept per (video, region) combo -- tune if needed

df = pd.read_csv("ml/processed_data/manifest.csv")
print(f"Original rows: {len(df)}")

# --- Downsample: cap how many near-duplicate frames we keep per video ---
# (using a plain loop instead of groupby().apply() -- pandas 2.2+ silently drops
#  the grouping columns from the result of .apply(), which breaks the split step below)
sampled_chunks = []
for (gid, region), g in df.groupby(["group_id", "region"]):
    n = min(len(g), MAX_PER_GROUP)
    sampled_chunks.append(g.sample(n=n, random_state=42))
df = pd.concat(sampled_chunks, ignore_index=True)
print(f"After downsampling: {len(df)}")

# --- Split by participant/group, not by frame, to avoid leakage ---
# group_id already encodes participant identity (e.g. uta_Fold1_part1_01_0, yawdd_3-FemaleGlasses-Yawning)
# but for UTA-RLDD we want to split by PERSON, not by individual video, so strip the trailing video label:
def person_key(row):
    if row["dataset"] == "uta_rldd":
        # group_id is: uta_<FoldX>_<partY>_<participant#>_<label...>
        # e.g. uta_Fold1_part1_01_0     (label = "0", 1 token)
        #      uta_Fold1_part1_01_10_1  (label = "10_1", 2 tokens -- split drowsy file)
        # First 4 tokens always identify the person regardless of label length.
        # (Dropping only the "last" token breaks on split files -- it left a couple
        #  of participants' drowsy footage keyed as a different "person" than their
        #  own alert/low_vigilance footage, risking leakage across the split.)
        return "_".join(row["group_id"].split("_")[:4])
    else:
        # group_id is: yawdd_<person-descriptor>-<state>
        # e.g. yawdd_1-FemaleNoGlasses-Normal / -Talking / -Yawning are the SAME person.
        # Using group_id directly (no stripping) treated every clip as a different
        # person -- meaning the same person's face/lighting/camera could appear in
        # both train and test. Dropping the trailing state token fixes this for
        # essentially every YawDD participant, not just an edge case.
        return "-".join(row["group_id"].split("-")[:-1])

df["person"] = df.apply(person_key, axis=1)

gss = GroupShuffleSplit(n_splits=1, train_size=0.7, random_state=42)
train_idx, temp_idx = next(gss.split(df, groups=df["person"]))
train_df, temp_df = df.iloc[train_idx], df.iloc[temp_idx]

gss2 = GroupShuffleSplit(n_splits=1, train_size=0.5, random_state=42)
val_idx, test_idx = next(gss2.split(temp_df, groups=temp_df["person"]))
val_df, test_df = temp_df.iloc[val_idx], temp_df.iloc[test_idx]

train_df.to_csv("ml/processed_data/train.csv", index=False)
val_df.to_csv("ml/processed_data/val.csv", index=False)
test_df.to_csv("ml/processed_data/test.csv", index=False)

print(f"train={len(train_df)}  val={len(val_df)}  test={len(test_df)}")
print(f"unique people -> train={train_df['person'].nunique()}  val={val_df['person'].nunique()}  test={test_df['person'].nunique()}")
