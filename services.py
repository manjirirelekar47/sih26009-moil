"""services.py: data loading and the weather adapter for the dashboard.

Everything here is the logic that used to sit inside app.py, moved unchanged
(same paths, same column names, same calls into your backend modules) so that
app.py only has to lay things out.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from config import DATA_PROCESSED, DATA_RAW
from src.equipment_health.health import score_equipment
from weather_predictor import evaluate_weather_impact

ROOT = Path(__file__).resolve().parent

RM_DIR = ROOT / "reserve_mapping"
RM_MAP_HTML = RM_DIR / "data" / "prospectivity_map.html"
RM_TARGETS = RM_DIR / "data" / "top_exploration_targets.csv"
RM_FI_CSV = RM_DIR / "data" / "feature_importances.csv"
RM_SCORES_CSV = RM_DIR / "data" / "zone_scores.csv"

FORECAST_CSV = ROOT / "forecasting" / "output" / "forecast_results.csv"
FORECAST_JSON = ROOT / "forecasting" / "output" / "summary.json"


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> dict:
    """Production, equipment risk, satellite series and forecast. Raises FileNotFoundError
    if the pipeline has not been run."""
    prod = pd.read_csv(DATA_PROCESSED / "synthetic_production_weekly.csv", parse_dates=["week_start"])
    eq = pd.read_csv(DATA_PROCESSED / "synthetic_equipment_downtime_weekly.csv", parse_dates=["week_start"])
    forecast = pd.read_csv(FORECAST_CSV, parse_dates=["ds"]) if FORECAST_CSV.exists() else None
    return {
        "prod": prod,
        "risk": score_equipment(eq),
        "rain": pd.read_csv(DATA_RAW / "chirps_rain.csv", parse_dates=["date"]),
        "ndvi": pd.read_csv(DATA_RAW / "sentinel2_ndvi.csv", parse_dates=["date"]),
        "lst": pd.read_csv(DATA_RAW / "modis_lst.csv", parse_dates=["date"]),
        "sar": pd.read_csv(DATA_RAW / "sentinel1_vv.csv", parse_dates=["date"]),
        "forecast": forecast,
    }


@st.cache_data
def load_forecast_summary():
    """Contents of forecasting/output/summary.json, or None if it does not exist."""
    if FORECAST_JSON.exists():
        with open(FORECAST_JSON) as f:
            return json.load(f)
    return None


@st.cache_data
def load_reserve_outputs():
    """Reserve-mapping outputs. Returns None if the pipeline has not been run."""
    if not all(p.exists() for p in [RM_MAP_HTML, RM_TARGETS, RM_FI_CSV]):
        return None
    fi = pd.read_csv(RM_FI_CSV)
    # Real vs demo is read from the label source in zone_scores.csv (real runs are tagged REAL_...),
    # so it never depends on loading the model file. Default to demo if the file is missing.
    is_demo = True
    if RM_SCORES_CSV.exists():
        src = pd.read_csv(RM_SCORES_CSV, usecols=["label_source"])["label_source"].astype(str).str.upper()
        is_demo = not src.str.startswith("REAL").any()
    return {
        "is_demo": is_demo,
        "fi": fi,
        "map_html": RM_MAP_HTML.read_text(encoding="utf-8"),
        "targets": pd.read_csv(RM_TARGETS),
    }


# ── Weather adapter ───────────────────────────────────────────────────────────
LEVEL_MAP = {
    "HIGH": "warning", "CRITICAL": "warning",
    "MODERATE": "watch", "WARNING": "watch",
    "LOW": None, "NORMAL": None, "STABLE": None,
    "HIGH_HAZARD": "warning", "MODERATE_HAZARD": "watch",
}


def get_weather_alerts(week_ts, rain_raw, sar_raw) -> dict:
    """Derive weather inputs from the satellite data for the selected week and call
    evaluate_weather_impact(). Returns the result plus the inputs used."""
    week_end = week_ts + pd.Timedelta(days=6)

    # 48h rainfall: last 2 days of the week
    rain_48 = rain_raw[(rain_raw["date"] >= week_end - pd.Timedelta(days=1)) &
                       (rain_raw["date"] <= week_end)]["rainfall_mm"].sum()
    # 7d rainfall: full week
    rain_7d = rain_raw[(rain_raw["date"] >= week_ts) &
                       (rain_raw["date"] <= week_end)]["rainfall_mm"].sum()
    # Soil moisture proxy: normalise SAR VV for this week (higher VV dB = wetter)
    sar_week = sar_raw[(sar_raw["date"] >= week_ts) & (sar_raw["date"] <= week_end)]["sar_vv_db"]
    sar_all = sar_raw["sar_vv_db"]
    smi = float(((sar_week.mean() - sar_all.min()) / (sar_all.max() - sar_all.min())).clip(0, 1)) \
        if not sar_week.empty else 0.3

    # Consecutive dry days: days before this week with 0 rain
    prior = rain_raw[rain_raw["date"] < week_ts].sort_values("date", ascending=False)
    dry_days = int((prior["rainfall_mm"] == 0).cumprod().sum())

    result = evaluate_weather_impact(
        rainfall_48h_mm=round(float(rain_48), 2),
        soil_moisture_index=round(smi, 3),
        rainfall_7d_mm=round(float(rain_7d), 2),
        consecutive_dry_days=dry_days,
    )
    return {
        "wx": result,
        "rain_48": round(float(rain_48), 1),
        "rain_7d": round(float(rain_7d), 1),
        "smi": round(smi, 3),
        "dry_days": dry_days,
    }


def weather_to_alerts(wx: dict) -> list[dict]:
    """Convert the weather engine's output dict into the prescriptive engine's alert list."""
    mapping = {
        "waterlogging": "waterlogging",
        "road_risk": "road",
        "haul_friction": "haul_friction",
    }
    alerts = []
    for key, alert_type in mapping.items():
        level_str = wx[key].get("level", "LOW")
        engine_level = LEVEL_MAP.get(level_str.upper())
        if engine_level:
            alerts.append({"type": alert_type, "level": engine_level})
    return alerts
