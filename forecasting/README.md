# Production Forecasting + Shortfall Prediction (Member 3 - Samiksha)

## What this does
1. Fits Prophet on weekly production actuals -> forecast + confidence interval.
2. Shortfall risk score (0-100%) = probability actual output lands below target,
   derived straight from the width of Prophet's own confidence band.
3. Anomaly flag = any actual point that falls outside its forecast interval
   (no separate anomaly model needed).
4. Outputs a chart + a CSV that Member 5 (Srushti) plugs into the rule engine.

## Setup
    pip install -r requirements.txt

## Run
    python make_sample_data.py          # only until Manjiri's real dataset lands
    python forecast_shortfall.py --data data/weekly_production.csv --weeks 12

## Outputs
- output/forecast_chart.png    -> the deliverable chart
- output/forecast_results.csv  -> ds, actual, target, yhat, yhat_lower, yhat_upper,
                                   risk_score_pct, risk_level, is_anomaly
                                   (this is what Member 5 reads)
- output/summary.json          -> quick-glance summary for the dashboard

## Swapping in the real dataset
Just replace data/weekly_production.csv with Manjiri's file, keeping the
same 3 columns: date, actual, target. Everything else stays the same.
