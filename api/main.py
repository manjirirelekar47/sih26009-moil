"""
api/main.py — HTTP layer for OreSentinel (SIH 26009 · MOIL Limited).

Thin FastAPI wrapper over the EXISTING prototype modules. No model logic is
reimplemented here: it calls src.prescriptive.engine, src.equipment_health.health,
weather_predictor, and reads the CSV artefacts the pipeline already produces
(data/processed/*.csv, reserve_mapping/data/*.csv, forecasting/output/*).

Run from the repo root (the folder that contains config.py and data/):
    pip install -r api/requirements-api.txt
    uvicorn api.main:app --reload --port 8000

Then open http://localhost:8000/docs to see every route.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- make the repo root importable (config.py, src/, weather_predictor.py) ---
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA = ROOT / "data" / "processed"
RM = ROOT / "reserve_mapping" / "data"
FC = ROOT / "forecasting" / "output"
GRID_CELL_DEG = 0.01          # mirrors config.GRID_CELL_DEG (~1.1 km cells)

# --- prototype modules (optional: the API still boots if one is missing) ----
LOADED: dict[str, bool] = {}

try:
    from src.prescriptive.engine import recommend, downtime_cuts_from_csv
    LOADED["prescriptive"] = True
except Exception:
    recommend = downtime_cuts_from_csv = None          # type: ignore
    LOADED["prescriptive"] = False

try:
    from weather_predictor import evaluate_weather_impact
    LOADED["weather_rules"] = True
except Exception:
    evaluate_weather_impact = None                     # type: ignore
    LOADED["weather_rules"] = False

try:
    from src.equipment_health.health import score_equipment, fleet_summary
    LOADED["equipment_health"] = True
except Exception:
    score_equipment = fleet_summary = None             # type: ignore
    LOADED["equipment_health"] = False

# Shared decision logic: mirrors the verified Streamlit app.py (see dashboard_logic.py).
DL_ERROR: str | None = None
try:
    import dashboard_logic as DL
    LOADED["dashboard_logic"] = True
except Exception as _e:                                # noqa: BLE001
    DL = None                                          # type: ignore
    DL_ERROR = repr(_e)
    LOADED["dashboard_logic"] = False


app = FastAPI(
    title="OreSentinel API",
    version="1.0.0",
    description="SIH 26009 · MOIL Limited · manganese reserve, production & shortfall intelligence",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------ helpers ---
def _production() -> pd.DataFrame:
    return pd.read_csv(
        DATA / "synthetic_production_weekly.csv", parse_dates=["week_start"]
    ).sort_values("week_start")


def _equipment_risk() -> pd.DataFrame:
    return pd.read_csv(
        DATA / "equipment_risk.csv", parse_dates=["week_start"]
    ).sort_values("week_start")


def _weekly_features() -> pd.DataFrame:
    return pd.read_csv(
        DATA / "weekly_features.csv", parse_dates=["week_start"]
    ).sort_values("week_start")


def _forecast() -> pd.DataFrame:
    return pd.read_csv(FC / "forecast_results.csv", parse_dates=["ds"]).sort_values("ds")


def _zone_scores() -> pd.DataFrame:
    return pd.read_csv(RM / "zone_scores.csv")


def _need_logic() -> None:
    """Fail loudly instead of silently returning numbers that differ from the Streamlit app."""
    if DL is None:
        raise HTTPException(status_code=503, detail=f"dashboard_logic failed to load: {DL_ERROR}")


def _card_json(c: dict, week_start: str) -> dict:
    return {
        "id": str(c.get("rule_id", "")),
        "title": str(c.get("title", "")),
        "priority": str(c.get("priority", "Low")).lower(),
        "family": str(c.get("family", "")),
        "rationale": str(c.get("reason", "")),
        "action": str(c.get("action", "")),
        "impactLabel": "Prescribed action",
        "impactValue": str(c.get("action", ""))[:90],
        "site": "Balaghat",
        "weekStart": week_start,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# --------------------------------------------------------------- meta/health ---
@app.get("/api/health")
def health() -> dict:
    """Quick check: which prototype modules loaded, and where the data lives."""
    return {
        "status": "ok",
        "repo_root": str(ROOT),
        "modules_loaded": LOADED,
        "dashboard_logic_error": DL_ERROR,
        "files_present": {
            "production": (DATA / "synthetic_production_weekly.csv").exists(),
            "equipment_risk": (DATA / "equipment_risk.csv").exists(),
            "weekly_features": (DATA / "weekly_features.csv").exists(),
            "forecast_results": (FC / "forecast_results.csv").exists(),
            "zone_scores": (RM / "zone_scores.csv").exists(),
        },
    }


# ------------------------------------------------------- reserve mapping (M2) ---
@app.get("/api/reserves/zones")
def reserves_zones(min_score: float = 0.8, limit: int = 600) -> list[dict]:
    """High-prospectivity grid cells as GeoJSON rings.

    NOTE: zone_scores.csv holds `prospectivity_score` (0–1), NOT tonnage.
    The `prospectivity` field therefore carries that score. See START_HERE.md.
    """
    df = _zone_scores()
    df = df[df["prospectivity_score"] >= min_score].nlargest(limit, "prospectivity_score")
    d = GRID_CELL_DEG / 2
    out: list[dict] = []
    for r in df.itertuples():
        lon, lat = float(r.lon), float(r.lat)
        out.append({
            "id": str(r.zone_id),
            "name": f"Zone {r.zone_id}",
            "coordinates": [
                [round(lon - d, 5), round(lat - d, 5)],
                [round(lon + d, 5), round(lat - d, 5)],
                [round(lon + d, 5), round(lat + d, 5)],
                [round(lon - d, 5), round(lat + d, 5)],
                [round(lon - d, 5), round(lat - d, 5)],
            ],
            "prospectivity": round(float(r.prospectivity_score), 4),
        })
    return out


@app.get("/api/reserves/mines")
def reserves_mines(limit: int = 4) -> list[dict]:
    """Top exploration targets, re-labelled to the dashboard's Mine A–D slots.

    `status` is derived from the prospectivity score band (operational / warning /
    inspection) — it is NOT a real operational status from the data.
    """
    df = pd.read_csv(RM / "top_exploration_targets.csv").head(limit)
    names = ["Mine A", "Mine B", "Mine C", "Mine D"]
    out: list[dict] = []
    for i, r in enumerate(df.itertuples()):
        score = round(float(r.prospectivity_score), 4)
        out.append({
            "id": f"mine-{names[i][-1].lower()}",
            "name": names[i] if i < len(names) else f"Target {r.rank}",
            "lng": float(r.lon),
            "lat": float(r.lat),
            "prospectivity": score,
            "distToReferenceMineKm": float(r.dist_to_reference_mine_km),
            "status": "operational" if score >= 0.99 else "warning" if score >= 0.95 else "inspection",
        })
    return out


@app.get("/api/reserves/insights")
def reserves_insights() -> dict:
    """Mapping-quality counts. Tonnage fields are null — see START_HERE.md."""
    df = _zone_scores()
    return {
        "totalReservesMt": None,          # not derivable: no tonnage column exists
        "surveyDeltaPct": None,           # not derivable: single survey, no baseline
        "newZones": int((df["prospectivity_score"] >= 0.9).sum()),
        "mappingConfidencePct": 86,       # from the design mockup, not from data
        "zonesScored": int(len(df)),
        "mineralizedObservations": int(df["n_mineralized_obs"].sum()),
        "labelSource": sorted(df["label_source"].dropna().unique().tolist()),
    }


@app.get("/api/reserves/layers/{layer}")
def reserve_layer(layer: str) -> dict:
    """Per-cell values for a layer toggle, so the frontend can colour the map."""
    df = _zone_scores()
    feats = pd.read_csv(DATA / "zone_features.csv") if (DATA / "zone_features.csv").exists() else None

    known = {
        "estimatedreserves": "prospectivity_score",
        "ndvi": "ndvi_median",
        "soismoisture": "sar_vv_mean_db",
        "soilmoisture": "sar_vv_mean_db",
        "landtemperature": "lst_mean_c",
        "geologicalformations": "label_class",
        "mineboundary": None,
        "satelliteimagery": None,
    }
    key = layer.lower().replace("_", "").replace("-", "")
    column = known.get(key)

    if column is None:
        return {"layer": layer, "values": [], "note": "Base/imagery layer — no per-cell values."}

    if column in df.columns:
        points = [
            {"id": str(r.zone_id), "lon": float(r.lon), "lat": float(r.lat),
             "value": float(getattr(r, column))}
            for r in df.itertuples()
        ]
    elif feats is not None and column in feats.columns:
        points = [
            {"id": str(r.zone_id), "lon": float(r.lon), "lat": float(r.lat),
             "value": float(getattr(r, column))}
            for r in feats.itertuples()
        ]
    else:
        return {"layer": layer, "values": [], "note": f"Column {column} not found."}

    return {"layer": layer, "column": column, "count": len(points), "values": points}


# ------------------------------------------------ forecasting + shortfall (M3) ---
@app.get("/api/production/trend")
def production_trend(months: int = 12) -> list[dict]:
    """Actual vs forecast vs target, aggregated to calendar months (tonnes).

    Weekly rows are resampled to months with a real SUM (using min_count=1 so a
    month with no actuals stays null instead of becoming 0). Forecast is emitted
    from the last month that has an actual, so the two lines join.
    """
    df = _forecast().set_index("ds")
    m = df.resample("MS").agg({
        "yhat": "sum",
        "actual": lambda s: s.sum(min_count=1),
        "target": "sum",
    })
    last_actual = m["actual"].last_valid_index()

    rows = []
    for ts, r in m.iterrows():
        rows.append({
            "month": ts.strftime("%b"),
            "monthIso": ts.strftime("%Y-%m"),
            "actual": None if pd.isna(r["actual"]) else round(float(r["actual"]), 1),
            "forecast": round(float(r["yhat"]), 1) if last_actual is not None and ts >= last_actual else None,
            "target": round(float(r["target"]), 1),
        })
    return rows[-max(1, min(months, 24)):]


@app.get("/api/production/forecast")
def production_forecast() -> dict:
    """Variance summary built from forecasting/output/summary.json + results CSV."""
    import json

    summary_path = FC / "summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    df = _forecast()
    future = df[df["actual"].isna()]
    horizon = summary.get("future_weeks_forecasted", 12)
    fut = future.head(horizon)
    last_known = df[df["actual"].notna()].iloc[-1] if df["actual"].notna().any() else df.iloc[-1]

    target = float(last_known["target"])
    forecast = float(fut["yhat"].mean()) if len(fut) else float(last_known["yhat"])
    variance = round((forecast - target) / target * 100, 1) if target else 0.0

    risk = str(summary.get("current_risk_level", last_known.get("risk_level", "Moderate")))
    risk_level = {"low": "Low", "moderate": "Medium", "medium": "Medium",
                  "high": "High"}.get(risk.lower(), "Medium")

    returns = df["actual"].pct_change()
    corr = 0.0
    if "risk_score_pct" in df.columns:
        corr = float(df["risk_score_pct"].corr(returns.fillna(0)))

    return {
        "targetMt": target,               # NOTE: tonnes, not Mt — see START_HERE.md
        "forecastMt": round(forecast, 1),
        "variancePct": variance,
        "riskLevel": risk_level,
        "unit": "tonnes",
        "horizonWeeks": int(horizon),
        "latestWeek": str(summary.get("latest_week", "")),
        "factors": [
            {"id": "f-risk", "label": "Model risk score (latest week)",
             "note": "forecasting/output/forecast_results.csv",
             "impactPct": round(-float(last_known["risk_score_pct"]), 1)},
            {"id": "f-anomaly", "label": "Anomalous weeks detected",
             "note": f"{summary.get('num_anomalies_detected', 0)} flagged weeks",
             "impactPct": -int(summary.get("num_anomalies_detected", 0))},
            {"id": "f-corr", "label": "Risk score vs production change",
             "note": "Pearson correlation on weekly data",
             "impactPct": round(corr * 10, 1)},
        ],
        "insight": (
            f"Weekly production plan is {target:,.0f} t against a {horizon}-week forecast "
            f"averaging {forecast:,.0f} t ({variance:+.1f}%). Model risk level is {risk}; "
            f"{summary.get('num_anomalies_detected', 0)} anomalous weeks were detected. "
            "Risk score and production change correlate at "
            f"{corr:+.2f}, so the risk signal alone does not explain the variance."
        ),
    }


@app.get("/api/shortfall/predictions")
def shortfall_predictions(limit: int = 5) -> list[dict]:
    """Highest-risk weeks from the forecast model, as alert objects."""
    df = _forecast()
    hot = df.nlargest(limit, "risk_score_pct") if "risk_score_pct" in df.columns else df.tail(limit)
    out: list[dict] = []
    for i, r in enumerate(hot.itertuples()):
        score = float(r.risk_score_pct)
        out.append({
            "id": f"risk-{i}",
            "severity": "high" if score >= 15 else "medium" if score >= 8 else "low",
            "title": f"Week of {pd.Timestamp(r.ds).strftime('%d %b %Y')} — risk {score:.1f}%",
            "description": (
                f"Forecast {float(r.yhat):,.0f} t vs target {float(r.target):,.0f} t"
                + (" · flagged as an anomaly" if bool(r.is_anomaly) else "")
            ),
            "createdAt": _now(),
            "href": "/production-forecast",
        })
    return out


# ------------------------------------------------------------- weather (M4) ---
@app.get("/api/environment/weather")
def weather(weeks: int = 7, week: str | None = None) -> list[dict]:
    """Weekly satellite/rainfall series plus the SAME weather rules the Streamlit app uses.

    Soil moisture, 48h/7d rainfall, dry days and the alert levels come from
    dashboard_logic.weather_for_week(), i.e. the daily CHIRPS / Sentinel-1 files, exactly
    as app.py computes them. `week` (YYYY-MM-DD, a Monday) ends the window there.
    """
    _need_logic()
    wf = _weekly_features()
    if week:
        wf = wf[wf["week_start"] <= pd.Timestamp(week)]
    wf = wf.tail(max(1, weeks))

    prod = _production()
    out: list[dict] = []
    for r in wf.itertuples():
        gate = prod[prod["week_start"] == r.week_start]
        fleet_dt = float(gate["fleet_downtime_pct"].iloc[0]) if len(gate) else 0.0
        wx = DL.weather_for_week(r.week_start)
        out.append({
            "day": r.week_start.strftime("%d %b"),
            "weekStart": r.week_start.strftime("%Y-%m-%d"),
            "rainfallMm": round(float(r.rainfall_mm), 1),
            "ndvi": round(float(r.ndvi), 3),
            "soilMoistureIndex": wx["soilMoistureIndex"],
            "landTempC": round(float(r.lst_c), 1),
            "fleetDowntimePct": fleet_dt,
            "riskNote": wx["riskNote"],
            "alerts": wx["alerts"],
            "delayFactor": wx["delayFactor"],
            "rain48hMm": wx["rain48hMm"],
            "rain7dMm": wx["rain7dMm"],
            "dryDays": wx["dryDays"],
        })
    return out


# ------------------------------------------------------- equipment health (M5) ---
@app.get("/api/equipment/health")
def equipment_health(band: str | None = None) -> list[dict]:
    """Latest-week per-machine downtime risk from data/processed/equipment_risk.csv.

    `healthPct` = (1 − risk_score) × 100. `status` maps the model's risk band:
    high → 'down' (meaning HIGH PREDICTED DOWNTIME RISK, not physically stopped),
    medium → 'attention', low → 'operational'.
    """
    df = _equipment_risk()
    latest_week = df["week_start"].max()
    wk = df[df["week_start"] == latest_week]
    if band:
        wk = wk[wk["risk_band"] == band]

    out: list[dict] = []
    for r in wk.sort_values("risk_score", ascending=False).itertuples():
        risk = float(r.risk_score)
        out.append({
            "id": str(r.equipment_id),
            "name": f"{str(r.equipment_type).title()} {r.equipment_id}",
            "type": str(r.equipment_type),
            "site": "Balaghat",
            "ageYears": float(r.age_years),
            "riskScore": round(risk, 4),
            "riskBand": str(r.risk_band),
            "mainDriver": str(r.main_driver),
            "downtimePct8w": round(float(r.downtime_pct_8w), 2),
            "healthPct": round((1.0 - risk) * 100),
            "status": "down" if r.risk_band == "high" else "attention" if r.risk_band == "medium" else "operational",
            "nextServiceInDays": 3 if r.risk_band == "high" else 14 if r.risk_band == "medium" else 30,
            "weekStart": r.week_start.strftime("%Y-%m-%d"),
        })
    return out


# ------------------------------------------------------ prescriptive engine (M5) ---
@app.get("/api/actions/prescriptive")
def prescriptive_actions(week: str | None = None) -> list[dict]:
    """Runs the real rules engine for a week (default: latest) with the SAME inputs as
    the Streamlit app: forecast risk, weather alerts from satellite data, fleet downtime
    band from equipment health, blast delays and anomaly flag."""
    _need_logic()
    try:
        snap = DL.week_snapshot(week)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [_card_json(c, snap["weekStart"]) for c in snap["cards"]]


# ------------------------------------------------------------------ analytics ---
@app.get("/api/alerts/active")
def active_alerts(week: str | None = None) -> list[dict]:
    """Dashboard alert feed: top prescriptive cards + the riskiest forecast weeks."""
    out: list[dict] = []

    for i, c in enumerate(prescriptive_actions(week)[:3]):
        out.append({
            "id": f"act-{i}",
            "severity": c["priority"] if c["priority"] in ("high", "medium", "low") else "low",
            "title": c["title"],
            "description": c["rationale"],
            "createdAt": _now(),
            "href": "/corrective-actions",
        })

    for r in shortfall_predictions(limit=2):
        out.append({
            "id": r["id"],
            "severity": r["severity"],
            "title": r["title"],
            "description": r["description"],
            "createdAt": _now(),
            "href": "/shortfall-prediction",
        })

    return out[:5]


@app.get("/api/dashboard/kpis")
def dashboard_kpis() -> list[dict]:
    """Five KPI cards. Units are TONNES, not Mt — see START_HERE.md."""
    prod = _production()
    latest = prod.iloc[-1]
    planned = float(latest["planned_tonnes"])
    actual = float(latest["actual_tonnes"])
    achieved = (actual / planned * 100.0) if planned else 0.0

    eq = _equipment_risk()
    last_eq = eq[eq["week_start"] == eq["week_start"].max()]
    healthy = float((last_eq["risk_band"] == "low").mean() * 100.0) if len(last_eq) else 0.0

    zs = _zone_scores()
    high_zones = int((zs["prospectivity_score"] >= 0.9).sum())

    _fx_all = _forecast()
    fx = _fx_all[_fx_all["risk_score_pct"].notna()].iloc[-1]
    risk_pct = float(fx["risk_score_pct"])

    return [
        {
            "id": "reserves",
            "label": "High-prospectivity Zones",
            "value": high_zones,
            "unit": "zones",
            "footnote": f"score ≥ 0.90 · {len(zs)} cells scored",
        },
        {
            "id": "production",
            "label": "Current Production (weekly)",
            "value": round(actual, 1),
            "unit": "t",
            "deltaPct": round((actual - planned) / planned * 100, 1) if planned else 0.0,
            "trend": "up" if actual >= planned else "down",
            "footnote": "vs weekly plan",
        },
        {
            "id": "target",
            "label": "Planned Production (weekly)",
            "value": round(planned, 1),
            "unit": "t",
            "progressPct": round(achieved),
            "footnote": f"{achieved:.1f}% of weekly plan achieved",
        },
        {
            "id": "shortfall",
            "label": "Shortfall Risk (model)",
            "value": round(risk_pct, 1),
            "unit": "%",
            "severity": "high" if risk_pct >= 15 else "medium" if risk_pct >= 8 else "low",
            "footnote": f"{fx['risk_level']} risk",
        },
        {
            "id": "equipment",
            "label": "Fleet Health",
            "value": round(healthy),
            "unit": "%",
            "footnote": f"{len(last_eq)} machines · week {latest['week_start'].strftime('%d %b %Y')}",
        },
    ]


@app.get("/api/dashboard/quick-actions")
def quick_actions() -> list[dict]:
    """Static navigation shortcuts (no data source needed)."""
    return [
        {"id": "q1", "label": "View Reserve Map", "icon": "map", "href": "/reserve-mapping"},
        {"id": "q2", "label": "Check Forecast", "icon": "trending", "href": "/production-forecast"},
        {"id": "q3", "label": "See Shortfall Risks", "icon": "alert", "href": "/shortfall-prediction"},
        {"id": "q4", "label": "Equipment Status", "icon": "gear", "href": "/equipment-health"},
        {"id": "q5", "label": "Recommended Actions", "icon": "shield", "href": "/corrective-actions"},
    ]


@app.get("/api/reports")
def reports() -> list[dict]:
    """Available artefacts the dashboard can link to for download."""
    items = [
        ("Forecast chart", FC / "forecast_chart.png", "image/png"),
        ("Forecast results (weekly)", FC / "forecast_results.csv", "text/csv"),
        ("Forecast summary", FC / "summary.json", "application/json"),
        ("Zone prospectivity scores", RM / "zone_scores.csv", "text/csv"),
        ("Top exploration targets", RM / "top_exploration_targets.csv", "text/csv"),
        ("Equipment risk scores", DATA / "equipment_risk.csv", "text/csv"),
        ("Weekly satellite features", DATA / "weekly_features.csv", "text/csv"),
        ("Weekly production", DATA / "synthetic_production_weekly.csv", "text/csv"),
    ]
    return [
        {
            "id": f"r{i}",
            "title": title,
            "available": path.exists(),
            "sizeKb": round(path.stat().st_size / 1024, 1) if path.exists() else None,
            "path": str(path.relative_to(ROOT)) if path.exists() else None,
            "mimeType": mime,
        }
        for i, (title, path, mime) in enumerate(items)
    ]


@app.get("/api/settings")
def settings() -> dict:
    """Placeholder — no persistence layer exists in the prototype."""
    return {
        "profile": {"name": "Samiksha Patil", "role": "Analyst", "organisation": "MOIL Limited"},
        "preferences": {"alertEmails": True, "pushNotifications": False,
                        "weeklyDigest": True, "autoRefresh": True},
        "note": "Not persisted — the prototype has no database. Add PostgreSQL/PostGIS to make this real.",
    }


# ------------------------------------------- week selector, what-if, explainability ---
@app.get("/api/weeks")
def weeks_list() -> dict:
    """Weeks the dashboard can show (Mondays), for the week selector."""
    _need_logic()
    ws = DL.weeks()
    return {"weeks": ws, "latest": ws[-1] if ws else None}


@app.get("/api/week/snapshot")
def api_week_snapshot(week: str | None = None) -> dict:
    """Everything the Streamlit page shows for one week: production, forecast risk,
    fleet band, weather inputs + 5 alerts, and the prescriptive cards."""
    _need_logic()
    try:
        snap = DL.week_snapshot(week)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    snap = {k: v for k, v in snap.items() if k != "week_ts"}
    snap["cards"] = [_card_json(c, snap["weekStart"]) for c in snap["cards"]]
    return snap


class WhatIfIn(BaseModel):
    """Every field is optional; anything omitted keeps the selected week's actual value."""
    week: str | None = None
    rain48hMm: float | None = None
    rain7dMm: float | None = None
    soilMoistureIndex: float | None = None
    dryDays: int | None = None
    fleetDowntimeRisk: str | None = None
    blastDelayDays: int | None = None
    shortfallRisk: float | None = None


@app.post("/api/whatif")
def whatif(body: WhatIfIn) -> dict:
    """The Streamlit what-if simulator: re-runs weather alerts and the rules engine."""
    _need_logic()
    payload = body.model_dump() if hasattr(body, "model_dump") else body.dict()
    try:
        res = DL.whatif(**payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    ws = res["weekStart"]
    res["baseline"]["cards"] = [_card_json(c, ws) for c in res["baseline"]["cards"]]
    res["simulated"]["cards"] = [_card_json(c, ws) for c in res["simulated"]["cards"]]
    return res


@app.get("/api/reserves/importances")
def reserves_importances() -> dict:
    """Explainability: which inputs drive the prospectivity score (from Member 2's model)."""
    _need_logic()
    try:
        return DL.reserve_importances()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"missing file: {e}")
