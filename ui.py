"""ui.py: OreSentinel-themed look-and-feel helpers for the MOIL dashboard.

Colours match .streamlit/config.toml + OreSentinel dark sidebar from the mockup.
"""
from __future__ import annotations

import html
from typing import Iterable, Sequence

import streamlit as st

PALETTE = {
    "ink":    "#1A2236",
    "muted":  "#5F6B82",
    "line":   "#D5DAE5",
    "grid":   "#E3E7EF",
    "violet": "#5A3E9B",
    "teal":   "#3C9A8E",
    "ok":     "#1E8E5A",
    "watch":  "#B7791F",
    "risk":   "#C0392B",
}

SERIES = [PALETTE["violet"], PALETTE["teal"], PALETTE["ok"], PALETTE["watch"], PALETTE["risk"], "#4C6EF5"]

_LEVELS = {
    "high":   PALETTE["risk"],
    "medium": PALETTE["watch"],
    "low":    PALETTE["ok"],
}

_KINDS = {
    "ok":      PALETTE["ok"],
    "watch":   PALETTE["watch"],
    "risk":    PALETTE["risk"],
    "neutral": PALETTE["muted"],
}

_CSS = f"""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}

/* ── Global page ── */
.main .block-container {{
    padding-top: 0 !important;
    padding-bottom: 2rem;
    max-width: 1600px;
}}
[data-testid="stHeader"] {{ background: transparent; height: 0; }}
#MainMenu, footer {{ visibility: hidden; }}

/* ── SIDEBAR — dark OreSentinel style ── */
[data-testid="stSidebar"] {{
    background: #0D1B2A !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1rem;
}}
[data-testid="stSidebar"] * {{
    color: rgba(255,255,255,0.80) !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.10) !important;
    margin: 0.6rem 0;
}}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
    color: rgba(255,255,255,0.45) !important;
    font-size: 0.68rem !important;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    font-weight: 600;
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
    color: rgba(255,255,255,0.85) !important;
    font-size: 0.83rem;
}}
[data-testid="stSidebar"] .stSelectbox > div > div {{
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 8px;
    color: white !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background: #F0F2F7;
    border-radius: 10px;
    padding: 4px;
    border: none;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 7px;
    padding: 0.4rem 1rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: {PALETTE['muted']};
    border: none;
    background: transparent;
}}
.stTabs [aria-selected="true"] {{
    background: white !important;
    color: {PALETTE['violet']} !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.10);
}}

/* ── Metrics ── */
[data-testid="stMetricLabel"] p {{
    font-size: 0.78rem;
    color: {PALETTE['muted']};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
[data-testid="stMetricValue"] {{
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    color: {PALETTE['ink']};
    font-size: 1.5rem !important;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.75rem !important;
}}
[data-testid="metric-container"] {{
    background: white;
    border-radius: 12px;
    padding: 1rem 1.2rem !important;
    border: 1px solid {PALETTE['line']};
    box-shadow: 0 1px 6px rgba(26,34,54,0.06);
}}

/* ── OreSentinel page header ── */
.ore-topbar {{
    background: white;
    border-bottom: 1px solid {PALETTE['line']};
    padding: 1rem 2rem 0.9rem 2rem;
    margin: 0 -2rem 1.5rem -2rem;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.8rem;
}}
.ore-topbar h1 {{
    margin: 0; padding: 0;
    font-size: 1.55rem;
    font-weight: 800;
    color: {PALETTE['ink']};
    line-height: 1.2;
}}
.ore-topbar .sub {{
    margin: 0.2rem 0 0 0;
    color: {PALETTE['muted']};
    font-size: 0.88rem;
}}
.ore-pills {{
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
    align-items: center;
}}

/* ── Pills ── */
.ore-pill {{
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.18rem 0.65rem;
    border-radius: 999px;
    border: 1.5px solid currentColor;
    white-space: nowrap;
    letter-spacing: 0.02em;
}}
.ore-pill.ok      {{ color: {PALETTE['ok']};    background: #E6F4EC; }}
.ore-pill.watch   {{ color: {PALETTE['watch']};  background: #FBF1DD; }}
.ore-pill.risk    {{ color: {PALETTE['risk']};   background: #FBE7E4; }}
.ore-pill.neutral {{ color: {PALETTE['muted']};  background: #ECEFF5; }}
.ore-pill.teal    {{ color: {PALETTE['teal']};   background: #E6F4F2; }}

/* ── Action cards (prescriptive engine) ── */
.ore-card {{
    background: white;
    border: 1px solid {PALETTE['line']};
    border-left: 5px solid;
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.65rem;
    box-shadow: 0 1px 5px rgba(26,34,54,0.05);
    transition: box-shadow 0.15s;
}}
.ore-card:hover {{ box-shadow: 0 3px 12px rgba(26,34,54,0.10); }}
.ore-card .ct  {{ font-weight: 700; font-size: 0.93rem; color: {PALETTE['ink']}; margin-bottom: 0.2rem; }}
.ore-card .cd  {{ color: {PALETTE['muted']}; font-size: 0.84rem; line-height: 1.5; }}
.ore-card .ca  {{ margin-top: 0.45rem; font-size: 0.88rem; color: {PALETTE['ink']}; }}
.ore-card .ca b {{ color: {PALETTE['violet']}; }}

/* ── Weather / status cards ── */
.ore-status {{
    background: white;
    border: 1px solid {PALETTE['line']};
    border-left: 5px solid;
    border-radius: 10px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 4px rgba(26,34,54,0.05);
}}
.ore-status .row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
}}
.ore-status .st {{ font-weight: 700; font-size: 0.88rem; color: {PALETTE['ink']}; }}
.ore-status .sd {{ margin-top: 0.3rem; font-size: 0.80rem; color: {PALETTE['muted']}; line-height: 1.4; }}

/* ── Equipment tiles ── */
.ore-tile {{
    background: white;
    border: 1px solid {PALETTE['line']};
    border-top: 4px solid;
    border-radius: 10px;
    padding: 0.65rem 0.8rem;
    margin-bottom: 0.5rem;
    text-align: center;
    box-shadow: 0 1px 4px rgba(26,34,54,0.05);
}}
.ore-tile .eid  {{ font-weight: 700; font-size: 0.82rem; color: {PALETTE['ink']}; }}
.ore-tile .emeta {{ color: {PALETTE['muted']}; font-size: 0.72rem; margin-top: 0.1rem; }}
.ore-tile .escore {{ font-size: 1.45rem; font-weight: 800; font-variant-numeric: tabular-nums; margin: 0.25rem 0 0.1rem; }}
.ore-tile .eband  {{ font-size: 0.70rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
.ore-tile .edrv   {{ font-size: 0.66rem; color: {PALETTE['muted']}; margin-top: 0.2rem; }}

/* ── Section dividers ── */
.ore-section {{
    font-size: 0.88rem;
    font-weight: 700;
    color: {PALETTE['ink']};
    border-left: 4px solid {PALETTE['teal']};
    padding-left: 0.6rem;
    margin: 1.2rem 0 0.7rem 0;
    letter-spacing: -0.01em;
}}

/* ── Logo block in sidebar ── */
.ore-logo {{
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.3rem 0.5rem 0.8rem 0.5rem;
}}
.ore-logo-icon {{
    background: rgba(60,154,142,0.22);
    border: 1px solid rgba(60,154,142,0.40);
    border-radius: 10px;
    width: 38px; height: 38px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem; flex-shrink: 0;
}}
.ore-logo-name {{
    font-size: 1.05rem;
    font-weight: 800;
    color: white !important;
    letter-spacing: -0.01em;
    line-height: 1.15;
}}
.ore-logo-tag {{
    font-size: 0.59rem;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    font-weight: 600;
    color: rgba(255,255,255,0.38) !important;
}}

/* ── Ministry card ── */
.ore-ministry {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 10px;
    padding: 0.65rem 0.8rem;
    margin-top: 0.5rem;
}}
.ore-ministry .mn  {{ font-size: 0.82rem; font-weight: 700; color: white !important; }}
.ore-ministry .ms  {{ font-size: 0.70rem; color: rgba(255,255,255,0.48) !important; }}
.ore-ministry .mg  {{ font-size: 0.64rem; color: rgba(255,255,255,0.30) !important; }}

/* ── Containers ── */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 12px !important;
    border-color: {PALETTE['line']} !important;
}}
</style>
"""


def _flat(markup: str) -> str:
    return "".join(line.strip() for line in markup.splitlines())


def _e(value) -> str:
    return html.escape(str(value))


def level_kind(level) -> str:
    lvl = str(level).upper()
    if lvl in ("HIGH", "CRITICAL", "HIGH_HAZARD"):        return "risk"
    if lvl in ("MODERATE", "WARNING", "MODERATE_HAZARD"): return "watch"
    if lvl in ("LOW", "STABLE", "NORMAL"):                return "ok"
    return "neutral"


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def sidebar_logo() -> None:
    st.markdown(_flat("""
        <div class="ore-logo">
          <div class="ore-logo-icon">⛏️</div>
          <div>
            <div class="ore-logo-name">Ore<span style="color:#3C9A8E">Sentinel</span></div>
            <div class="ore-logo-tag">Smart Mines, Stronger Tomorrow</div>
          </div>
        </div>
    """), unsafe_allow_html=True)


def ministry_card() -> None:
    st.markdown(_flat("""
        <div class="ore-ministry">
          <div class="mn">MOIL Limited</div>
          <div class="ms">Ministry of Steel</div>
          <div class="mg">Govt. of India</div>
        </div>
    """), unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "",
                pills: Iterable[tuple[str, str]] = ()) -> None:
    pill_html = "".join(
        f'<span class="ore-pill {_e(kind)}">{_e(text)}</span>'
        for text, kind in pills
    )
    st.markdown(_flat(f"""
        <div class="ore-topbar">
          <div>
            <h1>{_e(title)}</h1>
            <p class="sub">{_e(subtitle)}</p>
          </div>
          <div class="ore-pills">{pill_html}</div>
        </div>
    """), unsafe_allow_html=True)


def section(title: str) -> None:
    st.markdown(f'<div class="ore-section">{_e(title)}</div>', unsafe_allow_html=True)


def kpi_row(items: Sequence[dict]) -> None:
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.metric(
                item["label"],
                item["value"],
                item.get("delta"),
                delta_color=item.get("delta_color", "normal"),
                help=item.get("help"),
                border=True,
            )


def action_card(level: str, title: str, detail: str, action: str | None = None) -> None:
    color = _LEVELS.get(str(level).lower(), PALETTE["muted"])
    action_html = f'<div class="ca"><b>Action:</b> {_e(action)}</div>' if action else ""
    st.markdown(_flat(f"""
        <div class="ore-card" style="border-left-color:{color}">
          <div class="ct">{_e(title)}</div>
          <div class="cd">{_e(detail)}</div>
          {action_html}
        </div>
    """), unsafe_allow_html=True)


def status_card(kind: str, title: str, badge: str, body: str = "") -> None:
    kind = kind if kind in _KINDS else "neutral"
    body_html = f'<div class="sd">{_e(body)}</div>' if body else ""
    st.markdown(_flat(f"""
        <div class="ore-status" style="border-left-color:{_KINDS[kind]}">
          <div class="row">
            <span class="st">{_e(title)}</span>
            <span class="ore-pill {kind}">{_e(badge)}</span>
          </div>
          {body_html}
        </div>
    """), unsafe_allow_html=True)


def equipment_tile(equipment_id, equipment_type, age_years,
                   score: float, band, driver) -> None:
    color = _LEVELS.get(str(band).lower(), PALETTE["muted"])
    st.markdown(_flat(f"""
        <div class="ore-tile" style="border-top-color:{color}">
          <div class="eid">{_e(equipment_id)}</div>
          <div class="emeta">{_e(equipment_type)} · {_e(age_years)} yr</div>
          <div class="escore" style="color:{color}">{float(score):.2f}</div>
          <div class="eband" style="color:{color}">{_e(str(band).upper())}</div>
          <div class="edrv">{_e(driver)}</div>
        </div>
    """), unsafe_allow_html=True)


def style_fig(fig, height: int = 360, hovermode: str = "x unified"):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=8, r=8, t=40, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=PALETTE["ink"], family="Inter, sans-serif"),
        colorway=SERIES,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=11)),
        hovermode=hovermode,
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(size=10))
    fig.update_yaxes(gridcolor=PALETTE["grid"], tickfont=dict(size=10))
    return fig
