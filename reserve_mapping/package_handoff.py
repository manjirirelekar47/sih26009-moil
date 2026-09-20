"""
package_handoff.py - Build the exact hand-off bundle for Member 6 (Yuga)
SIH26009 / MOIL (Member 2)

The README's usage snippets need more than the 3 files it used to list:
  bundle = load_bundle(...); get_feature_importances(bundle)   -> needs step3_train_model.py
  m, targets = build_prospectivity_map()                       -> needs step4_make_map.py
                                                                    + data/zones.geojson
                                                                    + data/zone_scores.csv
This script copies precisely those files (plus requirements.txt and a short
HANDOFF.md) into handoff_member6/, then zips it, so nothing is missing when
it's actually handed over.

Run AFTER run_pipeline.py (or steps 1-4) so the data/ and models/ files exist.

    python package_handoff.py
"""
import os
import shutil
import zipfile

OUT_DIR = "handoff_member6"
REQUIRED_FILES = [
    "models/prospectivity_model.joblib",
    "step3_train_model.py",
    "step4_make_map.py",
    "data/zones.geojson",
    "data/zone_scores.csv",
    "data/top_exploration_targets.csv",
    "requirements.txt",
]

HANDOFF_MD = """# Reserve Mapping hand-off (Member 2 -> Member 6)

## Files in this folder
- `prospectivity_model.joblib` - trained model bundle (RF or XGBoost, whichever
  won spatial cross-validation). Check `bundle["is_demo"]` before presenting
  any result - if True, these are DEMO/SYNTHETIC placeholder labels, not real
  manganese evidence.
- `step3_train_model.py` - defines `load_bundle()` and `get_feature_importances()`
  for the Explainability Panel.
- `step4_make_map.py` - defines `build_prospectivity_map()` for the map widget.
- `zones.geojson`, `zone_scores.csv`, `top_exploration_targets.csv` - data the
  map function reads; keep them in a `data/` subfolder next to your script, or
  edit `ZONES_GEOJSON` / `SCORES_CSV` at the top of `step4_make_map.py`.
- `requirements.txt` - exact package versions this was built and tested with.

## Explainability Panel
```python
from step3_train_model import load_bundle, get_feature_importances
bundle = load_bundle("prospectivity_model.joblib")
if bundle["is_demo"]:
    st.warning("Reserve Mapping is running on DEMO/SYNTHETIC data - not real evidence.")
importances = get_feature_importances(bundle)   # DataFrame: feature, importance
```

## Map widget (Streamlit)
```python
import streamlit.components.v1 as components
from step4_make_map import build_prospectivity_map
m, targets = build_prospectivity_map()
components.html(m.get_root().render(), height=650)
```

## One label to keep consistent on the dashboard
The model outputs a **prospectivity score** (relative exploration indicator),
not a reserve probability or an official reserve estimate. Please keep that
wording on any dashboard label/tooltip that shows this number.
"""


def main():
    missing = [f for f in REQUIRED_FILES if not os.path.exists(f)]
    if missing:
        raise SystemExit(
            "Cannot package hand-off - missing files (run run_pipeline.py first):\n  "
            + "\n  ".join(missing)
        )

    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    for f in REQUIRED_FILES:
        shutil.copy(f, os.path.join(OUT_DIR, os.path.basename(f)))

    with open(os.path.join(OUT_DIR, "HANDOFF.md"), "w") as fh:
        fh.write(HANDOFF_MD)

    zip_path = OUT_DIR + ".zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT_DIR):
            for fn in files:
                path = os.path.join(root, fn)
                z.write(path, os.path.relpath(path, "."))

    print(f"Hand-off bundle ready: {OUT_DIR}/  and  {zip_path}")
    print("Contents:")
    for fn in sorted(os.listdir(OUT_DIR)):
        print(f"  {fn}")


if __name__ == "__main__":
    main()
