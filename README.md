# SIH 26009 — MOIL Mining Intelligence Dashboard

**See → Predict → Act**: satellite-based reserve mapping, production forecasting with shortfall risk, equipment health monitoring, weather impact prediction, and prescriptive corrective actions — all on one dashboard.

Ministry of Steel / MOIL Limited. Balaghat mine, Madhya Pradesh.

---

## What's Built

| Module | Owner | Status | Real Data |
|--------|-------|--------|-----------|
| Data Pipeline (Sentinel-2, Sentinel-1, MODIS, CHIRPS) | Member 1 (Manjiri) | ✅ Done | ✅ Google Earth Engine |
| Equipment Health (downtime risk score, 8 machines) | Member 1 (Manjiri) | ✅ Done | ✅ Real rainfall-driven |
| Reserve Mapping (RF classifier, Folium heatmap) | Member 2 (Samruddhi) | ✅ Done | ✅ Real EE features |
| Production Forecasting + Shortfall Prediction | Member 3 (Samiksha) | ✅ Done | ✅ 156 weeks real data |
| Weather Impact Predictor | Member 4 (Shreya) | ✅ Done | ✅ Real SAR + CHIRPS |
| Prescriptive Engine (17 rules, no gaps) | Member 5 (Srushti) | ✅ Done | ✅ |
| Unified Dashboard | Member 6 (Yuga) | 🔄 In progress | — |

---

## Folder Structure

```
sih26009-moil/
├── app.py                          ← Streamlit dashboard (run this)
├── config.py                       ← Shared settings (bbox, dates, paths)
├── weather_predictor.py            ← Member 4's weather alert engine
├── src/
│   ├── data_pipeline/              ← Member 1: Earth Engine pull scripts
│   │   ├── pull_timeseries.py      ← Sentinel-2, Sentinel-1, MODIS, CHIRPS
│   │   ├── generate_synthetic.py   ← Production + equipment dataset
│   │   └── pull_zone_features.py   ← Grid features for reserve mapping
│   ├── equipment_health/           ← Member 1 extra: downtime risk scorer
│   │   ├── health.py
│   │   └── test_health.py
│   ├── prescriptive/               ← Member 5: rule engine
│   │   ├── engine.py
│   │   ├── rules.csv
│   │   └── test_engine.py
│   └── reserve_mapping/            ← (placeholder — see reserve_mapping/)
├── reserve_mapping/                ← Member 2: full pipeline
│   ├── run_pipeline.py             ← One-command runner
│   ├── step1_build_zones.py
│   ├── step2_features.py
│   ├── step3_train_model.py
│   └── step4_make_map.py
├── forecasting/                    ← Member 3: Prophet forecasting
│   ├── forecast_shortfall.py
│   └── data/weekly_production.csv
├── data/
│   ├── raw/                        ← Earth Engine CSV outputs
│   └── processed/                  ← Merged weekly features + model outputs
└── docs/
    └── DATA_CONTRACT.md            ← Column names every module agrees on
```

---

## Setup

**Requirements:** Python 3.11, Windows/macOS/Linux

```powershell
git clone https://github.com/manjirirelekar47/sih26009-moil
cd sih26009-moil

# If using Python 3.11 specifically (recommended):
# Set-Alias python "C:\Users\<you>\AppData\Local\Programs\Python\Python311\python.exe"

python -m pip install earthengine-api pandas numpy geopandas folium scikit-learn ^
    xgboost prophet shap matplotlib streamlit streamlit-folium joblib shapely scipy
```

---

## Running the Full Pipeline

Run each step once in order. After that, just `streamlit run app.py`.

### Step 1 — Authenticate Earth Engine (first time only)
```powershell
earthengine authenticate
```

### Step 2 — Pull real satellite data (~5 minutes)
```powershell
python -m src.data_pipeline.pull_timeseries
```
Outputs: `data/raw/sentinel2_ndvi.csv`, `sentinel1_vv.csv`, `modis_lst.csv`, `chirps_rain.csv`, `data/processed/weekly_features.csv`

### Step 3 — Generate synthetic production data (driven by real rainfall)
```powershell
python -m src.data_pipeline.generate_synthetic
```
Outputs: `data/processed/synthetic_production_weekly.csv`, `synthetic_equipment_downtime_weekly.csv`

### Step 4 — Run Equipment Health scorer
```powershell
python -m src.equipment_health.health
```
Output: `data/processed/equipment_risk.csv`

### Step 5 — Run Production Forecasting
```powershell
cd forecasting
python forecast_shortfall.py --data data/weekly_production.csv --weeks 12
cd ..
```
Outputs: `forecasting/output/forecast_results.csv`, `forecast_chart.png`, `summary.json`

### Step 6 — Run Reserve Mapping pipeline (~15 seconds, demo mode)
```powershell
cd reserve_mapping
python run_pipeline.py --mode demo
cd ..
```
Outputs: `reserve_mapping/data/prospectivity_map.html`, `top_exploration_targets.csv`, `models/prospectivity_model.joblib`

### Step 7 — Launch the dashboard
```powershell
streamlit run app.py
```
Opens at `http://localhost:8501`

---

## Running Tests

```powershell
python -m src.equipment_health.test_health    # 6 tests
python -m src.prescriptive.test_engine        # 14 tests
python weather_predictor.py                   # 2 demo cases
```

---

## Key Config (config.py)

| Setting | Value | Change if... |
|---------|-------|--------------|
| `GEE_PROJECT` | `serious-citron-317703` | Using a different Google Cloud project |
| `BBOX` | `[80.05, 21.65, 80.35, 21.95]` | Changing the study area |
| `START_DATE` / `END_DATE` | 2023-01-01 / 2025-12-31 | Extending the time window |
| `ANNUAL_TARGET_TONNES` | 1,100,000 | Using a different mine's production scale |

---

## Data Notes

- **Satellite data** — real, pulled from Google Earth Engine for Balaghat, Madhya Pradesh
- **Production data** — synthetic, anchored to MOIL's real ~1.1M tonnes/year and driven by real CHIRPS rainfall (correlation −0.87)
- **Reserve mapping** — runs in demo mode by default (synthetic labels); switch to `--mode real` with real geological labels from GSI Bhukosh
- **Equipment data** — synthetic fleet of 8 machines (2 drills, 3 loaders, 3 dumpers), ages 3–13 years

---

## Jury Questions — Quick Answers

**"Why is production data synthetic?"**
MOIL does not publish mine-level weekly production publicly. We anchored the synthetic data to their reported annual figure (~1.1M tonnes) and drove variance from real CHIRPS rainfall. The −0.87 correlation with rainfall matches real mining patterns.

**"How accurate is the reserve model?"**
Random Forest spatial cross-validation ROC-AUC 0.905. With real geological labels from GSI Bhukosh, retrain by running `python run_pipeline.py --mode real --labels data/geological_labels.csv`.

**"How do you explain the recommendations?"**
The prescriptive engine uses 17 explicit if/then rules. Every card shows the exact inputs that triggered it. No black box.

**"Can this scale to all MOIL mines?"**
Yes — change `BBOX`, `MINE_LAT`, `MINE_LON` in `config.py` and rerun the pipeline. The architecture is mine-agnostic.

---

## Built With

Google Earth Engine · Sentinel-2 · Sentinel-1 SAR · MODIS · CHIRPS · Prophet · scikit-learn · XGBoost · GeoPandas · Folium · Streamlit · Python 3.11

*SIH 26009 — Ministry of Steel / MOIL Limited*
