"""
SIH 26009 — MOIL Dashboard
Members: Data Pipeline + Equipment Health + Forecasting + Weather + Prescriptive Engine
Run from repo root:  streamlit run app.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config import DATA_PROCESSED, DATA_RAW
from src.equipment_health.health import score_equipment, fleet_summary
from src.prescriptive.engine import recommend, risk_band
from weather_predictor import evaluate_weather_impact
import streamlit.components.v1 as components

RM_DIR      = ROOT / "reserve_mapping"
RM_MODEL    = RM_DIR / "models" / "prospectivity_model.joblib"
RM_MAP_HTML = RM_DIR / "data" / "prospectivity_map.html"
RM_TARGETS  = RM_DIR / "data" / "top_exploration_targets.csv"
RM_FI_CSV   = RM_DIR / "data" / "feature_importances.csv"

FORECAST_CSV   = ROOT / "forecasting" / "output" / "forecast_results.csv"
FORECAST_JSON  = ROOT / "forecasting" / "output" / "summary.json"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MOIL Mining Dashboard — SIH 26009",
    page_icon="⛏️",
    layout="wide",
)

st.markdown("""
<style>
body { background: #f0f4f8; }
.metric-card {
    background: white; border-radius: 12px;
    padding: 1rem 1.4rem;
    box-shadow: 0 1px 6px rgba(0,0,0,.08); margin-bottom: .5rem;
}
.band-high      { color: #c0392b; font-weight: 700; }
.band-medium    { color: #e67e22; font-weight: 700; }
.band-low       { color: #27ae60; font-weight: 700; }
.band-moderate  { color: #e67e22; font-weight: 700; }
.band-critical  { color: #c0392b; font-weight: 700; }
.card-high   { border-left:5px solid #c0392b; background:#fff5f5; border-radius:8px; padding:.8rem 1rem; margin-bottom:.5rem; }
.card-medium { border-left:5px solid #e67e22; background:#fffbf0; border-radius:8px; padding:.8rem 1rem; margin-bottom:.5rem; }
.card-low    { border-left:5px solid #27ae60; background:#f0fff4; border-radius:8px; padding:.8rem 1rem; margin-bottom:.5rem; }
.weather-high     { background:#fff0f0; border:1px solid #e74c3c; border-radius:8px; padding:.6rem .9rem; margin-bottom:.4rem; }
.weather-moderate { background:#fffbf0; border:1px solid #e67e22; border-radius:8px; padding:.6rem .9rem; margin-bottom:.4rem; }
.weather-low      { background:#f0fff4; border:1px solid #27ae60; border-radius:8px; padding:.6rem .9rem; margin-bottom:.4rem; }
.weather-normal   { background:#f8f9fa; border:1px solid #ccc;    border-radius:8px; padding:.6rem .9rem; margin-bottom:.4rem; }
.block-container { padding-top: 1.5rem; }
h2, h3 { color: #1f4e79; }
@media (max-width: 768px) { .metric-card { padding: .6rem .8rem; } }
</style>
""", unsafe_allow_html=True)

st.title("⛏️ MOIL Mining Intelligence Dashboard")
st.caption("SIH 26009 | Balaghat Mine | Reserve Mapping | Forecasting | Weather | Equipment Health | Prescriptive Actions | What-if")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    prod     = pd.read_csv(DATA_PROCESSED / "synthetic_production_weekly.csv", parse_dates=["week_start"])
    eq       = pd.read_csv(DATA_PROCESSED / "synthetic_equipment_downtime_weekly.csv", parse_dates=["week_start"])
    risk     = score_equipment(eq)
    rain_raw = pd.read_csv(DATA_RAW / "chirps_rain.csv",    parse_dates=["date"])
    ndvi_raw = pd.read_csv(DATA_RAW / "sentinel2_ndvi.csv", parse_dates=["date"])
    lst_raw  = pd.read_csv(DATA_RAW / "modis_lst.csv",      parse_dates=["date"])
    sar_raw  = pd.read_csv(DATA_RAW / "sentinel1_vv.csv",   parse_dates=["date"])
    forecast = pd.read_csv(FORECAST_CSV, parse_dates=["ds"]) if FORECAST_CSV.exists() else None
    return prod, eq, risk, rain_raw, ndvi_raw, lst_raw, sar_raw, forecast

try:
    prod, eq, risk, rain_raw, ndvi_raw, lst_raw, sar_raw, forecast = load_data()
except FileNotFoundError as e:
    st.error(f"Missing data file: {e}\nRun the pipeline first.")
    st.stop()

all_weeks = sorted(prod["week_start"].dt.date.unique())
@st.cache_data
def load_reserve_outputs():
    """Member 2 outputs. Returns None if the pipeline has not been run."""
    if not all(p.exists() for p in [RM_MAP_HTML, RM_TARGETS, RM_FI_CSV]):
        return None
    is_demo = True   # safe default: show the DEMO label unless the model says otherwise
    fi = pd.read_csv(RM_FI_CSV)
    try:
        sys.path.append(str(RM_DIR))
        from step3_train_model import load_bundle, get_feature_importances
        bundle = load_bundle(str(RM_MODEL))
        is_demo = bool(bundle.get("is_demo", True))
        fi = get_feature_importances(bundle)
    except Exception:
        pass   # fall back to the CSV
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
    sar_all  = sar_raw["sar_vv_db"]
    smi = float(((sar_week.mean() - sar_all.min()) / (sar_all.max() - sar_all.min())).clip(0, 1)) \
          if not sar_week.empty else 0.3

    # Consecutive dry days: days before this week with 0 rain
    prior = rain_raw[rain_raw["date"] < week_ts].sort_values("date", ascending=False)
    dry_days = int((prior["rainfall_mm"] == 0).cumprod().sum())

    result = evaluate_weather_impact(
        rainfall_48h_mm     = round(float(rain_48), 2),
        soil_moisture_index = round(smi, 3),
        rainfall_7d_mm      = round(float(rain_7d), 2),
        consecutive_dry_days= dry_days,
    )
    return result, round(float(rain_48), 1), round(float(rain_7d), 1), round(smi, 3), dry_days


def weather_to_alerts(wx):
    """Convert Member 4's output dict → prescriptive engine alert list."""
    mapping = {
        "waterlogging": "waterlogging",
        "road_risk":    "road",
        "haul_friction":"haul_friction",
    }
    alerts = []
    for key, alert_type in mapping.items():
        level_str = wx[key].get("level", "LOW")
        engine_level = LEVEL_MAP.get(level_str.upper())
        if engine_level:
            alerts.append({"type": alert_type, "level": engine_level})
    return alerts


def weather_css(level):
    l = level.upper()
    if l in ("HIGH", "CRITICAL", "HIGH_HAZARD"):   return "weather-high"
    if l in ("MODERATE", "WARNING", "MODERATE_HAZARD"): return "weather-moderate"
    if l in ("LOW", "STABLE", "NORMAL"):            return "weather-low"
    return "weather-normal"

def weather_icon(level):
    l = level.upper()
    if l in ("HIGH", "CRITICAL", "HIGH_HAZARD"):        return "🔴"
    if l in ("MODERATE", "WARNING", "MODERATE_HAZARD"): return "🟠"
    return "🟢"

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("Week selector")
selected_date = st.sidebar.selectbox(
    "Select week", options=all_weeks, index=len(all_weeks) - 1,
    format_func=lambda d: d.strftime("%d %b %Y"),
)
selected_ts = pd.Timestamp(selected_date)

if FORECAST_JSON.exists():
    with open(FORECAST_JSON) as f:
        summary = json.load(f)
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Forecasting**")
    st.sidebar.markdown(f"Anomalies detected: **{summary['num_anomalies_detected']}**")
    st.sidebar.markdown(f"Current risk: **{summary['current_risk_level']}**")
    st.sidebar.markdown(f"Forecast horizon: **{summary['future_weeks_forecasted']} weeks**")

# ── Selected week data ────────────────────────────────────────────────────────
week_prod = prod[prod["week_start"] == selected_ts].iloc[0]
week_risk = risk[risk["week_start"] == selected_ts]
fleet     = fleet_summary(week_risk)

shortfall_pct   = float(week_prod["shortfall_pct"])
shortfall_score = max(0.0, min(1.0, shortfall_pct / 30.0))
is_anomaly = False
if forecast is not None:
    fw = forecast[forecast["ds"] == selected_ts]
    if not fw.empty and pd.notna(fw.iloc[0].get("risk_score_pct")):
        shortfall_score = float(fw.iloc[0]["risk_score_pct"]) / 100.0
    if not fw.empty and "is_anomaly" in fw.columns:
        is_anomaly = bool(fw.iloc[0]["is_anomaly"])

wx, rain_48, rain_7d, smi, dry_days = get_weather_alerts(selected_ts, rain_raw, sar_raw)
alerts_in = weather_to_alerts(wx)

# ── TOP METRICS ───────────────────────────────────────────────────────────────
st.subheader(f"Week of {selected_date.strftime('%d %b %Y')}")
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

def band_html(b):
    return f'<span class="band-{b.lower()}">{b.upper()}</span>'

c1.markdown(f"""<div class="metric-card">
<div style="font-size:.8rem;color:#666">Planned (t)</div>
<div style="font-size:1.5rem;font-weight:700">{int(week_prod['planned_tonnes']):,}</div>
</div>""", unsafe_allow_html=True)

c2.markdown(f"""<div class="metric-card">
<div style="font-size:.8rem;color:#666">Actual (t)</div>
<div style="font-size:1.5rem;font-weight:700">{int(week_prod['actual_tonnes']):,}</div>
</div>""", unsafe_allow_html=True)

sc = "#c0392b" if shortfall_pct > 10 else "#27ae60"
c3.markdown(f"""<div class="metric-card">
<div style="font-size:.8rem;color:#666">Shortfall %</div>
<div style="font-size:1.5rem;font-weight:700;color:{sc}">{shortfall_pct:+.1f}%</div>
</div>""", unsafe_allow_html=True)

c4.markdown(f"""<div class="metric-card">
<div style="font-size:.8rem;color:#666">Rainfall 48h (mm)</div>
<div style="font-size:1.5rem;font-weight:700">{rain_48}</div>
</div>""", unsafe_allow_html=True)

c5.markdown(f"""<div class="metric-card">
<div style="font-size:.8rem;color:#666">Soil Moisture</div>
<div style="font-size:1.5rem;font-weight:700">{smi:.2f}</div>
</div>""", unsafe_allow_html=True)

c6.markdown(f"""<div class="metric-card">
<div style="font-size:.8rem;color:#666">Fleet Downtime</div>
<div style="font-size:1.5rem">{band_html(fleet['downtime_risk'])}</div>
</div>""", unsafe_allow_html=True)

anomaly_html = '<span style="color:#c0392b;font-weight:700">⚠ YES</span>' if is_anomaly else '<span style="color:#27ae60">✓ Normal</span>'
c7.markdown(f"""<div class="metric-card">
<div style="font-size:.8rem;color:#666">Anomaly</div>
<div style="font-size:1.3rem">{anomaly_html}</div>
</div>""", unsafe_allow_html=True)

st.divider()

# ── ROW 1: Production + Satellite ────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📈 Production vs Plan")
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.fill_between(prod["week_start"], prod["actual_tonnes"], prod["planned_tonnes"],
                    where=prod["actual_tonnes"] < prod["planned_tonnes"],
                    alpha=0.25, color="#c0392b", label="Shortfall gap")
    ax.plot(prod["week_start"], prod["planned_tonnes"], "--", color="#7f8c8d", lw=1.2, label="Planned")
    ax.plot(prod["week_start"], prod["actual_tonnes"],  color="#2980b9", lw=1.5, label="Actual")
    ax.axvline(selected_ts, color="#e74c3c", lw=1.5, ls=":", label="Selected week")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    ax.set_ylabel("Tonnes"); ax.legend(fontsize=8)
    ax.set_xlim(prod["week_start"].min(), prod["week_start"].max())
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)

with col_right:
    st.subheader("🛰️ Satellite Signals (real data)")
    tab1, tab2, tab3, tab4 = st.tabs(["Rainfall", "NDVI", "Temp (LST)", "SAR (SMI)"])
    with tab1:
        fig, ax = plt.subplots(figsize=(5, 2.8))
        ax.bar(rain_raw["date"], rain_raw["rainfall_mm"], color="#3498db", width=1, alpha=0.7)
        ax.axvline(selected_ts, color="#e74c3c", lw=1.2, ls=":")
        ax.set_ylabel("mm/day"); fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    with tab2:
        fig, ax = plt.subplots(figsize=(5, 2.8))
        ax.plot(ndvi_raw["date"], ndvi_raw["ndvi"], color="#27ae60", lw=1.2)
        ax.axvline(selected_ts, color="#e74c3c", lw=1.2, ls=":")
        ax.set_ylabel("NDVI"); fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    with tab3:
        fig, ax = plt.subplots(figsize=(5, 2.8))
        ax.plot(lst_raw["date"], lst_raw["lst_c"], color="#e67e22", lw=1.2)
        ax.axvline(selected_ts, color="#e74c3c", lw=1.2, ls=":")
        ax.set_ylabel("°C"); fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    with tab4:
        fig, ax = plt.subplots(figsize=(5, 2.8))
        ax.plot(sar_raw["date"], sar_raw["sar_vv_db"], color="#8e44ad", lw=1.2)
        ax.axvline(selected_ts, color="#e74c3c", lw=1.2, ls=":")
        ax.set_ylabel("SAR VV (dB)"); fig.tight_layout(); st.pyplot(fig); plt.close(fig)

st.divider()

# ── ROW 2: Weather Alerts ─────────────────────────────────────────────────────
st.subheader("🌧️ Weather & Operational Alerts")
st.caption(f"Inputs — 48h rainfall: {rain_48} mm · 7d rainfall: {rain_7d} mm · "
           f"Soil moisture index: {smi:.3f} · Dry days: {dry_days}")

alert_labels = {
    "waterlogging":      ("💧 Waterlogging",        wx["waterlogging"]),
    "road_risk":         ("🛣️ Road Risk",            wx["road_risk"]),
    "haul_friction":     ("🚛 Haul Friction",        wx["haul_friction"]),
    "slope_instability": ("⛰️ Slope Instability",    wx["slope_instability"]),
    "dust_visibility":   ("🌫️ Dust / Visibility",    wx["dust_visibility"]),
}

wx_cols = st.columns(5)
for col, (key, (label, alert)) in zip(wx_cols, alert_labels.items()):
    level = alert.get("level", "NORMAL")
    css   = weather_css(level)
    icon  = weather_icon(level)
    msg   = alert.get("message", "")
    col.markdown(f"""<div class="{css}">
    <div style="font-size:.8rem;font-weight:700">{icon} {label}</div>
    <div style="font-size:.75rem;font-weight:700;margin:.2rem 0">{level}</div>
    <div style="font-size:.68rem;color:#555">{msg}</div>
    </div>""", unsafe_allow_html=True)

delay = wx.get("overall_delay_factor", 0)
delay_color = "#c0392b" if delay >= 0.18 else "#e67e22" if delay >= 0.1 else "#27ae60"
st.markdown(f"**Overall delay factor:** <span style='color:{delay_color};font-weight:700'>"
            f"{delay*100:.0f}%</span> estimated production loss this week from weather.",
            unsafe_allow_html=True)

st.divider()

# ── ROW 3: Forecasting ────────────────────────────────────────────────────────
if forecast is not None:
    st.subheader("🔮 Production Forecast (Prophet)")
    hist      = forecast[forecast["actual"].notna()].copy()
    future    = forecast[forecast["actual"].isna()].copy()
    anomalies = hist[hist["is_anomaly"] == True] if "is_anomaly" in hist.columns else pd.DataFrame()

    fig, ax = plt.subplots(figsize=(12, 3.5))
    ax.fill_between(forecast["ds"], forecast["yhat_lower"], forecast["yhat_upper"],
                    alpha=0.2, color="#1f77b4", label="90% confidence")
    ax.plot(forecast["ds"], forecast["yhat"],   color="#1f77b4", lw=1.5, label="Forecast")
    ax.plot(hist["ds"],     hist["actual"],      color="black",   lw=1.2, label="Actual")
    ax.plot(hist["ds"],     hist["target"],      color="#27ae60", ls="--", lw=1, label="Target")
    if not anomalies.empty:
        ax.scatter(anomalies["ds"], anomalies["actual"],
                   color="#c0392b", zorder=5, s=35, label=f"Anomalies ({len(anomalies)})")
    if not future.empty:
        ax.axvspan(future["ds"].min(), future["ds"].max(), alpha=0.05, color="#e67e22")
    ax.axvline(selected_ts, color="#e74c3c", lw=1.5, ls=":", label="Selected week")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    ax.set_ylabel("Tonnes"); ax.legend(fontsize=8, ncol=4)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)

    risk_hist = forecast[forecast["risk_score_pct"].notna()]
    if not risk_hist.empty:
        fig, ax = plt.subplots(figsize=(12, 2))
        ax.fill_between(risk_hist["ds"], risk_hist["risk_score_pct"], alpha=0.4, color="#e74c3c")
        ax.plot(risk_hist["ds"], risk_hist["risk_score_pct"], color="#c0392b", lw=1.2)
        ax.axhline(75, color="#c0392b", ls="--", lw=0.8, label="Critical (75)")
        ax.axhline(50, color="#e67e22", ls="--", lw=0.8, label="High (50)")
        ax.axhline(20, color="#27ae60", ls="--", lw=0.8, label="Low (20)")
        ax.axvline(selected_ts, color="#7f8c8d", lw=1.2, ls=":")
        ax.set_ylabel("Shortfall risk %"); ax.set_ylim(0, 100)
        ax.legend(fontsize=7, ncol=3); fig.tight_layout()
        st.pyplot(fig); plt.close(fig)

    st.divider()
# ---- ROW 3b: Reserve Mapping + Explainability (Member 2) ----
st.subheader("Reserve Mapping - Prospectivity")
rm = load_reserve_outputs()
if rm is None:
    st.info("Reserve mapping outputs not found. Run  python run_pipeline.py  "
            "inside the reserve_mapping folder first.")
else:
    if rm["is_demo"]:
        st.warning("DEMO / SYNTHETIC DATA - software test only. Scores are a prospectivity "
                   "indicator, not a reserve estimate or real manganese findings.")
    map_col, tbl_col = st.columns([3, 2])
    with map_col:
        components.html(rm["map_html"], height=560)
    with tbl_col:
        st.markdown("**Top 10 Exploration Targets**")
        st.dataframe(rm["targets"].head(10), use_container_width=True, hide_index=True)

    st.subheader("Explainability - Why these scores?")
    fi = rm["fi"].sort_values("importance")
    ex_l, ex_r = st.columns([3, 2])
    with ex_l:
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.barh(fi["feature"], fi["importance"], color="#1f4e79")
        ax.set_xlabel("Model importance")
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    with ex_r:
        top = fi.iloc[-1]
        st.markdown(f"**Top driver:** `{top['feature']}` "
                    f"({top['importance']*100:.0f}% of total importance)")
        st.caption("Longer bars mean the feature influenced the prospectivity score more. "
                   + ("In demo mode these come from synthetic data." if rm["is_demo"] else ""))

st.divider()
# ── ROW 4: Equipment Health ───────────────────────────────────────────────────
st.subheader("🔧 Equipment Health — Selected Week")
eq_sorted = week_risk.sort_values("risk_score", ascending=False)
cols = st.columns(len(eq_sorted))
for col, (_, row) in zip(cols, eq_sorted.iterrows()):
    b     = row["risk_band"]
    color = {"high": "#c0392b", "medium": "#e67e22", "low": "#27ae60"}[b]
    col.markdown(f"""<div style="background:white;border-radius:10px;padding:.7rem;
        border-top:4px solid {color};box-shadow:0 1px 4px rgba(0,0,0,.08);text-align:center">
        <div style="font-size:.75rem;color:#666">{row['equipment_id']}</div>
        <div style="font-size:.7rem;color:#999">{row['equipment_type']} · {row['age_years']}yr</div>
        <div style="font-size:1.3rem;font-weight:700;color:{color}">{row['risk_score']:.2f}</div>
        <div style="font-size:.65rem;color:{color}">{b.upper()}</div>
        <div style="font-size:.6rem;color:#aaa;margin-top:.2rem">{row['main_driver']}</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── ROW 5: Equipment risk trend ───────────────────────────────────────────────
st.subheader("📊 Equipment Risk Trend")
machines          = sorted(risk["equipment_id"].unique())
selected_machines = st.multiselect("Show machines", machines, default=machines[:4])
if selected_machines:
    fig, ax = plt.subplots(figsize=(10, 3))
    for m in selected_machines:
        d = risk[risk["equipment_id"] == m]
        ax.plot(d["week_start"], d["risk_score"], lw=1.3, label=m)
    ax.axhline(0.78, color="#c0392b", ls="--", lw=0.8, label="High threshold")
    ax.axhline(0.60, color="#e67e22", ls="--", lw=0.8, label="Medium threshold")
    ax.axvline(selected_ts, color="#7f8c8d", lw=1, ls=":")
    ax.set_ylabel("Risk score (0–1)"); ax.set_ylim(0, 1)
    ax.legend(fontsize=7, ncol=5); fig.tight_layout()
    st.pyplot(fig); plt.close(fig)

st.divider()

# ── ROW 6: Prescriptive Engine ────────────────────────────────────────────────
st.subheader("💡 Prescriptive Recommendations")
st.caption(f"Inputs — shortfall risk: {shortfall_score:.2f} · fleet downtime: {fleet['downtime_risk']} · "
           f"blast delays: {int(week_prod['blast_delay_days'])}d · "
           f"weather alerts: {len(alerts_in)} active · anomaly: {is_anomaly}")

cards = recommend(
    shortfall_risk   = shortfall_score,
    alerts           = alerts_in,
    downtime_risk    = fleet["downtime_risk"],
    blast_delay_days = int(week_prod["blast_delay_days"]),
    worst_equipment  = fleet["worst_equipment"],
    is_anomaly       = is_anomaly,
)

for card in cards:
    css = f"card-{card['priority'].lower()}"
    st.markdown(f"""<div class="{css}">
    <strong>[{card['priority']}] {card['title']}</strong><br>
    <span style="font-size:.9rem">🎯 {card['action']}</span><br>
    <span style="font-size:.8rem;color:#555">📌 {card['reason']}</span>
    </div>""", unsafe_allow_html=True)

st.divider()
# ---- ROW 6b: What-if Simulator ----
st.subheader("What-if Simulator")
st.caption("Change the inputs - weather alerts and recommendations re-run instantly. "
           "Sliders start from the selected week's values.")

k = str(selected_date)   # resets the sliders when the week changes
w1, w2 = st.columns(2)
with w1:
    sim_rain48 = st.slider("Rainfall, last 48h (mm)", 0.0, 150.0, float(min(rain_48, 150.0)), 1.0, key=f"wi_r48_{k}")
    sim_rain7  = st.slider("Rainfall, last 7 days (mm)", 0.0, 400.0, float(min(rain_7d, 400.0)), 1.0, key=f"wi_r7_{k}")
    sim_smi    = st.slider("Soil moisture index", 0.0, 1.0, float(min(max(smi, 0.0), 1.0)), 0.01, key=f"wi_smi_{k}")
    sim_dry    = st.slider("Consecutive dry days", 0, 30, int(min(dry_days, 30)), key=f"wi_dry_{k}")
with w2:
    bands = ["low", "medium", "high"]
    cur = str(fleet["downtime_risk"]).lower()
    sim_down  = st.selectbox("Fleet downtime risk", bands, index=bands.index(cur) if cur in bands else 0, key=f"wi_down_{k}")
    sim_blast = st.slider("Blast delay (days)", 0, 5, int(min(week_prod["blast_delay_days"], 5)), key=f"wi_blast_{k}")
    sim_short = st.slider("Shortfall risk", 0.0, 1.0, float(min(max(shortfall_score, 0.0), 1.0)), 0.01, key=f"wi_short_{k}")

sim_wx = evaluate_weather_impact(
    rainfall_48h_mm=sim_rain48, soil_moisture_index=sim_smi,
    rainfall_7d_mm=sim_rain7, consecutive_dry_days=int(sim_dry),
)
sim_alerts = weather_to_alerts(sim_wx)
sim_cards = recommend(
    shortfall_risk=sim_short, alerts=sim_alerts, downtime_risk=sim_down,
    blast_delay_days=int(sim_blast), worst_equipment=fleet["worst_equipment"],
    is_anomaly=is_anomaly,
)

sim_delay = sim_wx.get("overall_delay_factor", 0)
m1, m2, m3 = st.columns(3)
m1.metric("Weather delay factor", f"{sim_delay*100:.0f}%",
          delta=f"{(sim_delay - delay)*100:+.0f} pts vs actual week", delta_color="inverse")
m2.metric("Active weather alerts", len(sim_alerts),
          delta=len(sim_alerts) - len(alerts_in), delta_color="inverse")
m3.metric("Recommendations", len(sim_cards))

chip_cols = st.columns(5)
for col, (key, (label, _)) in zip(chip_cols, alert_labels.items()):
    lvl = sim_wx[key].get("level", "NORMAL")
    col.markdown(f"""<div class="{weather_css(lvl)}">
    <div style="font-size:.8rem;font-weight:700">{label}</div>
    <div style="font-size:.75rem;font-weight:700">{lvl}</div>
    </div>""", unsafe_allow_html=True)

for card in sim_cards:
    css = f"card-{card['priority'].lower()}"
    st.markdown(f"""<div class="{css}">
    <strong>[{card['priority']}] {card['title']}</strong><br>
    <span style="font-size:.9rem">{card['action']}</span><br>
    <span style="font-size:.8rem;color:#555">{card['reason']}</span>
    </div>""", unsafe_allow_html=True)

st.divider()
# ── ROW 7: Raw data tables ────────────────────────────────────────────────────
with st.expander("📋 Raw — Production (this week)"):
    st.dataframe(week_prod.to_frame().T, use_container_width=True)

with st.expander("📋 Raw — Equipment scores (this week)"):
    st.dataframe(
        eq_sorted[["equipment_id","equipment_type","age_years",
                   "downtime_pct_8w","breakdowns_8w","risk_score","risk_band","main_driver"]],
        use_container_width=True,
    )

with st.expander("📋 Raw — Weather outputs (this week)"):
    wx_flat = {}
    for k, v in wx.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                wx_flat[f"{k}.{k2}"] = v2
        else:
            wx_flat[k] = v
    st.dataframe(pd.DataFrame([wx_flat]), use_container_width=True)

if forecast is not None:
    with st.expander("📋 Raw — Forecast (all weeks)"):
        cols_show = [c for c in ["ds","yhat","yhat_lower","yhat_upper","actual","target",
                                  "risk_score_pct","risk_level","is_anomaly"] if c in forecast.columns]
        st.dataframe(forecast[cols_show], use_container_width=True)

st.caption("Sentinel-2 NDVI · Sentinel-1 SAR · MODIS LST · CHIRPS rainfall via Google Earth Engine · "
           "Synthetic production ~1.1M t/yr · Prophet forecasting · Weather risk engine · SIH 26009")
