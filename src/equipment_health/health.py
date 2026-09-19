"""
Equipment Health: a simple, explainable downtime-risk score per machine per week.

Score (0-1) = 0.4 * recent downtime + 0.2 * recent breakdowns + 0.4 * machine age
  recent downtime   average downtime share of scheduled hours over the last 8 weeks,
                    scaled so the fleet's 90th-percentile value counts as 1.0 (taken from the data)
  recent breakdowns breakdowns in the last 8 weeks, 2 or more counts as 1.0
  machine age       age_years / 15
Only data up to and including the scored week is used (no peeking at the future).
The weights and cut-offs are expert-set assumptions for the prototype. Edit them below.

Outputs   data/processed/equipment_risk.csv
Run       python -m src.equipment_health.health
Use       recommend(risk, alerts, **fleet_context("2025-08-04"))     # Member 5's engine
"""
import numpy as np
import pandas as pd

# --- Assumptions (change here) ---------------------------------------------------------
WINDOW_WEEKS = 8
WEIGHTS = {"downtime": 0.4, "breakdown": 0.2, "age": 0.4}
BREAKDOWNS_FOR_FULL_RISK = 2
AGE_FOR_FULL_RISK_YEARS = 15
BAND_CUTS = (0.60, 0.78)       # <0.60 low, <0.78 medium, else high (tuned so ~10% of machine-weeks are High)
DRIVER_LABELS = {"downtime": "recent downtime", "breakdown": "recent breakdowns", "age": "machine age"}


def band(score):
    return "low" if score < BAND_CUTS[0] else "medium" if score < BAND_CUTS[1] else "high"


def score_equipment(eq, dt_ref=None):
    """eq: synthetic_equipment_downtime_weekly.csv as a DataFrame. Returns one row per machine-week."""
    eq = eq.copy()
    eq["week_start"] = pd.to_datetime(eq["week_start"])
    eq = eq.sort_values(["equipment_id", "week_start"]).reset_index(drop=True)
    eq["_rate"] = eq["downtime_hours"] / eq["scheduled_hours"]
    g = eq.groupby("equipment_id")
    eq["downtime_pct_8w"] = g["_rate"].transform(lambda s: s.rolling(WINDOW_WEEKS, min_periods=1).mean()) * 100
    eq["breakdowns_8w"] = g["breakdown_events"].transform(lambda s: s.rolling(WINDOW_WEEKS, min_periods=1).sum())
    if dt_ref is None:
        dt_ref = float(eq["downtime_pct_8w"].quantile(0.90))
    eq["c_downtime"] = WEIGHTS["downtime"] * (eq["downtime_pct_8w"] / dt_ref).clip(0, 1)
    eq["c_breakdown"] = WEIGHTS["breakdown"] * (eq["breakdowns_8w"] / BREAKDOWNS_FOR_FULL_RISK).clip(0, 1)
    eq["c_age"] = WEIGHTS["age"] * (eq["age_years"] / AGE_FOR_FULL_RISK_YEARS).clip(0, 1)
    eq["risk_score"] = eq[["c_downtime", "c_breakdown", "c_age"]].sum(axis=1)
    eq["risk_band"] = eq["risk_score"].map(band)
    key = {"c_downtime": "downtime", "c_breakdown": "breakdown", "c_age": "age"}
    eq["main_driver"] = eq[list(key)].idxmax(axis=1).map(key).map(DRIVER_LABELS)
    cols = ["week_start", "equipment_id", "equipment_type", "age_years", "downtime_pct_8w", "breakdowns_8w",
            "c_downtime", "c_breakdown", "c_age", "risk_score", "risk_band", "main_driver"]
    out = eq[cols].sort_values(["week_start", "equipment_id"]).reset_index(drop=True)
    num = out.select_dtypes("number").columns
    out[num] = out[num].round(4)
    return out


def fleet_summary(week_scores):
    """One week's rows -> fleet band for Member 5, plus the most at-risk machine.
    high = 2+ machines High;  medium = 1 High or 4+ Medium;  otherwise low."""
    n_high = int((week_scores["risk_band"] == "high").sum())
    n_med = int((week_scores["risk_band"] == "medium").sum())
    fleet = "high" if n_high >= 2 else "medium" if (n_high == 1 or n_med >= 4) else "low"
    worst = week_scores.loc[week_scores["risk_score"].idxmax()]
    return {"downtime_risk": fleet, "worst_equipment": str(worst["equipment_id"]),
            "n_high": n_high, "n_medium": n_med}


def fleet_context(week_start, risk_csv=None, production_csv=None):
    """Inputs for prescriptive.recommend(): fleet downtime band, worst machine and blast-delay days."""
    if risk_csv is None or production_csv is None:
        from config import DATA_PROCESSED
        risk_csv = risk_csv or DATA_PROCESSED / "equipment_risk.csv"
        production_csv = production_csv or DATA_PROCESSED / "synthetic_production_weekly.csv"
    ts = pd.Timestamp(week_start)
    scores = pd.read_csv(risk_csv, parse_dates=["week_start"])
    wk = scores[scores["week_start"] == ts]
    if wk.empty:
        raise ValueError(f"week_start {week_start} not found in {risk_csv}")
    prod = pd.read_csv(production_csv, parse_dates=["week_start"])
    row = prod[prod["week_start"] == ts]
    blast = int(row["blast_delay_days"].iloc[0]) if not row.empty else 0
    s = fleet_summary(wk)
    return {"downtime_risk": s["downtime_risk"], "blast_delay_days": blast, "worst_equipment": s["worst_equipment"]}


def backtest(scores, eq):
    """Does this week's score say anything about NEXT week's downtime hours? (honest sanity check)"""
    d = scores.merge(eq[["week_start", "equipment_id", "downtime_hours"]].assign(
        week_start=lambda x: pd.to_datetime(x["week_start"])), on=["week_start", "equipment_id"])
    d = d.sort_values(["equipment_id", "week_start"])
    d["next_downtime_h"] = d.groupby("equipment_id")["downtime_hours"].shift(-1)
    d = d.dropna(subset=["next_downtime_h"])
    by_band = d.groupby("risk_band")["next_downtime_h"].mean().round(1).to_dict()
    return {"corr_with_next_week_downtime": round(float(d["risk_score"].corr(d["next_downtime_h"])), 2),
            "avg_next_week_downtime_h_by_band": by_band,
            "corr_age_alone": round(float(d["age_years"].corr(d["next_downtime_h"])), 2)}


def main():
    from config import DATA_PROCESSED
    src = DATA_PROCESSED / "synthetic_equipment_downtime_weekly.csv"
    if not src.exists():
        raise SystemExit(f"{src} not found. Run the data pipeline first.")
    eq = pd.read_csv(src)
    scores = score_equipment(eq)
    out = DATA_PROCESSED / "equipment_risk.csv"
    scores.to_csv(out, index=False)
    print(f"Saved {out.name}  ({len(scores)} rows, {scores['equipment_id'].nunique()} machines)")
    print("\nShare of machine-weeks per band:\n", scores["risk_band"].value_counts(normalize=True).round(2).to_string())
    fleet = scores.groupby("week_start").apply(lambda w: fleet_summary(w)["downtime_risk"], include_groups=False)
    print("\nShare of weeks per FLEET band:\n", fleet.value_counts(normalize=True).round(2).to_string())
    latest = scores[scores["week_start"] == scores["week_start"].max()].sort_values("risk_score", ascending=False)
    print("\nLatest week, most at-risk machines:\n",
          latest[["equipment_id", "risk_score", "risk_band", "main_driver"]].head(3).to_string(index=False))
    print("\nBacktest (weak signal is expected: the data is synthetic):", backtest(scores, eq))


if __name__ == "__main__":
    main()
