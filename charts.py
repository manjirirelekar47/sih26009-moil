"""charts.py: Plotly figure builders for the dashboard.

Each function takes plain DataFrames and returns a styled go.Figure (or None when
there is nothing to draw). No Streamlit calls in here, so they are easy to test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

import ui

P = ui.PALETTE

# Passed to st.plotly_chart(config=...): hide the floating toolbar
CONFIG = {"displayModeBar": False}


def _dt(ts):
    """Timestamp -> plain datetime, which Plotly shapes and annotations accept everywhere."""
    return pd.Timestamp(ts).to_pydatetime()


def _mark_week(fig, selected_ts, label: bool = True) -> None:
    """Dotted vertical line at the selected week."""
    x = _dt(selected_ts)
    fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, xref="x", yref="paper",
                  line=dict(color=P["risk"], width=1.5, dash="dot"))
    if label:
        fig.add_annotation(x=x, y=1, xref="x", yref="paper", text="Selected week",
                           showarrow=False, yanchor="bottom", font=dict(size=11, color=P["risk"]))


def production_vs_plan(prod: pd.DataFrame, selected_ts, height: int = 360):
    x = prod["week_start"]
    planned, actual = prod["planned_tonnes"], prod["actual_tonnes"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=planned, name="Planned", mode="lines",
                             line=dict(color=P["muted"], width=1.5, dash="dash"),
                             hovertemplate="%{y:,.0f} t"))
    # Fills only where actual < planned, because the lower edge is min(actual, planned)
    fig.add_trace(go.Scatter(x=x, y=np.minimum(actual, planned), name="Shortfall gap", mode="lines",
                             line=dict(width=0), fill="tonexty", fillcolor="rgba(192,57,43,0.25)",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=actual, name="Actual", mode="lines",
                             line=dict(color=P["violet"], width=2), hovertemplate="%{y:,.0f} t"))
    _mark_week(fig, selected_ts)
    fig.update_yaxes(title_text="Tonnes per week", tickformat=",")
    return ui.style_fig(fig, height)


def satellite_series(df: pd.DataFrame, y: str, ylabel: str, color: str, selected_ts,
                     kind: str = "line", height: int = 260):
    """Rainfall / NDVI / LST / SAR series with the selected week marked."""
    fig = go.Figure()
    if kind == "bar":
        fig.add_trace(go.Bar(x=df["date"], y=df[y], marker_color=color, opacity=0.8, name=ylabel))
    else:
        fig.add_trace(go.Scatter(x=df["date"], y=df[y], mode="lines",
                                 line=dict(color=color, width=1.6), name=ylabel))
    _mark_week(fig, selected_ts, label=False)
    fig.update_yaxes(title_text=ylabel)
    fig.update_layout(showlegend=False)
    return ui.style_fig(fig, height)


def forecast_chart(forecast: pd.DataFrame, selected_ts, height: int = 400):
    hist = forecast[forecast["actual"].notna()]
    future = forecast[forecast["actual"].isna()]

    fig = go.Figure()
    # Confidence band: invisible upper edge, then the lower edge filled up to it
    fig.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat_upper"], mode="lines",
                             line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat_lower"], mode="lines",
                             line=dict(width=0), fill="tonexty", fillcolor="rgba(90,62,155,0.15)",
                             name="90% confidence", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat"], mode="lines", name="Forecast",
                             line=dict(color=P["violet"], width=2), hovertemplate="%{y:,.0f} t"))
    fig.add_trace(go.Scatter(x=hist["ds"], y=hist["actual"], mode="lines", name="Actual",
                             line=dict(color=P["ink"], width=1.4), hovertemplate="%{y:,.0f} t"))
    if "target" in hist.columns:
        fig.add_trace(go.Scatter(x=hist["ds"], y=hist["target"], mode="lines", name="Target",
                                 line=dict(color=P["ok"], width=1.2, dash="dash"),
                                 hovertemplate="%{y:,.0f} t"))
    if "is_anomaly" in hist.columns:
        anomalies = hist[hist["is_anomaly"] == True]  # noqa: E712  (column may hold bools or objects)
        if not anomalies.empty:
            fig.add_trace(go.Scatter(x=anomalies["ds"], y=anomalies["actual"], mode="markers",
                                     name=f"Anomalies ({len(anomalies)})",
                                     marker=dict(color=P["risk"], size=9, line=dict(color="white", width=1)),
                                     hovertemplate="%{y:,.0f} t"))
    if not future.empty:
        fig.add_shape(type="rect", x0=_dt(future["ds"].min()), x1=_dt(future["ds"].max()),
                      xref="x", y0=0, y1=1, yref="paper", layer="below", line_width=0,
                      fillcolor="rgba(183,121,31,0.08)")
    _mark_week(fig, selected_ts)
    fig.update_yaxes(title_text="Tonnes per week", tickformat=",")
    return ui.style_fig(fig, height)


def risk_chart(forecast: pd.DataFrame, selected_ts, height: int = 260):
    """Shortfall risk score over time, with the Low / High / Critical thresholds."""
    if "risk_score_pct" not in forecast.columns:
        return None
    r = forecast[forecast["risk_score_pct"].notna()]
    if r.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=r["ds"], y=r["risk_score_pct"], mode="lines", name="Shortfall risk",
                             line=dict(color=P["risk"], width=1.6), fill="tozeroy",
                             fillcolor="rgba(192,57,43,0.18)", hovertemplate="%{y:.0f}%"))
    for y, label, color in [(75, "Critical", P["risk"]), (50, "High", P["watch"]), (20, "Low", P["ok"])]:
        fig.add_hline(y=y, line=dict(color=color, width=1, dash="dash"),
                      annotation_text=f"{label} ({y})", annotation_position="top left")
    _mark_week(fig, selected_ts, label=False)
    fig.update_yaxes(title_text="Shortfall risk %", range=[0, 100])
    fig.update_layout(showlegend=False)
    return ui.style_fig(fig, height)


def equipment_trend(risk: pd.DataFrame, machines, selected_ts, height: int = 340):
    fig = go.Figure()
    for m in machines:
        d = risk[risk["equipment_id"] == m]
        fig.add_trace(go.Scatter(x=d["week_start"], y=d["risk_score"], mode="lines", name=str(m),
                                 line=dict(width=1.6), hovertemplate="%{y:.2f}"))
    fig.add_hline(y=0.78, line=dict(color=P["risk"], width=1, dash="dash"),
                  annotation_text="High threshold", annotation_position="top left")
    fig.add_hline(y=0.60, line=dict(color=P["watch"], width=1, dash="dash"),
                  annotation_text="Medium threshold", annotation_position="top left")
    _mark_week(fig, selected_ts, label=False)
    fig.update_yaxes(title_text="Risk score (0 to 1)", range=[0, 1])
    return ui.style_fig(fig, height)


def importance_bar(fi: pd.DataFrame, height: int = 320):
    """Reserve-model feature importances, largest at the top."""
    fi = fi.sort_values("importance")
    fig = go.Figure(go.Bar(x=fi["importance"], y=fi["feature"], orientation="h",
                           marker_color=P["violet"], hovertemplate="%{x:.1%}"))
    fig.update_xaxes(title_text="Model importance", tickformat=".0%")
    fig.update_layout(showlegend=False)
    return ui.style_fig(fig, height, hovermode="closest")
