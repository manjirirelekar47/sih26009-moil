"""
geo_labels.py - Evidence-based training labels for manganese prospectivity
SIH26009 / MOIL - Reserve Mapping (Member 2)

=====================  WHAT EACH LABEL MEANS (zone level)  =====================

POSITIVE  = "mineralized"   (label = 1)
    The zone contains >= 1 VALIDATED mineralized observation and no barren one:
    an assay-supported Mn occurrence, a mineralized borehole intercept, or a
    validated mapped occurrence.

NEGATIVE  = "barren"        (label = 0)
    The zone contains >= 1 VALIDATED barren / non-mineralized observation
    (ground that was actually tested - borehole, assayed sample, mapped
    traverse - and found not mineralized) and no mineralized one.

UNKNOWN                     (label = NaN)
    Everything else: no validated evidence, OR conflicting evidence (both a
    mineralized and a barren observation fall in the same zone).
    UNKNOWN IS NOT NEGATIVE. Unknown zones are never used for training, but they
    ARE scored - that is where "Top Exploration Targets" come from.

==========  WHY DISTANCE FROM A MINE IS NOT GROUND TRUTH  ==========
Being far from an existing mine does not show that a place is barren, and being
close does not show that it is mineralized. Only observations that tested the
ground (assays, boreholes, validated mapping) are evidence. The known mine
location is therefore NOT used to create any label in this project.

=====================  DEMO / SYNTHETIC vs REAL  ======================
REAL  : observations come from a team-supplied CSV (schema below). Label source
        = "REAL_GEOLOGICAL".
DEMO  : no real geological labels exist in this repo, so the pipeline can be
        exercised with SYNTHETIC placeholder observations. Label source =
        "DEMO_SYNTHETIC". They are NOT real manganese occurrences, are NOT
        anchored to the mine, and any model trained on them says nothing about
        real geology. Every output derived from them is flagged DEMO.

=====================  REAL-DATA CSV SCHEMA  ==========================
One row per validated point observation (one row = one borehole/assay/site):

  obs_id        unique id                                   (required)
  lat, lon      WGS84 decimal degrees                       (required)
  label_class   "mineralized" or "barren" (nothing else)    (required)
  evidence_type e.g. "assay", "borehole", "mapped occurrence" (required)
  source        who/what supplied it (report, dataset, DB)  (required)
  mn_pct        Mn assay grade in %, if available           (optional)
  notes         free text                                   (optional)

Do NOT list "unknown" areas in the file: unknown = absence of evidence.
"""
import os

import geopandas as gpd
import numpy as np
import pandas as pd

MINERALIZED, BARREN, UNKNOWN = "mineralized", "barren", "unknown"
SRC_DEMO, SRC_REAL = "DEMO_SYNTHETIC", "REAL_GEOLOGICAL"

REQUIRED_COLUMNS = ["obs_id", "lat", "lon", "label_class", "evidence_type", "source"]
OPTIONAL_COLUMNS = ["mn_pct", "notes"]
TEMPLATE_FILENAME = "geological_labels_template.csv"


def write_template(path):
    """Write an empty CSV with the expected header."""
    pd.DataFrame(columns=REQUIRED_COLUMNS + OPTIONAL_COLUMNS).to_csv(path, index=False)


# =============================================================================
# REAL-DATA INTERFACE
# =============================================================================
def load_observations(path, mn_cutoff_pct=None):
    """Read + validate a real observation file. Raises ValueError on problems.

    mn_cutoff_pct: optional team-defined grade cut-off. If given AND an
    observation has mn_pct, "mineralized" must be >= cutoff and "barren" below
    it. No default is assumed - the geologists decide the cut-off.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Real-label file not found: {path}\n"
            f"Fill in the template ({TEMPLATE_FILENAME}) with validated "
            f"observations and save it there. Demo labels are NOT used as a "
            f"fallback in real mode.")
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    if len(df) == 0:
        raise ValueError(f"{path} has no observations (header only).")
    for c in OPTIONAL_COLUMNS:
        if c not in df.columns:
            df[c] = np.nan

    df["label_class"] = df["label_class"].astype(str).str.strip().str.lower()
    bad = sorted(set(df["label_class"]) - {MINERALIZED, BARREN})
    if bad:
        raise ValueError(
            f"Invalid label_class values {bad}. Only 'mineralized' or 'barren' "
            f"are allowed; leave unvalidated areas out (unknown = no evidence).")

    if df["obs_id"].isna().any() or df["obs_id"].duplicated().any():
        raise ValueError("obs_id must be present and unique for every row.")

    for c in ["lat", "lon"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df[["lat", "lon"]].isna().any().any():
        raise ValueError("lat/lon must be numeric for every row.")
    if not df["lat"].between(-90, 90).all() or not df["lon"].between(-180, 180).all():
        raise ValueError("lat/lon out of range (expected WGS84 degrees).")

    for c in ["evidence_type", "source"]:
        if df[c].isna().any() or (df[c].astype(str).str.strip() == "").any():
            raise ValueError(f"'{c}' must be filled for every row (traceability).")
    if df["source"].astype(str).str.upper().str.contains("DEMO|SYNTHETIC").any():
        raise ValueError("Rows marked DEMO/SYNTHETIC are not allowed in a real "
                         "label file.")

    df["mn_pct"] = pd.to_numeric(df["mn_pct"], errors="coerce")
    if (df["mn_pct"].dropna() < 0).any() or (df["mn_pct"].dropna() > 100).any():
        raise ValueError("mn_pct must be between 0 and 100.")
    if mn_cutoff_pct is not None:
        g = df.dropna(subset=["mn_pct"])
        clash = g[((g.label_class == MINERALIZED) & (g.mn_pct < mn_cutoff_pct)) |
                  ((g.label_class == BARREN) & (g.mn_pct >= mn_cutoff_pct))]
        if len(clash):
            raise ValueError(
                f"{len(clash)} observation(s) contradict mn_cutoff_pct="
                f"{mn_cutoff_pct}: {clash['obs_id'].tolist()[:10]}")
    return df


def assign_zone_labels(zones_m, obs, label_source):
    """Turn point observations into zone labels (mineralized / barren / unknown).

    zones_m : GeoDataFrame of zone polygons in a metric CRS, with `zone_id`.
    obs     : validated observation DataFrame (lat, lon, label_class, obs_id).

    Zone rules: only mineralized obs -> mineralized(1); only barren obs ->
    barren(0); no obs -> unknown(NaN); BOTH kinds -> unknown (conflict, flagged;
    we do not guess). Observations outside the study grid are dropped (counted).
    """
    pts = gpd.GeoDataFrame(
        obs[["obs_id", "label_class"]].copy(),
        geometry=gpd.points_from_xy(obs["lon"], obs["lat"]), crs="EPSG:4326",
    ).to_crs(zones_m.crs)
    joined = gpd.sjoin(pts, zones_m[["zone_id", "geometry"]],
                       how="left", predicate="intersects")
    joined = joined.drop_duplicates(subset="obs_id")   # point on a shared edge
    n_outside = int(joined["zone_id"].isna().sum())
    if n_outside:
        print(f"WARNING: {n_outside} observation(s) fall outside the study area "
              f"and were ignored.")
    joined = joined.dropna(subset=["zone_id"])

    n_min = joined[joined.label_class == MINERALIZED].groupby("zone_id").size()
    n_bar = joined[joined.label_class == BARREN].groupby("zone_id").size()

    z = zones_m.copy()
    z["n_mineralized_obs"] = z["zone_id"].map(n_min).fillna(0).astype(int)
    z["n_barren_obs"] = z["zone_id"].map(n_bar).fillna(0).astype(int)
    has_min, has_bar = z["n_mineralized_obs"] > 0, z["n_barren_obs"] > 0

    z["label_class"] = UNKNOWN                       # default: NO evidence
    z.loc[has_min & ~has_bar, "label_class"] = MINERALIZED
    z.loc[has_bar & ~has_min, "label_class"] = BARREN
    z["conflict"] = has_min & has_bar                # stays UNKNOWN
    z["label"] = z["label_class"].map({MINERALIZED: 1.0, BARREN: 0.0})  # unknown->NaN
    z["label_source"] = label_source
    return z


# =============================================================================
# DEMO / SYNTHETIC GENERATOR  -  NOT REAL GEOLOGY
# =============================================================================
# Purpose: exercise the pipeline when no real labels exist. Nothing below refers
# to the mine location or to distance from it. A random smooth "demo latent
# field" is invented; placeholder observations are drawn from its high/low
# areas, and step2 derives demo satellite features from the same field so a
# model has SOMETHING synthetic to fit. That relationship is planted purely for
# software testing - it is not a manganese signature.
def smooth_random_field(lat, lon, rng, n_waves=6):
    """Spatially smooth random field in [0, 1] (sum of random sinusoids)."""
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    f = np.zeros_like(lat)
    for _ in range(n_waves):
        kx, ky = rng.uniform(2, 12, 2)
        ph = rng.uniform(0, 2 * np.pi)
        f += np.sin(kx * (lon - lon.min()) + ky * (lat - lat.min()) + ph)
    return (f - f.min()) / (f.max() - f.min())


def make_demo_latent(zones, seed):
    """DEMO ONLY: random smooth field per zone (independent of the mine)."""
    rng = np.random.default_rng(seed)
    return smooth_random_field(zones["lat"].values, zones["lon"].values, rng)


def make_demo_observations(zones, latent, n_mineralized, n_barren, cell_km, seed):
    """DEMO ONLY: synthetic placeholder observations in the real-data schema.

    'mineralized' points come from the top ~35% of the demo latent field and
    'barren' points from its lower ~75%; the two ranges deliberately overlap so
    the demo is NOT trivially separable. All rows are tagged DEMO_SYNTHETIC.
    """
    rng = np.random.default_rng(seed + 1)
    hi = np.where(latent >= np.quantile(latent, 0.65))[0]
    lo = np.where(latent <= np.quantile(latent, 0.75))[0]
    m_idx = rng.choice(hi, n_mineralized, replace=False)
    b_idx = rng.choice(lo, n_barren, replace=False)

    rows = []
    for cls, idxs, tag in [(MINERALIZED, m_idx, "M"), (BARREN, b_idx, "B")]:
        for i, zi in enumerate(idxs, 1):
            lat0, lon0 = zones["lat"].values[zi], zones["lon"].values[zi]
            jit = 0.3 * cell_km                      # stay inside the 1 km zone
            dlat = rng.uniform(-jit, jit) / 110.57
            dlon = rng.uniform(-jit, jit) / (111.32 * np.cos(np.radians(lat0)))
            rows.append({
                "obs_id": f"DEMO-{tag}-{i:03d}", "lat": lat0 + dlat,
                "lon": lon0 + dlon, "label_class": cls,
                "evidence_type": "DEMO_SYNTHETIC (no real assay)",
                "source": SRC_DEMO, "mn_pct": np.nan,
                "notes": "synthetic placeholder - not a real observation"})
    return pd.DataFrame(rows)
