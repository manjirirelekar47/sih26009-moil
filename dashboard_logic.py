"""
dashboard_logic.py - the dashboard's decision logic, shared with the FastAPI layer.

Every function here mirrors the VERIFIED Streamlit app.py step for step (same inputs,
same order, same calls into weather_predictor / equipment_health / prescriptive), so the
Next.js UI and the Streamlit app give the same answer for the same week.
app.py itself is NOT modified. If you ever change the logic in app.py, change it here too.

Run the self-check from the repo root:   py -3.11 check_dashboard_logic.py
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from config import DATA_PROCESSED, DATA_RAW
from src.equipment_health.health import fleet_summary, score_equipment
from src.prescriptive.engine import recommend
from weather_predictor import evaluate_weather_impact

ROOT = Path(__file__).resolve().parent
FORECAST_CSV = ROOT / "forecasting" / "output" / "forecast_results.csv"
RM_DIR = ROOT / "reserve_mapping"

# Same slider ranges as the Streamlit what-if simulator.
WHATIF_RANGES = {
    "rain48hMm": (0.0, 150.0), "rain7dMm": (0.0, 400.0), "soilMoistureIndex": (0.0, 1.0),
    "dryDays": (0, 30), "blastDelayDays": (0, 5), "shortfallRisk": (0.0, 1.0),
}
ALERT_KEYS = [("waterlogging", "Waterlogging"), ("road_risk", "Road risk"), ("haul_friction", "Haul friction"),
              ("slope_instability", "Slope instability"), ("dust_visibility", "Dust / visibility")]

# ---------------------------------------------------------------- data (loaded once)
@lru_cache(maxsize=1)
def load_data() -> dict:
    prod = pd.read_csv(DATA_PROCESSED / "synthetic_production_weekly.csv", parse_dates=["week_start"])
    eq = pd.read_csv(DATA_PROCESSED / "synthetic_equipment_downtime_weekly.csv", parse_dates=["week_start"])
    return {
        "prod": prod,
        "risk": score_equipment(eq),
        "rain_raw": pd.read_csv(DATA_RAW / "chirps_rain.csv", parse_dates=["date"]),
        "sar_raw": pd.read_csv(DATA_RAW / "sentinel1_vv.csv", parse_dates=["date"]),
        "forecast": pd.read_csv(FORECAST_CSV, parse_dates=["ds"]) if FORECAST_CSV.exists() else None,
    }


def weeks() -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in sorted(load_data()["prod"]["week_start"].unique())]


# ---------------------------------------------------------------- weather adapter (copied from app.py)
LEVEL_MAP = {
    "HIGH": "warning", "CRITICAL": "warning",
    "MODERATE": "watch", "WARNING": "watch",
    "LOW": None, "NORMAL": None, "STABLE": None,
    "HIGH_HAZARD": "warning", "MODERATE_HAZARD": "watch",
}


def get_weather_alerts(week_ts, rain_raw, sar_raw):
    """Derive weather inputs from real satellite data for the selected week and call Member 4's function."""
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
    return result, round(float(rain_48), 1), round(float(rain_7d), 1), round(smi, 3), dry_days


def weather_to_alerts(wx):
    """Convert Member 4's output dict -> prescriptive engine alert list."""
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


def _alert_rows(wx: dict) -> list[dict]:
    return [{"key": k, "label": label, "level": str(wx[k].get("level", "NORMAL")),
             "message": str(wx[k].get("message", ""))} for k, label in ALERT_KEYS if k in wx]


def _worst_note(rows: list[dict]) -> str:
    rank = {"warning": 2, "watch": 1}
    best = max(rows, key=lambda r: rank.get(LEVEL_MAP.get(r["level"].upper()) or "", 0), default=None)
    if best is None or not LEVEL_MAP.get(best["level"].upper()):
        return "No active weather alerts"
    return best["message"]


def weather_for_week(week_ts) -> dict:
    d = load_data()
    wx, rain_48, rain_7d, smi, dry = get_weather_alerts(pd.Timestamp(week_ts), d["rain_raw"], d["sar_raw"])
    rows = _alert_rows(wx)
    return {"alerts": rows, "delayFactor": float(wx.get("overall_delay_factor", 0)), "rain48hMm": rain_48,
            "rain7dMm": rain_7d, "soilMoistureIndex": smi, "dryDays": dry, "riskNote": _worst_note(rows)}


# ---------------------------------------------------------------- one week, exactly as app.py computes it
def week_snapshot(week: str | None = None) -> dict:
    d = load_data()
    prod = d["prod"]
    ts = pd.Timestamp(week) if week else prod["week_start"].max()
    rows = prod[prod["week_start"] == ts]
    if rows.empty:
        raise ValueError(f"week {week} not found; valid weeks are {weeks()[0]} to {weeks()[-1]}")
    week_prod = rows.iloc[0]
    week_risk = d["risk"][d["risk"]["week_start"] == ts]
    fleet = fleet_summary(week_risk)

    shortfall_pct = float(week_prod["shortfall_pct"])
    shortfall_score = max(0.0, min(1.0, shortfall_pct / 30.0))
    is_anomaly = False
    forecast = d["forecast"]
    if forecast is not None:
        fw = forecast[forecast["ds"] == ts]
        if not fw.empty and pd.notna(fw.iloc[0].get("risk_score_pct")):
            shortfall_score = float(fw.iloc[0]["risk_score_pct"]) / 100.0
        if not fw.empty and "is_anomaly" in fw.columns:
            is_anomaly = bool(fw.iloc[0]["is_anomaly"])

    wx, rain_48, rain_7d, smi, dry_days = get_weather_alerts(ts, d["rain_raw"], d["sar_raw"])
    alerts_in = weather_to_alerts(wx)
    blast = int(week_prod["blast_delay_days"])
    cards = recommend(
        shortfall_risk=shortfall_score,
        alerts=alerts_in,
        downtime_risk=fleet["downtime_risk"],
        blast_delay_days=blast,
        worst_equipment=fleet["worst_equipment"],
        is_anomaly=is_anomaly,
    )
    return {
        "week_ts": ts, "weekStart": ts.strftime("%Y-%m-%d"),
        "plannedTonnes": float(week_prod["planned_tonnes"]), "actualTonnes": float(week_prod["actual_tonnes"]),
        "shortfallPct": shortfall_pct, "shortfallRisk": round(shortfall_score, 4), "isAnomaly": is_anomaly,
        "blastDelayDays": blast,
        "fleet": {"downtimeRisk": str(fleet["downtime_risk"]), "worstEquipment": str(fleet["worst_equipment"]),
                  "nHigh": int(fleet["n_high"]), "nMedium": int(fleet["n_medium"])},
        "weather": {"alerts": _alert_rows(wx), "delayFactor": float(wx.get("overall_delay_factor", 0)),
                    "rain48hMm": rain_48, "rain7dMm": rain_7d, "soilMoistureIndex": smi, "dryDays": dry_days},
        "engineAlerts": alerts_in,
        "cards": cards,
    }


def whatif(week: str | None = None, **over) -> dict:
    """Same as the Streamlit what-if simulator: sliders start from the selected week's values."""
    base = week_snapshot(week)
    fleet_now = str(base["fleet"]["downtimeRisk"]).lower()
    start = {
        "rain48hMm": min(base["weather"]["rain48hMm"], 150.0), "rain7dMm": min(base["weather"]["rain7dMm"], 400.0),
        "soilMoistureIndex": min(max(base["weather"]["soilMoistureIndex"], 0.0), 1.0),
        "dryDays": int(min(base["weather"]["dryDays"], 30)),
        "fleetDowntimeRisk": fleet_now if fleet_now in ("low", "medium", "high") else "low",
        "blastDelayDays": int(min(base["blastDelayDays"], 5)),
        "shortfallRisk": min(max(base["shortfallRisk"], 0.0), 1.0),
    }
    use = dict(start)
    for k, v in over.items():
        if v is None or k not in use:
            continue
        if k == "fleetDowntimeRisk":
            if str(v).lower() not in ("low", "medium", "high"):
                raise ValueError("fleetDowntimeRisk must be low, medium or high")
            use[k] = str(v).lower()
        else:
            lo, hi = WHATIF_RANGES[k]
            use[k] = type(start[k])(min(max(v, lo), hi))

    sim_wx = evaluate_weather_impact(
        rainfall_48h_mm=use["rain48hMm"], soil_moisture_index=use["soilMoistureIndex"],
        rainfall_7d_mm=use["rain7dMm"], consecutive_dry_days=int(use["dryDays"]),
    )
    sim_alerts = weather_to_alerts(sim_wx)
    sim_cards = recommend(
        shortfall_risk=use["shortfallRisk"], alerts=sim_alerts, downtime_risk=use["fleetDowntimeRisk"],
        blast_delay_days=int(use["blastDelayDays"]), worst_equipment=base["fleet"]["worstEquipment"],
        is_anomaly=base["isAnomaly"],
    )
    sim_delay = float(sim_wx.get("overall_delay_factor", 0))
    return {
        "weekStart": base["weekStart"], "inputs": use, "startInputs": start,
        "ranges": {k: list(v) for k, v in WHATIF_RANGES.items()},
        "baseline": {"delayFactor": base["weather"]["delayFactor"], "alertCount": len(base["engineAlerts"]),
                     "cards": base["cards"]},
        "simulated": {"delayFactor": sim_delay, "alerts": _alert_rows(sim_wx), "alertCount": len(sim_alerts),
                      "cards": sim_cards},
        "delta": {"delayPts": round((sim_delay - base["weather"]["delayFactor"]) * 100, 1),
                  "alerts": len(sim_alerts) - len(base["engineAlerts"])},
    }


# ---------------------------------------------------------------- reserve mapping (Member 2 outputs)
def reserve_importances() -> dict:
    fi = pd.read_csv(RM_DIR / "data" / "feature_importances.csv").sort_values("importance", ascending=False)
    is_demo = True
    scores_csv = RM_DIR / "data" / "zone_scores.csv"
    if scores_csv.exists():
        src = pd.read_csv(scores_csv, usecols=["label_source"])["label_source"].astype(str).str.upper()
        is_demo = not src.str.startswith("REAL").any()
    total = float(fi["importance"].sum()) or 1.0
    rows = [{"feature": str(r.feature), "importance": round(float(r.importance), 4),
             "sharePct": round(float(r.importance) / total * 100, 1)} for r in fi.itertuples()]
    return {"features": rows, "topDriver": rows[0]["feature"] if rows else None,
            "topDriverSharePct": rows[0]["sharePct"] if rows else None, "isDemo": is_demo}
