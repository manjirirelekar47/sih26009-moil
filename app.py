"""
SIH 26009 — OreSentinel Mining Intelligence Dashboard
MOIL Limited · Ministry of Steel · Govt. of India
Run from repo root:  streamlit run app.py
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="OreSentinel — SIH 26009",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

import charts
import services
import ui
from src.equipment_health.health import fleet_summary
from src.prescriptive.engine import recommend
from weather_predictor import evaluate_weather_impact

ui.inject_css()

WEATHER_TILES = [
    ("waterlogging",      "💧 Waterlogging"),
    ("road_risk",         "🛣️ Road Risk"),
    ("haul_friction",     "🚛 Haul Friction"),
    ("slope_instability", "⛰️ Slope Stability"),
    ("dust_visibility",   "🌫️ Dust / Visibility"),
]


def show(fig, key: str) -> None:
    st.plotly_chart(fig, key=key, use_container_width=True, config=charts.CONFIG)


def render_cards(cards) -> None:
    if not cards:
        st.info("No corrective actions needed for these inputs.")
        return
    for card in cards:
        ui.action_card(
            level=card.get("priority", ""),
            title=f"[{card.get('priority','')}] {card.get('title','')}",
            detail=card.get("reason", ""),
            action=card.get("action", ""),
        )


@st.fragment
def equipment_trend_section(risk, selected_ts):
    machines = sorted(risk["equipment_id"].unique())
    chosen = st.multiselect("Show machines", machines, default=machines[:4])
    if chosen:
        show(charts.equipment_trend(risk, chosen, selected_ts), key="eq_trend")


@st.fragment
def whatif_section(selected_date, rain_48, rain_7d, smi, dry_days,
                   fleet, blast_days, shortfall_score, is_anomaly,
                   baseline_delay, baseline_alerts):
    st.caption("Adjust inputs below — weather alerts and recommendations update instantly.")
    k = str(selected_date)
    w1, w2 = st.columns(2, gap="large")
    with w1:
        st.markdown("**🌧️ Weather inputs**")
        sim_rain48 = st.slider("Rainfall, last 48h (mm)", 0.0, 150.0, float(min(rain_48, 150.0)), 1.0, key=f"wi_r48_{k}")
        sim_rain7  = st.slider("Rainfall, last 7 days (mm)", 0.0, 400.0, float(min(rain_7d, 400.0)), 1.0, key=f"wi_r7_{k}")
        sim_smi    = st.slider("Soil moisture index", 0.0, 1.0, float(min(max(smi, 0.0), 1.0)), 0.01, key=f"wi_smi_{k}")
        sim_dry    = st.slider("Consecutive dry days", 0, 30, int(min(dry_days, 30)), key=f"wi_dry_{k}")
    with w2:
        st.markdown("**⚙️ Operational inputs**")
        bands   = ["low", "medium", "high"]
        cur     = str(fleet["downtime_risk"]).lower()
        sim_down  = st.selectbox("Fleet downtime risk", bands, index=bands.index(cur) if cur in bands else 0, key=f"wi_down_{k}")
        sim_blast = st.slider("Blast delay (days)", 0, 5, int(min(blast_days, 5)), key=f"wi_blast_{k}")
        sim_short = st.slider("Shortfall risk (0–1)", 0.0, 1.0, float(min(max(shortfall_score, 0.0), 1.0)), 0.01, key=f"wi_short_{k}")

    sim_wx     = evaluate_weather_impact(rainfall_48h_mm=sim_rain48, soil_moisture_index=sim_smi,
                                         rainfall_7d_mm=sim_rain7, consecutive_dry_days=int(sim_dry))
    sim_alerts = services.weather_to_alerts(sim_wx)
    sim_cards  = recommend(shortfall_risk=sim_short, alerts=sim_alerts, downtime_risk=sim_down,
                           blast_delay_days=int(sim_blast), worst_equipment=fleet["worst_equipment"],
                           is_anomaly=is_anomaly)
    sim_delay  = sim_wx.get("overall_delay_factor", 0)

    st.markdown("---")
    ui.section("Simulated Outputs")
    m1, m2, m3 = st.columns(3)
    m1.metric("Weather delay factor", f"{sim_delay*100:.0f}%",
              delta=f"{(sim_delay - baseline_delay)*100:+.0f} pts vs actual",
              delta_color="inverse", border=True)
    m2.metric("Active weather alerts", len(sim_alerts),
              delta=len(sim_alerts) - baseline_alerts, delta_color="inverse", border=True)
    m3.metric("Recommendations fired", len(sim_cards), border=True)

    ui.section("Simulated Weather Alerts")
    chip_cols = st.columns(len(WEATHER_TILES))
    for col, (key, label) in zip(chip_cols, WEATHER_TILES):
        lvl = sim_wx.get(key, {}).get("level", "NORMAL")
        msg = sim_wx.get(key, {}).get("message", "")
        with col:
            ui.status_card(ui.level_kind(lvl), label, str(lvl).replace("_"," ").title(), msg)

    ui.section("Simulated Recommendations")
    render_cards(sim_cards)


# ── Load data ──────────────────────────────────────────────────────────────────
try:
    data = services.load_data()
except FileNotFoundError as e:
    st.error(f"Missing data file: {e}\nRun the data pipeline first.")
    st.stop()

prod       = data["prod"]
risk       = data["risk"]
forecast   = data["forecast"]
rain_raw   = data["rain"]
ndvi_raw   = data["ndvi"]
lst_raw    = data["lst"]
sar_raw    = data["sar"]
rm         = services.load_reserve_outputs()
summary    = services.load_forecast_summary()
all_weeks  = sorted(prod["week_start"].dt.date.unique())

# ── SIDEBAR — OreSentinel dark style ──────────────────────────────────────────
with st.sidebar:
    ui.sidebar_logo()
    st.markdown("---")

    st.markdown('<p style="font-size:.68rem;text-transform:uppercase;letter-spacing:.10em;color:rgba(255,255,255,.38);font-weight:600;padding-left:2px">Week Selector</p>', unsafe_allow_html=True)
    selected_date = st.selectbox(
        "Week", options=all_weeks, index=len(all_weeks) - 1,
        format_func=lambda d: d.strftime("%d %b %Y"),
        label_visibility="collapsed",
    )

    if summary:
        st.markdown("---")
        st.markdown('<p style="font-size:.68rem;text-transform:uppercase;letter-spacing:.10em;color:rgba(255,255,255,.38);font-weight:600;padding-left:2px">Forecast Summary</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:.82rem;margin:.1rem 0">Anomalies: <strong style="color:white">{summary.get("num_anomalies_detected","n/a")}</strong></p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:.82rem;margin:.1rem 0">Risk level: <strong style="color:#3C9A8E">{summary.get("current_risk_level","n/a")}</strong></p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:.82rem;margin:.1rem 0">Horizon: <strong style="color:white">{summary.get("future_weeks_forecasted","n/a")} weeks</strong></p>', unsafe_allow_html=True)

    st.markdown("---")
    ui.ministry_card()

selected_ts = pd.Timestamp(selected_date)

# ── Selected week calculations (unchanged backend logic) ──────────────────────
week_prod      = prod[prod["week_start"] == selected_ts].iloc[0]
week_risk      = risk[risk["week_start"] == selected_ts]
fleet          = fleet_summary(week_risk)
shortfall_pct  = float(week_prod["shortfall_pct"])
shortfall_score = max(0.0, min(1.0, shortfall_pct / 30.0))
is_anomaly = False
if forecast is not None:
    fw = forecast[forecast["ds"] == selected_ts]
    if not fw.empty and pd.notna(fw.iloc[0].get("risk_score_pct")):
        shortfall_score = float(fw.iloc[0]["risk_score_pct"]) / 100.0
    if not fw.empty and "is_anomaly" in fw.columns:
        is_anomaly = bool(fw.iloc[0]["is_anomaly"])

wxr        = services.get_weather_alerts(selected_ts, rain_raw, sar_raw)
wx         = wxr["wx"]
rain_48    = wxr["rain_48"]
rain_7d    = wxr["rain_7d"]
smi        = wxr["smi"]
dry_days   = wxr["dry_days"]
alerts_in  = services.weather_to_alerts(wx)
delay      = wx.get("overall_delay_factor", 0)
blast_days = int(week_prod["blast_delay_days"])
n_alerts   = len(alerts_in)

cards = recommend(
    shortfall_risk=shortfall_score, alerts=alerts_in,
    downtime_risk=fleet["downtime_risk"], blast_delay_days=blast_days,
    worst_equipment=fleet["worst_equipment"], is_anomaly=is_anomaly,
)

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
risk_kind = "risk" if shortfall_score > 0.6 else "watch" if shortfall_score > 0.3 else "ok"
anom_kind = "watch" if is_anomaly else "ok"
pills = [
    (f"Week of {selected_date.strftime('%d %b %Y')}", "neutral"),
    (f"Shortfall risk: {shortfall_score*100:.0f}%", risk_kind),
    (f"Fleet: {fleet['downtime_risk'].title()}", ui.level_kind(fleet["downtime_risk"])),
    (f"{n_alerts} weather alert(s)", "watch" if n_alerts else "ok"),
    ("⚠ Anomaly" if is_anomaly else "✓ Normal", anom_kind),
]
ui.page_header(
    "Welcome back, Analyst! 👋",
    "AI-powered insights for a more productive and sustainable tomorrow.",
    pills=pills,
)

# ── KPI ROW ───────────────────────────────────────────────────────────────────
planned = int(week_prod["planned_tonnes"])
actual  = int(week_prod["actual_tonnes"])
ui.kpi_row([
    {"label": "Planned Output",       "value": f"{planned:,} t"},
    {"label": "Actual Output",        "value": f"{actual:,} t",
     "delta": f"{actual - planned:+,} t vs plan"},
    {"label": "Shortfall Risk",       "value": f"{shortfall_score*100:.0f}%",
     "help": "Forecast risk score; falls back to shortfall % if no forecast."},
    {"label": "Weather Delay",        "value": f"{delay*100:.0f}%",
     "help": "Estimated production loss from weather this week."},
    {"label": "Fleet Downtime Risk",  "value": str(fleet["downtime_risk"]).title(),
     "delta": f"Worst: {fleet['worst_equipment']}", "delta_color": "off"},
    {"label": "Anomaly",              "value": "⚠ Yes" if is_anomaly else "✓ None"},
])

st.write("")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_over, tab_res, tab_fc, tab_wx, tab_eq, tab_sim, tab_data = st.tabs([
    "🏠 Overview",
    "🗺️ Reserves",
    "📈 Forecast",
    "🌧️ Weather",
    "🔧 Equipment",
    "🔬 What-if",
    "📋 Data",
])

# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab_over:
    top_l, top_r = st.columns([3, 2], gap="large")

    with top_l:
        ui.section("Production vs Plan")
        with st.container(border=True):
            show(charts.production_vs_plan(prod, selected_ts, height=380), key="ov_prod")

    with top_r:
        ui.section("Recommended Actions")
        with st.container(height=440, border=True):
            render_cards(cards)
        st.caption(f"Inputs → shortfall risk {shortfall_score:.2f} · fleet {fleet['downtime_risk']} · "
                   f"blast {blast_days}d · {n_alerts} alert(s) · anomaly: {is_anomaly}")

    bot_l, bot_r = st.columns([3, 2], gap="large")

    with bot_l:
        ui.section("Reserve Prospectivity Map")
        if rm is None:
            st.info("Reserve mapping outputs not found. Run `python run_pipeline.py` inside `reserve_mapping/`.")
        else:
            if rm["is_demo"]:
                st.warning("Demo / synthetic data. Scores are an exploration indicator, not a reserve estimate.")
            with st.container(border=True):
                components.html(rm["map_html"], height=430)

    with bot_r:
        ui.section("Weather & Operational Alerts")
        for key, label in WEATHER_TILES:
            alert = wx.get(key, {})
            level = alert.get("level", "NORMAL")
            ui.status_card(ui.level_kind(level), label, str(level).replace("_"," ").title(),
                           alert.get("message", ""))

# ═══════════════════════════════════════════════════════════════════════════════
# RESERVES & EXPLAINABILITY
# ═══════════════════════════════════════════════════════════════════════════════
with tab_res:
    if rm is None:
        st.info("Reserve mapping outputs not found. Run the pipeline inside `reserve_mapping/`.")
    else:
        if rm["is_demo"]:
            st.warning("DEMO / SYNTHETIC DATA: software test only. Not real manganese findings.")

        r_l, r_r = st.columns([3, 2], gap="large")
        with r_l:
            ui.section("Explainability — Why These Scores?")
            fi = rm["fi"].sort_values("importance")
            with st.container(border=True):
                show(charts.importance_bar(fi), key="rm_fi")

        with r_r:
            top = fi.iloc[-1]
            st.metric("Top Driver", str(top["feature"]),
                      f"{top['importance']*100:.0f}% of total importance",
                      delta_color="off", border=True)
            st.caption("Longer bars = more influence on the prospectivity score."
                       + (" (Demo mode — synthetic features.)" if rm["is_demo"] else ""))
            ui.section("Top 10 Exploration Targets")
            st.dataframe(rm["targets"].head(10), use_container_width=True, hide_index=True)

        ui.section("Interactive Prospectivity Map")
        with st.container(border=True):
            components.html(rm["map_html"], height=520)

# ═══════════════════════════════════════════════════════════════════════════════
# FORECAST
# ═══════════════════════════════════════════════════════════════════════════════
with tab_fc:
    if forecast is None:
        st.info("Forecast output not found. Run the forecasting pipeline first.")
    else:
        if summary:
            ui.kpi_row([
                {"label": "Anomalies Detected",  "value": str(summary.get("num_anomalies_detected","n/a"))},
                {"label": "Current Risk Level",  "value": str(summary.get("current_risk_level","n/a"))},
                {"label": "Forecast Horizon",    "value": f"{summary.get('future_weeks_forecasted','n/a')} weeks"},
            ])

        ui.section("Production Forecast vs Actual")
        with st.container(border=True):
            show(charts.forecast_chart(forecast, selected_ts, height=400), key="fc_main")

        risk_fig = charts.risk_chart(forecast, selected_ts)
        if risk_fig is not None:
            ui.section("Shortfall Risk Score Over Time")
            with st.container(border=True):
                show(risk_fig, key="fc_risk")

# ═══════════════════════════════════════════════════════════════════════════════
# WEATHER & SATELLITE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_wx:
    ui.kpi_row([
        {"label": "Rainfall, 48h",        "value": f"{rain_48} mm"},
        {"label": "Rainfall, 7 days",     "value": f"{rain_7d} mm"},
        {"label": "Soil Moisture Index",  "value": f"{smi:.3f}"},
        {"label": "Consecutive Dry Days", "value": str(dry_days)},
    ])

    ui.section("Operational Weather Alerts")
    wx_cols = st.columns(len(WEATHER_TILES))
    for col, (key, label) in zip(wx_cols, WEATHER_TILES):
        alert = wx.get(key, {})
        level = alert.get("level", "NORMAL")
        with col:
            ui.status_card(ui.level_kind(level), label,
                           str(level).replace("_"," ").title(), alert.get("message",""))

    delay_color = "#C0392B" if delay >= 0.18 else "#B7791F" if delay >= 0.1 else "#1E8E5A"
    st.markdown(f'<p style="font-size:.88rem;margin:.6rem 0">Overall delay factor: '
                f'<strong style="color:{delay_color}">{delay*100:.0f}%</strong> '
                f'estimated production loss from weather.</p>', unsafe_allow_html=True)

    ui.section("Satellite Signals (Real Earth Engine Data)")
    s1, s2 = st.columns(2, gap="large")
    with s1:
        with st.container(border=True):
            st.markdown("**🌧️ Rainfall (CHIRPS daily)**")
            show(charts.satellite_series(rain_raw, "rainfall_mm", "mm/day", "#4C6EF5",
                                         selected_ts, kind="bar"), key="sat_rain")
        with st.container(border=True):
            st.markdown("**🌡️ Land Surface Temperature (MODIS)**")
            show(charts.satellite_series(lst_raw, "lst_c", "°C", ui.PALETTE["watch"],
                                         selected_ts), key="sat_lst")
    with s2:
        with st.container(border=True):
            st.markdown("**🌿 Vegetation — NDVI (Sentinel-2)**")
            show(charts.satellite_series(ndvi_raw, "ndvi", "NDVI", ui.PALETTE["ok"],
                                         selected_ts), key="sat_ndvi")
        with st.container(border=True):
            st.markdown("**📡 Soil Moisture Proxy — SAR VV (Sentinel-1)**")
            show(charts.satellite_series(sar_raw, "sar_vv_db", "VV dB", ui.PALETTE["violet"],
                                         selected_ts), key="sat_sar")

# ═══════════════════════════════════════════════════════════════════════════════
# EQUIPMENT HEALTH
# ═══════════════════════════════════════════════════════════════════════════════
with tab_eq:
    fleet_avg = float(week_risk["risk_score"].mean()) if not week_risk.empty else 0.0
    ui.kpi_row([
        {"label": "Fleet Risk Band",    "value": str(fleet["downtime_risk"]).title()},
        {"label": "Worst Machine",      "value": fleet["worst_equipment"]},
        {"label": "Avg Risk Score",     "value": f"{fleet_avg:.2f}"},
        {"label": "High Risk Machines", "value": str(fleet.get("n_high", 0))},
        {"label": "Medium Risk",        "value": str(fleet.get("n_medium", 0))},
    ])

    ui.section("Equipment Health — Selected Week")
    eq_sorted = week_risk.sort_values("risk_score", ascending=False)
    if eq_sorted.empty:
        st.info("No equipment records for this week.")
    for start in range(0, len(eq_sorted), 5):
        cols = st.columns(5)
        for col, (_, row) in zip(cols, eq_sorted.iloc[start:start+5].iterrows()):
            with col:
                ui.equipment_tile(row["equipment_id"], row["equipment_type"], row["age_years"],
                                  row["risk_score"], row["risk_band"], row["main_driver"])

    ui.section("Equipment Risk Trend")
    equipment_trend_section(risk, selected_ts)

# ═══════════════════════════════════════════════════════════════════════════════
# WHAT-IF SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════
with tab_sim:
    whatif_section(selected_date, rain_48, rain_7d, smi, dry_days,
                   fleet, blast_days, shortfall_score, is_anomaly, delay, n_alerts)

# ═══════════════════════════════════════════════════════════════════════════════
# RAW DATA
# ═══════════════════════════════════════════════════════════════════════════════
with tab_data:
    with st.expander("📦 Production — this week"):
        st.dataframe(week_prod.to_frame().T, use_container_width=True)
    with st.expander("🔧 Equipment scores — this week"):
        st.dataframe(
            eq_sorted[["equipment_id","equipment_type","age_years","downtime_pct_8w",
                        "breakdowns_8w","risk_score","risk_band","main_driver"]],
            use_container_width=True,
        )
    with st.expander("🌧️ Weather outputs — this week"):
        wx_flat = {}
        for key, val in wx.items():
            if isinstance(val, dict):
                for k2, v2 in val.items():
                    wx_flat[f"{key}.{k2}"] = v2
            else:
                wx_flat[key] = val
        st.dataframe(pd.DataFrame([wx_flat]), use_container_width=True)
    if forecast is not None:
        with st.expander("📈 Forecast — all weeks"):
            cols_show = [c for c in ["ds","yhat","yhat_lower","yhat_upper","actual","target",
                                     "risk_score_pct","risk_level","is_anomaly"]
                         if c in forecast.columns]
            st.dataframe(forecast[cols_show], use_container_width=True)
    if rm is not None:
        with st.expander("🗺️ Top exploration targets"):
            st.dataframe(rm["targets"], use_container_width=True)
        with st.expander("🔬 Feature importances"):
            st.dataframe(rm["fi"], use_container_width=True)

st.caption("Sentinel-2 NDVI · Sentinel-1 SAR · MODIS LST · CHIRPS rainfall via Google Earth Engine · "
           "Synthetic production ~1.1M t/yr · Prophet forecasting · Weather risk engine · SIH 26009 · MOIL Limited")
