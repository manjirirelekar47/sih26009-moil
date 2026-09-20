"""
Step 2 - Feature table: demo generator + loader/validator/cleaner (Member 2)
SIH26009 / MOIL - Prospectivity mapping

Needs data/zones.csv from step1_build_zones.py. The label mode recorded there
(label_source column) decides where features come from:

  DEMO_SYNTHETIC  -> make_demo_features() writes data/demo_features.csv.
                     SYNTHETIC ONLY - randomized smooth fields plus a planted
                     relationship to a random "demo latent field" so the
                     software has something to fit. It does NOT depend on the
                     mine location or on distance to it, and it is NOT a real
                     manganese signature.
  REAL_GEOLOGICAL -> data/features.csv from Member 1 (real satellite features)
                     must exist; nothing is generated.

Run:  python step2_features.py
  -> data/model_table.csv   (zones + cleaned features + labels)
  -> data/feature_list.json (feature names, reused in steps 3-4)
"""
import json
import os
import sys

import numpy as np
import pandas as pd

from geo_labels import SRC_DEMO, smooth_random_field

ZONES_CSV = "data/zones.csv"
DEMO_LATENT_CSV = "data/demo_latent_field.csv"     # written by step 1 (demo only)
DEMO_FEATURES_CSV = "data/demo_features.csv"       # generated here (demo only)
REAL_FEATURES_CSV = "data/features.csv"            # Member 1's file (real mode)
MODEL_TABLE_CSV = "data/model_table.csv"
FEATURE_LIST_JSON = "data/feature_list.json"
DEMO_SIGNAL_STRENGTH = 0.6   # 0 = features are pure noise; higher = easier demo

# Column contract to agree with Member 1 (one row per zone_id)
FEATURE_COLS = [
    "ndvi_mean",     # Sentinel-2 vegetation index (mean over zone)
    "ndvi_std",      # Sentinel-2 NDVI variability inside the zone
    "sar_vv_mean",   # Sentinel-1 VV backscatter, dB (moisture proxy)
    "sar_vh_mean",   # Sentinel-1 VH backscatter, dB
    "lst_mean",      # MODIS land surface temperature, deg C
    "rain_mean",     # CHIRPS mean rainfall (mm) - coarse 5 km
]

# Extra terrain features Member 1 may also deliver (DEM-derived). Not part of
# the original contract above, but genuinely useful for prospectivity
# (structural/geomorphological control on mineralization), so they're used
# automatically if present and simply skipped if not.
OPTIONAL_FEATURE_COLS = [
    "elevation_m",
    "slope_deg",
]

# Real-world column names seen from Member 1 that mean the same thing as a
# FEATURE_COLS/OPTIONAL_FEATURE_COLS name, just spelled differently. Add to
# this dict rather than renaming her file by hand each time she re-exports.
# NOTE: ndvi_median -> ndvi_mean is a real statistic swap (median, not mean) -
# close enough to use, but flagged loudly below so it's a documented decision,
# not a silent one.
COLUMN_ALIASES = {
    "lst_mean_c": "lst_mean",
    "ndvi_median": "ndvi_mean",
    "rain_mm_per_year": "rain_mean",
    "sar_vv_mean_db": "sar_vv_mean",
    "sar_vh_mean_db": "sar_vh_mean",
}
SEMANTIC_SWAPS = {"ndvi_median": "ndvi_mean"}   # aliases that aren't just a rename

MAX_MISSING_FRAC = 0.30   # drop a feature if more than 30% of zones lack it
CORR_DROP_THRESHOLD = 0.95  # drop one of a pair that is this correlated


# ----------------------------------------------------------------------------
# 1. DEMO / SYNTHETIC DATA  (fake! only for testing the pipeline)
# ----------------------------------------------------------------------------
def make_demo_features(zones_csv=ZONES_CSV, latent_csv=DEMO_LATENT_CSV,
                       seed=42, nan_frac=0.03):
    """Build a SYNTHETIC Member-1-style feature table.

    Every feature is a random smooth spatial field plus noise. Four of them
    (NDVI mean/std, SAR VV, LST) also carry a planted dependence on the random
    "demo latent field" from step 1, so demo labels are learnable. The latent
    field is unrelated to the mine position: there is NO distance-to-mine term
    anywhere. This is a software test fixture, not geology.
    """
    rng = np.random.default_rng(seed)
    z = pd.read_csv(zones_csv)
    lat, lon = z["lat"].values, z["lon"].values
    latent = (pd.read_csv(latent_csv).set_index("zone_id")
              .loc[z["zone_id"], "demo_latent"].values)
    sig = DEMO_SIGNAL_STRENGTH * (latent - 0.5)      # in [-0.5, 0.5] * strength

    n = len(z)
    f = lambda: smooth_random_field(lat, lon, rng) - 0.5   # independent smooth field
    df = pd.DataFrame({"zone_id": z["zone_id"]})
    df["ndvi_mean"] = 0.45 + 0.30 * f() - 0.30 * sig + rng.normal(0, 0.04, n)
    df["ndvi_std"] = 0.07 + 0.05 * f() + 0.04 * sig + rng.normal(0, 0.012, n)
    df["sar_vv_mean"] = -10 + 4 * f() + 3.0 * sig + rng.normal(0, 0.8, n)
    df["sar_vh_mean"] = df["sar_vv_mean"] - 6 + rng.normal(0, 0.5, n)
    df["lst_mean"] = 32 + 5 * f() + 3.0 * sig + rng.normal(0, 0.6, n)
    df["rain_mean"] = 950 + 150 * f()                # smooth/coarse, no planted signal

    # punch a few holes to test the cleaning code (cloud gaps etc.)
    for col in ["ndvi_mean", "ndvi_std", "sar_vv_mean", "lst_mean"]:
        df.loc[rng.random(n) < nan_frac, col] = np.nan
    return df.round(4)


# ----------------------------------------------------------------------------
# 2. LOAD + VALIDATE + CLEAN  (works on demo or real data)
# ----------------------------------------------------------------------------
def load_and_merge(zones_csv=ZONES_CSV, features_csv=REAL_FEATURES_CSV):
    zones = pd.read_csv(zones_csv)
    feats = pd.read_csv(features_csv)

    # Apply known aliases (Member 1's export naming vs. the contract names)
    renamed = {c: COLUMN_ALIASES[c] for c in feats.columns if c in COLUMN_ALIASES}
    if renamed:
        feats = feats.rename(columns=renamed)
        print(f"Renamed columns from {features_csv} to match the feature "
              f"contract: {renamed}")
        for src, dst in renamed.items():
            if src in SEMANTIC_SWAPS:
                print(f"  NOTE: '{src}' -> '{dst}' is not just a rename - it's a "
                      f"different statistic (e.g. median vs mean). Using it as-is "
                      f"for now; flag to Member 1 if an exact match is needed.")

    if feats["zone_id"].duplicated().any():
        raise ValueError("Duplicate zone_id rows in feature file")

    all_wanted = FEATURE_COLS + OPTIONAL_FEATURE_COLS
    present = [c for c in all_wanted if c in feats.columns]
    missing_core = [c for c in FEATURE_COLS if c not in feats.columns]
    missing_optional = [c for c in OPTIONAL_FEATURE_COLS if c not in feats.columns]
    if missing_core:
        print(f"WARNING: {features_csv} is missing core contract columns "
              f"{missing_core} - proceeding without them rather than failing, "
              f"but the model will be weaker until Member 1 delivers them.")
    if missing_optional:
        print(f"(Optional terrain columns not present, skipping: {missing_optional})")
    if not present:
        raise ValueError(f"{features_csv} has none of the expected feature "
                         f"columns {all_wanted} (after alias mapping).")

    df = zones.merge(feats[["zone_id"] + present], on="zone_id", how="left")
    no_feats = df[present].isna().all(axis=1).sum()
    if no_feats:
        print(f"WARNING: {no_feats} zones have no features at all "
              f"(check zone_id alignment with Member 1)")
    return df, present


def clean_features(df, feats):
    """Drop unusable / redundant features. Returns (df, kept_feature_list).

    NOTE: NaNs are NOT filled here. Imputation goes inside the model pipeline
    in step 3 so it is fit on training folds only (no leakage). No scaling
    either - Random Forest / XGBoost don't need it.
    """
    feats = list(feats)

    # a) too many missing values
    miss = df[feats].isna().mean()
    print("\nMissing fraction per feature:\n", miss.round(3).to_string())
    too_missing = miss[miss > MAX_MISSING_FRAC].index.tolist()
    feats = [f for f in feats if f not in too_missing]

    # b) constant columns (no information)
    constant = [f for f in feats if df[f].nunique(dropna=True) <= 1]
    feats = [f for f in feats if f not in constant]

    # c) near-duplicate features (keep the first of each highly correlated pair)
    corr = df[feats].corr().abs()
    dropped_corr = []
    for i, a in enumerate(feats):
        for b in feats[i + 1:]:
            if a in dropped_corr or b in dropped_corr:
                continue
            if corr.loc[a, b] > CORR_DROP_THRESHOLD:
                dropped_corr.append(b)
    feats = [f for f in feats if f not in dropped_corr]

    print(f"\nDropped (missing>{MAX_MISSING_FRAC:.0%}): {too_missing}")
    print(f"Dropped (constant): {constant}")
    print(f"Dropped (corr>{CORR_DROP_THRESHOLD}): {dropped_corr}")
    print(f"Kept features: {feats}")
    return df, feats


def quick_sanity_report(df, feats):
    """Do mineralized zones differ from barren zones? (rough signal check)
    Unknown zones are excluded - they are neither class."""
    lab = df[df["label_class"].isin(["mineralized", "barren"])]
    summary = lab.groupby("label_class")[feats].mean().T
    summary["gap_in_std_units"] = (
        (summary["mineralized"] - summary["barren"]) / lab[feats].std()
    ).round(2)
    print("\nMean feature value: mineralized vs barren zones\n",
          summary.round(3).to_string())


if __name__ == "__main__":
    label_source = pd.read_csv(ZONES_CSV)["label_source"].iloc[0]

    if label_source == SRC_DEMO:
        print("DEMO / SYNTHETIC MODE: generating synthetic features (not real data).")
        make_demo_features().to_csv(DEMO_FEATURES_CSV, index=False)
        features_csv = DEMO_FEATURES_CSV
    else:
        features_csv = REAL_FEATURES_CSV
        if not os.path.exists(features_csv):
            sys.exit(f"Real label mode needs Member 1's feature file at "
                     f"{features_csv} (columns: zone_id + {FEATURE_COLS}).")

    df, feats = load_and_merge(ZONES_CSV, features_csv)
    df, feats = clean_features(df, feats)
    quick_sanity_report(df, feats)

    df.to_csv(MODEL_TABLE_CSV, index=False)
    with open(FEATURE_LIST_JSON, "w") as f:
        json.dump(feats, f)
    print(f"\nSaved {MODEL_TABLE_CSV} and {FEATURE_LIST_JSON}")
    print(f"Train-ready rows (mineralized+barren only): {df['label'].notna().sum()}  "
          f"| unknown (not trained on, still scored): {df['label'].isna().sum()}")
