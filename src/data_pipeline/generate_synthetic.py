"""
Generate SYNTHETIC weekly production + equipment-downtime data, driven by the REAL rainfall
pulled from CHIRPS (data/processed/weekly_features.csv).

How the numbers are built (say this out loud if the jury asks):
  * Planned output  = ANNUAL_TARGET_TONNES / 52.18 per week (config.py).
  * Rain reduces access/haulage: effective rain = 0.6 * this week + 0.4 * last week; loss rises
    smoothly above ~30 mm/week and saturates at 35 %.
  * Each equipment unit has baseline downtime that grows with age, extra rain-related downtime,
    and random breakdowns. Fleet downtime above a 10 % baseline cuts output.
  * Blast delays (days) are more likely in wet weeks; each lost day cuts output 2.5 %.
  * Random noise (+-4 %), then everything is rescaled so average actual/planned = TARGET_ACHIEVEMENT.

Outputs (data/processed/)
  synthetic_production_weekly.csv
  synthetic_equipment_downtime_weekly.csv

Run from repo root:
  python -m src.data_pipeline.generate_synthetic            # needs weekly_features.csv (real rainfall)
  python -m src.data_pipeline.generate_synthetic --demo     # test run with fake rainfall -> data/demo/
"""
import argparse

import numpy as np
import pandas as pd

from config import (ANNUAL_TARGET_TONNES, DATA_DEMO, DATA_PROCESSED, END_DATE, RANDOM_SEED,
                    START_DATE, TARGET_ACHIEVEMENT)

SCHEDULED_HOURS = 140  # per unit per week
FLEET = [  # (id, type, age in years)
    ("DRL-01", "drill", 6), ("DRL-02", "drill", 11),
    ("LDR-01", "loader", 4), ("LDR-02", "loader", 9), ("LDR-03", "loader", 13),
    ("DMP-01", "dumper", 3), ("DMP-02", "dumper", 8), ("DMP-03", "dumper", 12),
]
BASE_DOWNTIME_H = {"drill": 12, "loader": 10, "dumper": 9}  # per week at age 0


def demo_weeks_with_rain(rng):
    """Fake monsoon-shaped rainfall so the script can be tested without Earth Engine."""
    weeks = pd.date_range(START_DATE, END_DATE, freq="W-MON")
    doy = weeks.dayofyear.to_numpy()
    monsoon = np.exp(-((doy - 220) ** 2) / (2 * 35**2))  # peak early August
    rain = rng.gamma(shape=2.0, scale=(4 + 55 * monsoon) / 2.0)
    return pd.DataFrame({"week_start": weeks, "rainfall_mm": rain.round(2)})


def build(weekly, rng):
    rain = weekly["rainfall_mm"].to_numpy(dtype=float)
    prev = np.r_[rain[0], rain[:-1]]
    eff = 0.6 * rain + 0.4 * prev

    # --- equipment ---------------------------------------------------------------
    eq_rows = []
    for eq_id, eq_type, age in FLEET:
        base = BASE_DOWNTIME_H[eq_type] * (1 + 0.04 * age)
        routine = base * rng.gamma(shape=4, scale=0.25, size=len(weekly))       # mean 1.0
        rain_dt = 0.10 * eff * rng.uniform(0.5, 1.5, size=len(weekly))
        breakdown = rng.random(len(weekly)) < (0.02 + 0.004 * age)
        breakdown_dt = np.where(breakdown, rng.uniform(24, 72, size=len(weekly)), 0.0)
        downtime = np.clip(routine + rain_dt + breakdown_dt, 0, SCHEDULED_HOURS)
        eq_rows.append(pd.DataFrame({
            "week_start": weekly["week_start"], "equipment_id": eq_id, "equipment_type": eq_type,
            "age_years": age, "scheduled_hours": SCHEDULED_HOURS,
            "downtime_hours": downtime.round(1), "breakdown_events": breakdown.astype(int),
        }))
    equipment = pd.concat(eq_rows, ignore_index=True)
    fleet_dt_frac = (equipment.groupby("week_start")["downtime_hours"].sum().to_numpy()
                     / (len(FLEET) * SCHEDULED_HOURS))

    # --- blasting ------------------------------------------------------------------
    blast_days = np.clip(rng.poisson(0.15 + 0.012 * eff), 0, 5)

    # --- production ----------------------------------------------------------------
    planned = np.full(len(weekly), ANNUAL_TARGET_TONNES / 52.18)
    rain_loss = 0.35 * (1 - np.exp(-np.maximum(eff - 30, 0) / 80))
    dt_loss = 0.8 * np.maximum(fleet_dt_frac - 0.10, 0)
    blast_loss = 0.025 * blast_days
    raw = planned * (1 - rain_loss) * (1 - dt_loss) * (1 - blast_loss) * rng.lognormal(0, 0.04, len(weekly))
    actual = raw * (TARGET_ACHIEVEMENT * planned.sum() / raw.sum())

    shortfall_pct = (planned - actual) / planned * 100
    production = pd.DataFrame({
        "week_start": weekly["week_start"],
        "rainfall_mm": weekly["rainfall_mm"],
        "planned_tonnes": planned.round(0),
        "actual_tonnes": actual.round(0),
        "shortfall_pct": shortfall_pct.round(2),
        "shortfall_flag": (shortfall_pct > 10).astype(int),
        "fleet_downtime_pct": (fleet_dt_frac * 100).round(2),
        "blast_delay_days": blast_days.astype(int),
    })
    return production, equipment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="use fake rainfall; write to data/demo/")
    args = ap.parse_args()
    rng = np.random.default_rng(RANDOM_SEED)

    if args.demo:
        weekly, out_dir = demo_weeks_with_rain(rng), DATA_DEMO
        print("DEMO MODE: rainfall is fake. Do not commit or present these files.")
    else:
        src = DATA_PROCESSED / "weekly_features.csv"
        if not src.exists():
            raise SystemExit(f"{src} not found. Run pull_timeseries first (needs real CHIRPS rainfall).")
        weekly, out_dir = pd.read_csv(src, parse_dates=["week_start"]), DATA_PROCESSED

    out_dir.mkdir(parents=True, exist_ok=True)
    production, equipment = build(weekly[["week_start", "rainfall_mm"]].copy(), rng)
    production.to_csv(out_dir / "synthetic_production_weekly.csv", index=False)
    equipment.to_csv(out_dir / "synthetic_equipment_downtime_weekly.csv", index=False)

    # --- sanity checks to read before you commit -----------------------------------
    yearly = production.groupby(production["week_start"].dt.year).agg(
        planned=("planned_tonnes", "sum"), actual=("actual_tonnes", "sum"),
        shortfall_weeks=("shortfall_flag", "sum"))
    print("\nAnnual totals (tonnes):\n", yearly.round(0).to_string())
    print("\nCorrelation with rainfall (expect clearly negative for output):")
    print(production[["rainfall_mm", "actual_tonnes", "fleet_downtime_pct", "blast_delay_days"]]
          .corr()["rainfall_mm"].round(2).to_string())
    print(f"\nShortfall weeks (>10% below plan): {production['shortfall_flag'].mean():.0%}")
    print(f"Saved to {out_dir}")


if __name__ == "__main__":
    main()
