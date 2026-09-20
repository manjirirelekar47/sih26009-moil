"""
Step 3 - Train + validate + save the PROSPECTIVITY model (Member 2)
SIH26009 / MOIL - Reserve Mapping

Trains ONLY on zones with validated evidence: mineralized (1) vs barren (0).
UNKNOWN zones (no/conflicting evidence) are never treated as negative - they are
excluded from training and are only scored afterwards. The output is an
exploration-prospectivity score, NOT a reserve probability or reserve estimate.
If label_source is DEMO_SYNTHETIC the model is a software test only.

Needs (from steps 1-2): data/model_table.csv, data/feature_list.json
Run:  python step3_train_model.py

Writes:
  models/prospectivity_model.joblib     <- best model bundle (hand THIS to Member 6)
  models/prospectivity_rf.joblib        <- Random Forest bundle
  models/prospectivity_xgb.joblib       <- XGBoost bundle
  data/cv_results.csv             <- per-fold metrics (spatial vs random CV)
  data/feature_importances.csv    <- importances of the best model
  data/zone_scores.csv            <- prospectivity score for EVERY zone (input to step 4)

Member 6 usage:
    from step3_train_model import load_bundle, get_feature_importances
    bundle = load_bundle("models/prospectivity_model.joblib")
    get_feature_importances(bundle)        # DataFrame: feature, importance
"""
import json
import os
import shutil
import datetime as dt

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
from pyproj import Transformer
from scipy.spatial import cKDTree
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

# ----------------------------- CONFIG ---------------------------------------
MODEL_TABLE_CSV = "data/model_table.csv"
FEATURE_LIST_JSON = "data/feature_list.json"
MODEL_DIR = "models"

MINE_LAT, MINE_LON = 21.80, 80.19   # = study-area centre in step 1; used ONLY as the
                                    # coordinate origin for CV blocks, never as a label
METRIC_CRS = "EPSG:32644"

N_FOLDS = 4              # capped at the number of positive blocks
BLOCK_KM = 2.0           # spatial block size for CV (2 km = 2x2 zones)
TRAIN_BUFFER_KM = 1.5    # drop training zones this close to the test fold
TOP_FRAC = 0.20          # "recall in top 20% of test zones" (test sets are evidence-only)
SEED = 42

# Columns that must never be model inputs (they encode the label spatially)
FORBIDDEN = {"zone_id", "label", "label_class", "label_source", "conflict",
             "n_mineralized_obs", "n_barren_obs", "lat", "lon",
             "dist_to_mine_km", "demo_latent", "x_km", "y_km"}
# -----------------------------------------------------------------------------


# ------------------------------ MODELS ---------------------------------------
def make_pipeline(name, y_train):
    """Imputer + classifier, with class weighting for the rare positives."""
    n_pos = int((y_train == 1).sum())
    n_neg = int((y_train == 0).sum())
    if name == "rf":
        model = RandomForestClassifier(
            n_estimators=500,
            max_depth=6,
            min_samples_leaf=5,
            max_features="sqrt",
            class_weight="balanced_subsample",   # class weighting
            n_jobs=-1,
            random_state=SEED,
        )
    elif name == "xgb":
        model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=n_neg / max(n_pos, 1),   # class weighting
            eval_metric="logloss",
            tree_method="hist",
            n_jobs=-1,
            random_state=SEED,
        )
    else:
        raise ValueError(name)
    # Imputer lives INSIDE the pipeline -> fit on training rows only (no leakage)
    return Pipeline([("imputer", SimpleImputer(strategy="median")),
                     ("model", model)])


# ----------------------------- SPATIAL CV ------------------------------------
def add_metric_xy(df):
    """Zone centroid offsets from the mine, in km (mine = origin)."""
    tr = Transformer.from_crs("EPSG:4326", METRIC_CRS, always_xy=True)
    x, y = tr.transform(df["lon"].values, df["lat"].values)
    mx, my = tr.transform(MINE_LON, MINE_LAT)
    df["x_km"] = (x - mx) / 1000.0
    df["y_km"] = (y - my) / 1000.0
    return df


def assign_spatial_folds(df, n_folds, block_km, seed):
    """Group zones into square blocks; whole blocks go to one fold.

    Blocks that contain mineralized zones are spread round-robin over the
    folds first (so each test fold gets some positives); all other blocks are
    spread randomly. Neighbouring zones therefore never sit in both train and
    test.
    """
    bx = np.floor(df["x_km"] / block_km).astype(int)
    by = np.floor(df["y_km"] / block_km).astype(int)
    block = bx.astype(str) + "_" + by.astype(str)

    pos_blocks = sorted(block[df["label"] == 1].unique())
    if len(pos_blocks) < 2:
        raise ValueError("Need >=2 blocks containing positives for spatial CV; "
                         "reduce BLOCK_KM or supply more mineralized observations.")
    n_folds = min(n_folds, len(pos_blocks))

    fold_of = {b: i % n_folds for i, b in enumerate(pos_blocks)}
    others = [b for b in block.unique() if b not in fold_of]
    np.random.default_rng(seed).shuffle(others)
    fold_of.update({b: i % n_folds for i, b in enumerate(others)})
    return block.map(fold_of).values, n_folds


def fold_metrics(y, p):
    k = max(1, int(round(TOP_FRAC * len(y))))
    top = np.argsort(-p)[:k]
    return {
        "roc_auc": roc_auc_score(y, p),
        "avg_precision": average_precision_score(y, p),
        "recall_top20pct": float(y[top].sum() / y.sum()),
    }


def run_cv(df, feats, model_name, cv_type):
    X = df[feats].values
    y = df["label"].values.astype(int)
    xy = df[["x_km", "y_km"]].values
    rows = []

    if cv_type == "spatial":
        folds, n_folds = assign_spatial_folds(df, N_FOLDS, BLOCK_KM, SEED)
        splits = [(np.where(folds != k)[0], np.where(folds == k)[0])
                  for k in range(n_folds)]
    else:  # ordinary random CV, shown only to demonstrate the inflation
        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
        splits = list(skf.split(X, y))

    for k, (tr, te) in enumerate(splits):
        if cv_type == "spatial":
            # buffered CV: remove training zones adjacent to the test fold
            d, _ = cKDTree(xy[te]).query(xy[tr])
            tr = tr[d > TRAIN_BUFFER_KM]
        if y[te].sum() == 0 or y[tr].sum() == 0:
            continue
        pipe = make_pipeline(model_name, y[tr]).fit(X[tr], y[tr])
        p = pipe.predict_proba(X[te])[:, 1]
        rows.append({"model": model_name, "cv_type": cv_type, "fold": k,
                     "n_train_pos": int(y[tr].sum()),
                     "n_test_pos": int(y[te].sum()),
                     **fold_metrics(y[te], p)})
    return rows


# ------------------------- BUNDLE SAVE / LOAD --------------------------------
def build_bundle(pipe, model_name, feats, df_lab, cv_summary, label_source):
    return {
        "pipeline": pipe,                     # imputer + fitted model
        "feature_names": list(feats),         # column order the model expects
        "model_type": model_name,
        "label_source": label_source,         # DEMO_SYNTHETIC or REAL_GEOLOGICAL
        "is_demo": label_source == "DEMO_SYNTHETIC",
        "label_definition": ("1 = zone with validated mineralized observation(s); "
                             "0 = zone with validated barren observation(s); "
                             "unknown (no/conflicting evidence) excluded from "
                             "training and NOT treated as negative. Output is a "
                             "prospectivity score, not a reserve probability."),
        "n_train_positive": int((df_lab["label"] == 1).sum()),
        "n_train_negative": int((df_lab["label"] == 0).sum()),
        "spatial_cv_summary": cv_summary,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "versions": {"sklearn": sklearn.__version__, "xgboost": xgb.__version__,
                     "pandas": pd.__version__},
    }


def load_bundle(path):
    return joblib.load(path)


def get_feature_importances(bundle):
    """For Member 6's Explainability Panel."""
    m = bundle["pipeline"].named_steps["model"]
    return (pd.DataFrame({"feature": bundle["feature_names"],
                          "importance": m.feature_importances_})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True))


def predict_zone_proba(bundle, df):
    """Prospectivity score (0-1, relative; not a reserve probability) per row."""
    return bundle["pipeline"].predict_proba(df[bundle["feature_names"]].values)[:, 1]


# --------------------------------- MAIN --------------------------------------
if __name__ == "__main__":
    os.makedirs(MODEL_DIR, exist_ok=True)

    table = pd.read_csv(MODEL_TABLE_CSV)
    with open(FEATURE_LIST_JSON) as f:
        feats = json.load(f)
    leaked = FORBIDDEN & set(feats)
    assert not leaked, f"Forbidden columns used as features: {leaked}"

    table = add_metric_xy(table)
    label_source = table["label_source"].iloc[0]
    if label_source == "DEMO_SYNTHETIC":
        print("*" * 70)
        print("DEMO / SYNTHETIC LABELS AND FEATURES - software test only, this "
              "model says nothing about real manganese geology.")
        print("*" * 70)

    # Train ONLY on validated evidence. Unknown (NaN label) is never a negative.
    lab = table[table["label"].notna()].reset_index(drop=True)
    assert set(lab["label_class"]) <= {"mineralized", "barren"}, "unknown leaked into training"
    n_unknown = int((table["label_class"] == "unknown").sum())
    print(f"Label source: {label_source}")
    print(f"Training zones: {len(lab)}  "
          f"(mineralized={int((lab.label == 1).sum())}, "
          f"barren={int((lab.label == 0).sum())})  |  "
          f"unknown, excluded from training but scored: {n_unknown}")
    print(f"Random-guess average precision would be ~{(lab.label == 1).mean():.4f}\n")

    # ---- cross-validation: spatial (honest) vs random (inflated) ----
    results = []
    for m in ["rf", "xgb"]:
        for cv in ["spatial", "random"]:
            results += run_cv(lab, feats, m, cv)
    res = pd.DataFrame(results)
    res.to_csv("data/cv_results.csv", index=False)

    summary = (res.groupby(["model", "cv_type"])
                  [["roc_auc", "avg_precision", "recall_top20pct"]]
                  .agg(["mean", "std"]).round(3))
    print("Cross-validation summary (mean, std over folds):\n", summary.to_string())
    print("\nPer-fold training/test positives (spatial CV):")
    print(res[res.cv_type == "spatial"][
        ["model", "fold", "n_train_pos", "n_test_pos", "roc_auc", "avg_precision"]
    ].round(3).to_string(index=False))

    # ---- pick best model by mean spatial-CV average precision ----
    sp = res[res.cv_type == "spatial"].groupby("model")["avg_precision"].mean()
    best = sp.idxmax()
    print(f"\nBest by spatial-CV average precision: {best} ({sp[best]:.3f})")

    # ---- final fit on all labelled zones + save bundles ----
    X_all, y_all = lab[feats].values, lab["label"].values.astype(int)
    bundles = {}
    for m in ["rf", "xgb"]:
        pipe = make_pipeline(m, y_all).fit(X_all, y_all)
        cv_sum = (res[(res.model == m) & (res.cv_type == "spatial")]
                  [["roc_auc", "avg_precision", "recall_top20pct"]]
                  .mean().round(4).to_dict())
        bundles[m] = build_bundle(pipe, m, feats, lab, cv_sum, label_source)
        joblib.dump(bundles[m], f"{MODEL_DIR}/prospectivity_{m}.joblib")
    shutil.copyfile(f"{MODEL_DIR}/prospectivity_{best}.joblib",
                    f"{MODEL_DIR}/prospectivity_model.joblib")

    # ---- round-trip check: reload and compare predictions ----
    reloaded = load_bundle(f"{MODEL_DIR}/prospectivity_model.joblib")
    same = np.allclose(predict_zone_proba(reloaded, table.head(200)),
                       predict_zone_proba(bundles[best], table.head(200)))
    print(f"Reload check (predictions identical): {same}")

    imp = get_feature_importances(reloaded)
    imp.to_csv("data/feature_importances.csv", index=False)
    print("\nFeature importances (best model):\n", imp.round(3).to_string(index=False))

    # ---- score EVERY zone (incl. unknown) for the step-4 map ----
    # NOTE: zones with evidence were trained on, so THEIR scores are in-sample;
    # exploration targets are taken from unknown zones only (step 4).
    table["prospectivity_score"] = predict_zone_proba(reloaded, table)
    table[["zone_id", "lat", "lon", "label_class", "label", "label_source",
           "n_mineralized_obs", "n_barren_obs", "prospectivity_score"]].to_csv(
        "data/zone_scores.csv", index=False)
    print("\nSaved models/, data/cv_results.csv, data/feature_importances.csv, "
          "data/zone_scores.csv")
