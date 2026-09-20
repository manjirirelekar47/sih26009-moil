"""
forecast_shortfall.py
----------------------
Member 3 (Samiksha) - Production Forecasting + Shortfall Prediction

Pipeline:
  1. Load weekly production data (date, actual, target).
  2. Fit Prophet on `actual` to forecast expected output with a confidence
     interval (yhat_lower, yhat_upper).
  3. Shortfall risk score: probability that true production falls below
     `target`, estimated from the forecast's own uncertainty band
     (treated as a Gaussian centered on yhat).
  4. Anomaly flag: any *actual* historical point that falls outside its
     own forecast interval [yhat_lower, yhat_upper].
  5. Save:
       output/forecast_results.csv  -> feeds Member 5's rule engine
       output/forecast_chart.png    -> deliverable chart

Usage:
    python forecast_shortfall.py --data data/weekly_production.csv --weeks 12
"""
import argparse
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from prophet import Prophet


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    required = {"date", "actual", "target"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input data is missing columns: {missing}")
    return df


def fit_prophet(df: pd.DataFrame, interval_width: float = 0.90) -> Prophet:
    prophet_df = df.rename(columns={"date": "ds", "actual": "y"})[["ds", "y"]]
    model = Prophet(
        interval_width=interval_width,   # width of the confidence band
        weekly_seasonality=False,        # data is already weekly-aggregated
        yearly_seasonality=True,
        daily_seasonality=False,
    )
    model.fit(prophet_df)
    return model


def build_forecast(model: Prophet, df: pd.DataFrame, future_weeks: int) -> pd.DataFrame:
    future = model.make_future_dataframe(periods=future_weeks, freq="W-MON")
    forecast = model.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    # merge back actual + target for history; future rows will have NaN actual/target
    merged = forecast.merge(
        df.rename(columns={"date": "ds"}), on="ds", how="left"
    )
    return merged


def add_shortfall_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Shortfall risk score (0-100%): probability that true output < target,
    assuming forecast uncertainty is approximately Gaussian around yhat.
    Prophet's interval is a symmetric band at `interval_width` (e.g. 90%),
    so we back out an implied standard deviation from it.
    """
    # For a centered interval of width `interval_width` under a normal dist,
    # (yhat_upper - yhat_lower) = 2 * z * sigma  where z = norm.ppf(0.5 + interval_width/2)
    interval_width = 0.90  # keep in sync with fit_prophet()
    z = norm.ppf(0.5 + interval_width / 2)
    sigma = (df["yhat_upper"] - df["yhat_lower"]) / (2 * z)
    sigma = sigma.replace(0, np.nan)

    # only meaningful where a real target exists (planning targets for future
    # weeks should come from the mine's schedule, not be invented here - if
    # `target` is NaN for a future week, risk_score_pct stays NaN on purpose)
    risk = pd.Series(norm.cdf((df["target"] - df["yhat"]) / sigma) * 100, index=df.index)
    df["risk_score_pct"] = risk.round(1).where(df["target"].notna())
    df["risk_level"] = pd.cut(
        df["risk_score_pct"],
        bins=[-0.1, 20, 50, 75, 100.1],
        labels=["Low", "Moderate", "High", "Critical"],
    )
    return df


def add_anomaly_flags(df: pd.DataFrame) -> pd.DataFrame:
    df["is_anomaly"] = (
        df["actual"].notna()
        & ((df["actual"] < df["yhat_lower"]) | (df["actual"] > df["yhat_upper"]))
    )
    return df


def plot_forecast(df: pd.DataFrame, out_path: str):
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(df["ds"], df["yhat"], label="Forecast (yhat)", color="#1f77b4")
    ax.fill_between(
        df["ds"], df["yhat_lower"], df["yhat_upper"],
        alpha=0.2, color="#1f77b4", label="Confidence interval"
    )
    ax.plot(df["ds"], df["actual"], label="Actual", color="black", linewidth=1)
    ax.plot(df["ds"], df["target"], label="Target", color="green", linestyle="--")

    anomalies = df[df["is_anomaly"]]
    ax.scatter(
        anomalies["ds"], anomalies["actual"],
        color="red", zorder=5, label="Anomaly", s=40
    )

    ax.set_title("MOIL Weekly Production — Forecast vs Target with Shortfall Risk & Anomalies")
    ax.set_xlabel("Week")
    ax.set_ylabel("Production (tonnes)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/weekly_production.csv")
    parser.add_argument("--weeks", type=int, default=12, help="future weeks to forecast")
    parser.add_argument("--out-csv", default="output/forecast_results.csv")
    parser.add_argument("--out-chart", default="output/forecast_chart.png")
    args = parser.parse_args()

    df_raw = load_data(args.data)
    model = fit_prophet(df_raw)
    df = build_forecast(model, df_raw, args.weeks)
    df = add_shortfall_risk(df)
    df = add_anomaly_flags(df)

    df.to_csv(args.out_csv, index=False)
    plot_forecast(df, args.out_chart)

    # small JSON summary, handy for Member 5 / Member 6 to consume quickly
    summary = {
        "latest_week": str(df["ds"].max().date()),
        "num_anomalies_detected": int(df["is_anomaly"].sum()),
        "current_risk_level": str(df.dropna(subset=["target"]).iloc[-1]["risk_level"])
        if df["target"].notna().any() else None,
        "future_weeks_forecasted": args.weeks,
    }
    with open("output/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Done.")
    print(f"  -> {args.out_csv}")
    print(f"  -> {args.out_chart}")
    print(f"  -> output/summary.json")
    print(summary)


if __name__ == "__main__":
    main()
