# Mineral Prospectivity / Reserve Mapping (Member 2) - SIH26009 / MOIL

The model output is a **prospectivity score** (a relative exploration indicator),
NOT a reserve probability or an official reserve estimate. Map targets are called
**Top Exploration Targets**.

## Label logic (evidence-based - never distance from a mine)
| Class | Label | Meaning |
|---|---|---|
| mineralized (positive) | 1 | zone has validated mineralized evidence (assay / borehole / validated occurrence) |
| barren (negative)      | 0 | zone has validated barren / non-mineralized evidence |
| unknown                | NaN | no evidence or conflicting evidence. NOT negative: never trained on, still scored |

Distance from the known mine proves nothing about mineralization elsewhere, so it
is not used for any label. The mine is only a reference marker on the map.

## Two modes (kept separate)
* **DEMO / SYNTHETIC (default)** - placeholder observations + synthetic features,
  tagged `DEMO_SYNTHETIC`. For testing the software only. Not real manganese data,
  not tied to the mine, and every output is flagged DEMO (red map banner, model
  bundle `is_demo=True`).
* **REAL** - validated observations from `data/geological_labels.csv` and Member 1's
  real features in `data/features.csv`. No silent fallback to demo.

## Run (from inside this folder)
    pip install -r requirements.txt
    python run_pipeline.py                           # demo mode, steps 1-4 in one go

Real data:
    python run_pipeline.py --mode real --labels data/geological_labels.csv
                                                       # needs data/features.csv from Member 1 too

`run_pipeline.py` just runs the four steps below in order and stops immediately
on the first failure (so a bad run never continues on stale data) - useful to
have as a single command for the live demo. To run/debug one step at a time:
    python step1_build_zones.py                     # demo mode
    python step2_features.py
    python step3_train_model.py
    python step4_make_map.py                        # -> data/prospectivity_map.html

## Real label file schema (see geological_labels_template.csv)
`obs_id, lat, lon, label_class, evidence_type, source, [mn_pct], [notes]`
One row per validated point observation. `label_class` is only `mineralized` or
`barren`; do NOT list unknown areas. `source` and `evidence_type` are required.
Optional grade cut-off: set `MN_CUTOFF_PCT` in step1 (geologists decide the value).

## Features from Member 1 (real mode): `data/features.csv`
One row per `zone_id` (from data/zones.geojson) with: ndvi_mean, ndvi_std,
sar_vv_mean, sar_vh_mean, lst_mean, rain_mean.

Real-mode zones are built directly from THIS file's `zone_id`/`lat`/`lon`
(cell size auto-inferred) - not from the demo grid. If Member 1's column
names differ slightly (e.g. `lst_mean_c`, `ndvi_median`, `rain_mm_per_year`,
`sar_vv_mean_db`), `step2_features.py`'s `COLUMN_ALIASES` maps them
automatically; terrain extras (`elevation_m`, `slope_deg`) are used as bonus
features if present. A genuinely missing column (e.g. no SAR VH yet) prints a
warning and the run proceeds without it - check the console before trusting
a real-mode run.


## Hand-off to Member 6
Run `python package_handoff.py` after the pipeline - it copies exactly what
Member 6 needs (model bundle, step3_train_model.py, step4_make_map.py,
zones.geojson, zone_scores.csv, top_exploration_targets.csv, requirements.txt)
into `handoff_member6/` and `handoff_member6.zip`, plus a `HANDOFF.md` with the
two usage snippets below. (The model file and step3 script alone are not
enough - the map needs step4_make_map.py plus the two data files too.)

    from step3_train_model import load_bundle, get_feature_importances
    bundle = load_bundle("prospectivity_model.joblib")
    bundle["is_demo"]                 # True -> do NOT present as real findings
    get_feature_importances(bundle)

    from step4_make_map import build_prospectivity_map
    m, targets = build_prospectivity_map()
