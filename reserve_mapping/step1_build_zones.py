"""
Step 1 - Candidate zones + evidence-based labels for prospectivity mapping
SIH26009 / MOIL - Balaghat, MP  (Member 2)

Labels come from GEOLOGICAL EVIDENCE, never from distance to a mine
(see geo_labels.py for the exact definitions):
  mineralized (positive) : validated mineralized observation in the zone
  barren      (negative) : validated barren observation in the zone
  unknown                : no / conflicting evidence  -> NOT negative, not trained on

Two modes (kept strictly separate):
  demo  (default) : SYNTHETIC placeholder observations, tagged DEMO_SYNTHETIC.
                    Only for testing the software. NOT real manganese data.
  real            : reads validated observations from a team-supplied CSV
                    (schema in geo_labels.py). No silent fallback to demo.

Zone grid, by mode (these are NOT the same grid):
  demo : an invented 60x60 km UTM grid centred on STUDY_CENTRE_LAT/LON, built
         by build_grid() below, purely so the software has something to run on.
  real : built directly from Member 1's real feature file (REAL_FEATURES_CSV)
         by build_grid_from_points() - i.e. whatever bounding box, resolution
         and zone_id scheme Member 1 actually pulled satellite data on. This
         module does NOT force real data onto the demo grid; ideally Member 1
         extracts features on data/zones.geojson from a demo run so the two
         line up from the start, but if she instead delivers her own grid
         (as happened once already - a 30x30 lat/lon grid with "rXX_cYY" ids,
         not this module's 60x60 UTM grid with integer ids), real mode adopts
         HER grid rather than silently mismatching zone_ids.

Produces:
  data/zones.geojson, data/zones.csv   zone grid + labels (hand zones.geojson
                                       to Member 1 for feature extraction, if
                                       building features on YOUR grid instead)
  data/label_observations_used.csv     the observations behind the labels
  data/demo_latent_field.csv           (demo mode only) planted demo signal

Run:  python step1_build_zones.py                      # demo mode
      python step1_build_zones.py --mode real --labels data/geological_labels.csv \\
                                   --features data/features.csv
"""
import argparse
import os

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, box

import geo_labels as gl

# ----------------------------- CONFIG ---------------------------------------
LABEL_MODE = "demo"                          # "demo" | "real"  (or use --mode)
REAL_LABELS_CSV = "data/geological_labels.csv"
REAL_FEATURES_CSV = "data/features.csv"      # Member 1's real feature file
MN_CUTOFF_PCT = None                         # optional grade cut-off set by geologists

# Study-area centre only (Balaghat vicinity). NOT used to create any label.
# DEMO MODE ONLY - real mode's extent comes from Member 1's feature file instead.
STUDY_CENTRE_LAT, STUDY_CENTRE_LON = 21.80, 80.19
HALF_EXTENT_KM = 30                          # 60 x 60 km study area
                                             # (CHANGE to match Member 1's bounding box)
CELL_KM = 1.0                                # zone size; matches MODIS LST (1 km)
METRIC_CRS = "EPSG:32644"                    # UTM 44N - covers 80.19E, metres

# DEMO-mode settings (synthetic placeholders; ignored in real mode)
DEMO_N_MINERALIZED = 30
DEMO_N_BARREN = 150
DEMO_SEED = 7
OUT_DIR = "data"
# -----------------------------------------------------------------------------


def build_grid_from_points(features_csv, metric_crs=METRIC_CRS):
    """REAL MODE: build zone polygons around each zone Member 1 already
    extracted features for, instead of inventing a separate grid.

    Assumes her zone_id/lat/lon are on a regular grid (true for a Google Earth
    Engine export reduced to a lat/lon raster, which is how Sentinel/MODIS
    pulls normally come out). Cell size is INFERRED from the smallest gap
    between her sorted unique lat values and between her sorted unique lon
    values - it does not need to match HALF_EXTENT_KM/CELL_KM above, and
    her zone_id strings (e.g. "r00_c00") are kept as-is so nothing needs
    renaming downstream.
    """
    if not os.path.exists(features_csv):
        raise FileNotFoundError(
            f"Real mode needs Member 1's feature file at {features_csv} to build "
            f"zones from (real mode does not use the demo grid).")
    feats = pd.read_csv(features_csv)

    required = {"zone_id", "lat", "lon"}
    missing = required - set(feats.columns)
    if missing:
        raise ValueError(f"{features_csv} is missing required columns: {sorted(missing)}")
    if feats["zone_id"].duplicated().any():
        raise ValueError(f"Duplicate zone_id values in {features_csv}")
    if feats[["lat", "lon"]].isna().any().any():
        raise ValueError(f"lat/lon must be present for every row in {features_csv}")

    lats, lons = np.sort(feats["lat"].unique()), np.sort(feats["lon"].unique())
    if len(lats) < 2 or len(lons) < 2:
        raise ValueError("Need >=2 distinct lat values and >=2 distinct lon values "
                         "in the feature file to infer a cell size.")
    dlat, dlon = float(np.min(np.diff(lats))), float(np.min(np.diff(lons)))
    lat0 = float(feats["lat"].mean())
    cell_km_lat = dlat * 110.57
    cell_km_lon = dlon * 111.32 * np.cos(np.radians(lat0))

    pts = gpd.GeoDataFrame(
        feats[["zone_id"]].copy(),
        geometry=gpd.points_from_xy(feats["lon"], feats["lat"]), crs="EPSG:4326",
    ).to_crs(metric_crs)
    hx, hy = (dlon * 111.32 * np.cos(np.radians(feats["lat"].values))) * 1000 / 2, \
             (dlat * 110.57) * 1000 / 2
    xs, ys = pts.geometry.x.values, pts.geometry.y.values
    zones = gpd.GeoDataFrame(
        {"zone_id": feats["zone_id"].values},
        geometry=[box(x - hxi, y - hy, x + hxi, y + hy)
                 for x, y, hxi in zip(xs, ys, hx)],
        crs=metric_crs,
    )
    zones["lat"], zones["lon"] = feats["lat"].values, feats["lon"].values

    print(f"Built {len(zones)} REAL zones from {features_csv} "
          f"(inferred cell ~{cell_km_lon:.2f} x {cell_km_lat:.2f} km; "
          f"bbox lat [{lats.min():.3f},{lats.max():.3f}] "
          f"lon [{lons.min():.3f},{lons.max():.3f}])")
    return zones


def build_grid():
    """Square zones around the study centre. No labels are assigned here."""
    centre_m = (
        gpd.GeoSeries([Point(STUDY_CENTRE_LON, STUDY_CENTRE_LAT)], crs="EPSG:4326")
        .to_crs(METRIC_CRS).iloc[0]
    )
    half, step = HALF_EXTENT_KM * 1000, CELL_KM * 1000
    xs = np.arange(centre_m.x - half, centre_m.x + half, step)
    ys = np.arange(centre_m.y - half, centre_m.y + half, step)

    grid = gpd.GeoDataFrame(
        geometry=[box(x, y, x + step, y + step) for x in xs for y in ys],
        crs=METRIC_CRS)
    grid["zone_id"] = np.arange(len(grid))

    # centroid lat/lon (for mapping / spatial CV only - NOT model features)
    cen = grid.centroid.to_crs("EPSG:4326")
    grid["lat"], grid["lon"] = cen.y.values, cen.x.values
    return grid


def main(mode, labels_csv, features_csv):
    os.makedirs(OUT_DIR, exist_ok=True)

    if mode == "demo":
        print("=" * 70)
        print("DEMO / SYNTHETIC MODE: labels below are simulated placeholders,")
        print("NOT real manganese observations.")
        print("=" * 70)
        zones = build_grid()
        latent = gl.make_demo_latent(zones, DEMO_SEED)
        obs = gl.make_demo_observations(zones, latent, DEMO_N_MINERALIZED,
                                        DEMO_N_BARREN, CELL_KM, DEMO_SEED)
        label_source = gl.SRC_DEMO
        (zones[["zone_id"]].assign(demo_latent=latent)
         .to_csv(f"{OUT_DIR}/demo_latent_field.csv", index=False))
    elif mode == "real":
        zones = build_grid_from_points(features_csv)
        obs = gl.load_observations(labels_csv, MN_CUTOFF_PCT)
        label_source = gl.SRC_REAL
        print(f"REAL MODE: {len(obs)} validated observations from {labels_csv}")
    else:
        raise ValueError("mode must be 'demo' or 'real'")

    zones = gl.assign_zone_labels(zones, obs, label_source)

    print(f"\nLabel source : {label_source}")
    print(f"Total zones  : {len(zones)}")
    print(zones["label_class"].value_counts().to_string())
    print(f"Conflicting zones (kept UNKNOWN): {int(zones['conflict'].sum())}")

    obs.to_csv(f"{OUT_DIR}/label_observations_used.csv", index=False)
    zones.to_crs("EPSG:4326").to_file(f"{OUT_DIR}/zones.geojson", driver="GeoJSON")
    zones.drop(columns="geometry").to_csv(f"{OUT_DIR}/zones.csv", index=False)
    print(f"Saved {OUT_DIR}/zones.geojson and {OUT_DIR}/zones.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["demo", "real"], default=LABEL_MODE)
    ap.add_argument("--labels", default=REAL_LABELS_CSV,
                    help="real-mode observation CSV (see geo_labels.py schema)")
    ap.add_argument("--features", default=REAL_FEATURES_CSV,
                    help="real-mode feature CSV (Member 1's file) - real-mode "
                         "zones are built from this file's zone_id/lat/lon")
    a = ap.parse_args()
    main(a.mode, a.labels, a.features)
