# api/ — HTTP layer for the frontend

Thin FastAPI wrapper over the existing prototype modules. It reimplements no
model logic: it calls `src.prescriptive.engine`, `src.equipment_health.health`,
`weather_predictor`, and reads the CSVs already produced by the pipeline.

## Run (from the repo root — the folder with config.py and data/)

```bash
pip install -r api/requirements-api.txt
uvicorn api.main:app --reload --port 8000
```

Check it: <http://localhost:8000/api/health> and <http://localhost:8000/docs>

## Routes

| Route | Reads | Feeds frontend screen |
|---|---|---|
| `/api/health` | — | startup check |
| `/api/dashboard/kpis` | production + equipment_risk + zone_scores | Dashboard KPI row |
| `/api/alerts/active` | prescriptive + forecast_results | Active Alerts |
| `/api/dashboard/quick-actions` | static | Quick Actions |
| `/api/reserves/zones` | `reserve_mapping/data/zone_scores.csv` | Reserve Map + Reserve Mapping |
| `/api/reserves/mines` | `top_exploration_targets.csv` | Reserve Map markers |
| `/api/reserves/insights` | `zone_scores.csv` | Reserve Mapping Key Insights |
| `/api/reserves/layers/{layer}` | zone_scores + zone_features | Layer Controls |
| `/api/production/trend` | `forecasting/output/forecast_results.csv` | Production Trend chart |
| `/api/production/forecast` | `summary.json` + forecast_results | Production Forecast screen |
| `/api/shortfall/predictions` | forecast_results | Shortfall Prediction |
| `/api/environment/weather` | `data/processed/weekly_features.csv` | Weather & Environment |
| `/api/equipment/health` | `data/processed/equipment_risk.csv` | Equipment Health |
| `/api/actions/prescriptive` | `src/prescriptive/rules.csv` | Prescriptive Actions |
| `/api/reports` | filesystem listing | Reports |
| `/api/settings` | static | Settings |

## Units warning

The pipeline works in **tonnes** and **weekly** rows. The design mockup showed
`245.6 Mt`, `3.8 Mt`, `4.2 Mt` — those are **not** in your data. Real values are
`planned_tonnes ≈ 21,081` per week and a `prospectivity_score` between 0 and 1.
See `START_HERE.md` for exactly which mockup numbers had to change and why.
