import pandas as pd
import numpy as np

df = pd.read_csv("ml/processed_data/manifest.csv")
ear = df[(df.region == "eye") & (df.dataset == "uta_rldd")]["ear"]

print(f"Before filtering: {len(ear)} rows")

# Drop physiologically implausible values -- almost certainly landmark-detection
# glitches (bad angle, blur, partial occlusion), not real eye states.
ear = ear[(ear > 0.05) & (ear < 0.45)]
print(f"After filtering outliers: {len(ear)} rows")

counts, bin_edges = np.histogram(ear, bins=25)
print("\nbin_start,count")
for c, e in zip(counts, bin_edges):
    print(f"{e:.3f},{c}")

print(f"\n5th percentile: {ear.quantile(0.05):.4f}")
print(f"10th percentile: {ear.quantile(0.10):.4f}")
print(f"15th percentile: {ear.quantile(0.15):.4f}")
print(f"20th percentile: {ear.quantile(0.20):.4f}")
