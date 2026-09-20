"""
make_sample_data.py
--------------------
ONLY for local testing before Member 1 (Manjiri) delivers the real synthetic
weekly production dataset correlated with rainfall.

Produces data/weekly_production.csv with columns:
    date          - week start date
    actual        - actual weekly production (tonnes)
    target        - planned/target weekly production (tonnes)

Anchored loosely to MOIL's real ~1.1 million tonnes/year scale
(~21,000 tonnes/week average) as mentioned in the project report,
just so numbers look plausible while you build against them.

DELETE / IGNORE this file once Member 1's real dataset is ready -
just point --data at their CSV instead.
"""
import numpy as np
import pandas as pd

np.random.seed(42)

n_weeks = 156  # 3 years of weekly history
start = pd.Timestamp("2023-01-02")
dates = pd.date_range(start, periods=n_weeks, freq="W-MON")

base = 21000  # ~1.1M tonnes / 52 weeks
trend = np.linspace(0, 1500, n_weeks)  # slow ramp-up
seasonal = 800 * np.sin(2 * np.pi * np.arange(n_weeks) / 52)  # yearly seasonality
noise = np.random.normal(0, 700, n_weeks)

actual = base + trend + seasonal + noise

# inject a few realistic shocks (equipment downtime / heavy rain weeks)
shock_weeks = np.random.choice(n_weeks, size=5, replace=False)
actual[shock_weeks] -= np.random.uniform(3000, 6000, size=5)

target = base + trend + 500  # planning target, slightly above trend line

df = pd.DataFrame({
    "date": dates,
    "actual": actual.round(0),
    "target": target.round(0),
})

df.to_csv("data/weekly_production.csv", index=False)
print("Wrote data/weekly_production.csv with", len(df), "rows")
print(df.head())
