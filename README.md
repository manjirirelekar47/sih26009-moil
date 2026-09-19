# SIH 26009 - AI/ML + Space Tech for MOIL Manganese Reserves & Production Shortfalls

Ministry of Steel / MOIL Limited. See -> Predict -> Act: satellite-based reserve mapping,
production forecasting with shortfall risk, and prescriptive corrective actions on one dashboard.

## Folder = owner
| Folder | Owner | Output |
|---|---|---|
| `src/data_pipeline/` | Member 1 | satellite time series, zone features, synthetic production data |
| `src/reserve_mapping/` | Member 2 | reserve-probability map + trained model |
| `src/forecasting/` | Member 3 | production forecast, shortfall risk, anomaly flags |
| `src/weather_rules/` | Member 4 | waterlogging / road / haul-friction alerts |
| `src/prescriptive/` | Member 5 | recommendation cards |
| `app/` | Member 6 | Streamlit dashboard, what-if simulator, explainability |

Shared: `config.py`, `data/`, `docs/DATA_CONTRACT.md` (column names every module agrees on).

## Setup (Windows, PowerShell)
```powershell
git clone <REPO-URL>
cd sih26009-moil
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Only Member 1 needs Google Earth Engine access. Everyone else reads the CSVs in `data/processed/`.

Run any script from the repo root as a module, e.g. `python -m src.data_pipeline.generate_synthetic`.

Read `CONTRIBUTING.md` before your first commit.
