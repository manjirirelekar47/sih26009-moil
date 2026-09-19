# equipment_health - downtime-risk score per machine

Reads `data/processed/synthetic_equipment_downtime_weekly.csv`, writes `data/processed/equipment_risk.csv`.

Score (0-1) = 0.4 x recent downtime + 0.2 x recent breakdowns + 0.4 x machine age
(8-week window, trailing only, no future data). Bands: <0.60 low, <0.78 medium, else high.
Weights and cut-offs are prototype assumptions; edit the constants at the top of `health.py`.

Run:   `python -m src.equipment_health.health`
Test:  `python -m src.equipment_health.test_health`
Use:   `recommend(risk, alerts, **fleet_context("2025-08-04"))`   (feeds the prescriptive engine)

Output columns: week_start, equipment_id, equipment_type, age_years, downtime_pct_8w, breakdowns_8w,
c_downtime, c_breakdown, c_age (weighted parts of the score), risk_score, risk_band, main_driver.

Notes for the jury
- Haulage cycle is not modelled separately (no telemetry). Dumper rows in this table are the haulage-capacity view.
- The data is synthetic, so the backtest is only a sanity check, not evidence of real predictive power.
