"""
Prescriptive engine (Member 5): if/then rule table -> plain-language recommendation cards.

  from src.prescriptive.engine import recommend
  cards = recommend(shortfall_risk=0.72, alerts=[{"type": "road", "level": "warning"}],
                    downtime_risk="high", blast_delay_days=1, worst_equipment="LDR-03")

Each card: {rule_id, family, priority, title, action, reason}. Cards are sorted High -> Low.

The rules live in rules.csv (open it in Excel to edit). This file only reads them.
Matching rules for rules.csv columns:
  shortfall      low | medium | high            (use | for "either", or "any")
  weather_type   waterlogging | road | haul_friction | any_alert | none | any
                 (none = no active alert; any_alert = look at the strongest alert)
  weather_level  watch | warning | watch|warning | any   (level of that alert type)
  downtime       low | medium | high | any
  blast          yes (one or more blast-delay days) | no | any
  anomaly        yes | no | any
Text columns can use {risk} {risk_band} {downtime_band} {alerts} {blast_days} {equipment}.

Run a demo:   python -m src.prescriptive.engine
"""
import csv
from pathlib import Path

RULES_PATH = Path(__file__).with_name("rules.csv")

# --- Bands: agree these with Members 3 and 4 --------------------------------------
RISK_CUTS = (0.30, 0.60)            # <0.30 low, <0.60 medium, else high

LEVELS = {"none": 0, "low": 0, "watch": 1, "medium": 1, "moderate": 1,
          "warning": 2, "high": 2, "severe": 2}
LEVEL_NAMES = {0: "none", 1: "watch", 2: "warning"}
TYPE_ALIASES = {"waterlogging_risk": "waterlogging", "road_risk": "road",
                "friction": "haul_friction", "haul_road_friction": "haul_friction",
                "haul_friction_risk": "haul_friction"}
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


# --- Input helpers -------------------------------------------------------------
def risk_band(risk):
    risk = float(risk)
    if not 0.0 <= risk <= 1.0:
        raise ValueError(f"shortfall_risk must be between 0 and 1, got {risk}")
    return "low" if risk < RISK_CUTS[0] else "medium" if risk < RISK_CUTS[1] else "high"


def downtime_cuts_from_csv(path=None):
    """Low/high cut-offs (33rd and 67th percentile of fleet_downtime_pct) from the real data."""
    import pandas as pd
    if path is None:
        from config import DATA_PROCESSED
        path = DATA_PROCESSED / "synthetic_production_weekly.csv"
    pct = pd.read_csv(path)["fleet_downtime_pct"]
    return float(pct.quantile(0.33)), float(pct.quantile(0.67))


def downtime_band(value, cuts=None):
    """value = 'low'/'medium'/'high', or a fleet downtime % (needs cuts)."""
    if isinstance(value, str):
        v = value.strip().lower()
        if v not in ("low", "medium", "high"):
            raise ValueError(f"downtime_risk must be low/medium/high or a number, got {value!r}")
        return v
    if cuts is None:
        raise ValueError("Pass downtime_cuts=(low_cut, high_cut) when downtime_risk is a percentage. "
                         "Use downtime_cuts_from_csv() or week_context().")
    return "low" if value < cuts[0] else "medium" if value < cuts[1] else "high"


def _norm_type(t):
    t = str(t).strip().lower().replace(" ", "_").replace("-", "_")
    return TYPE_ALIASES.get(t, t)


def normalise_alerts(alerts):
    """[{'type','level'}, ...] -> {'road': 2, 'waterlogging': 1}  (0 none, 1 watch, 2 warning)."""
    out = {}
    for a in alerts or []:
        lvl = str(a.get("level", "none")).strip().lower()
        if lvl not in LEVELS:
            raise ValueError(f"Unknown alert level {a.get('level')!r} in {a}. Expected one of {sorted(LEVELS)}")
        t = _norm_type(a.get("type", ""))
        out[t] = max(out.get(t, 0), LEVELS[lvl])
    return out


def alerts_text(levels):
    active = sorted(((l, t) for t, l in levels.items() if l > 0), reverse=True)
    if not active:
        return "no weather alerts"
    return ", ".join(f"{t.replace('_', ' ')} {LEVEL_NAMES[l]}" for l, t in active)


# --- Rule matching ---------------------------------------------------------------
def load_rules(path=RULES_PATH):
    with open(path, newline="", encoding="utf-8-sig") as f:  # utf-8-sig: Excel adds a BOM
        return list(csv.DictReader(f))


def _in(cond, value):
    cond = (cond or "").strip().lower()
    return cond in ("", "any") or value in cond.split("|")


def _weather_ok(rule, levels):
    wtype = (rule["weather_type"] or "").strip().lower()
    strongest = max(levels.values(), default=0)
    if wtype in ("", "any"):
        return True
    if wtype == "none":
        return strongest == 0
    level = strongest if wtype == "any_alert" else levels.get(wtype, 0)
    return _in(rule["weather_level"], LEVEL_NAMES[level])


def recommend(shortfall_risk, alerts, downtime_risk, blast_delay_days=0,
              worst_equipment=None, is_anomaly=False, downtime_cuts=None, rules=None):
    """Return a list of recommendation cards for one week (highest priority first)."""
    rules = rules if rules is not None else load_rules()
    rb = risk_band(shortfall_risk)
    db = downtime_band(downtime_risk, downtime_cuts)
    levels = normalise_alerts(alerts)
    blast = "yes" if blast_delay_days and blast_delay_days > 0 else "no"
    anomaly = "yes" if is_anomaly else "no"

    ctx = {"risk": float(shortfall_risk), "risk_band": rb, "downtime_band": db,
           "alerts": alerts_text(levels), "blast_days": int(blast_delay_days or 0),
           "equipment": worst_equipment or "the unit with the most downtime"}

    cards = []
    for i, rule in enumerate(rules):
        if (_in(rule["shortfall"], rb) and _weather_ok(rule, levels) and _in(rule["downtime"], db)
                and _in(rule["blast"], blast) and _in(rule["anomaly"], anomaly)):
            cards.append((PRIORITY_ORDER.get(rule["priority"], 9), i, {
                "rule_id": rule["rule_id"], "family": rule["family"], "priority": rule["priority"],
                "title": rule["title"], "action": rule["action"].format(**ctx),
                "reason": rule["reason"].format(**ctx)}))
    if not cards:  # safety net: never return an empty answer
        cards.append((9, 0, {"rule_id": "FALLBACK", "family": "Monitor", "priority": "Low",
                             "title": "Keep the plan and re-check",
                             "action": "No rule matched. Keep the plan and re-check next week.",
                             "reason": f"Shortfall risk {rb} ({ctx['risk']:.2f}), downtime {db}, {ctx['alerts']}."}))
    return [c for _, _, c in sorted(cards, key=lambda x: (x[0], x[1]))]


# --- Pull the non-Member-3/4 inputs from Member 1's data ---------------------------
def week_context(week_start, production_csv=None, equipment_csv=None, lookback_weeks=4):
    """Downtime %, blast delays and the worst machine for one week, from the synthetic data.
    Use:  recommend(risk, alerts, **week_context("2025-08-04"))"""
    import pandas as pd
    if production_csv is None or equipment_csv is None:
        from config import DATA_PROCESSED
        production_csv = production_csv or DATA_PROCESSED / "synthetic_production_weekly.csv"
        equipment_csv = equipment_csv or DATA_PROCESSED / "synthetic_equipment_downtime_weekly.csv"
    ts = pd.Timestamp(week_start)
    prod = pd.read_csv(production_csv, parse_dates=["week_start"])
    row = prod.loc[prod["week_start"] == ts]
    if row.empty:
        raise ValueError(f"week_start {week_start} not found in {production_csv}")
    eq = pd.read_csv(equipment_csv, parse_dates=["week_start"])
    recent = eq[(eq["week_start"] <= ts) & (eq["week_start"] > ts - pd.Timedelta(weeks=lookback_weeks))]
    worst = recent.groupby("equipment_id")["downtime_hours"].sum().idxmax()
    pct = prod["fleet_downtime_pct"]
    return {"downtime_risk": float(row["fleet_downtime_pct"].iloc[0]),
            "downtime_cuts": (float(pct.quantile(0.33)), float(pct.quantile(0.67))),
            "blast_delay_days": int(row["blast_delay_days"].iloc[0]),
            "worst_equipment": worst}


# --- Demo -------------------------------------------------------------------------
if __name__ == "__main__":
    demos = [
        ("High risk, no weather issue, high downtime",
         dict(shortfall_risk=0.78, alerts=[], downtime_risk="high", worst_equipment="LDR-03")),
        ("Medium risk, road warning, blast delays",
         dict(shortfall_risk=0.45, alerts=[{"type": "road", "level": "warning"}],
              downtime_risk="medium", blast_delay_days=2)),
        ("Low risk, everything calm",
         dict(shortfall_risk=0.12, alerts=[], downtime_risk="low")),
    ]
    for name, kw in demos:
        print(f"\n=== {name} ===")
        for c in recommend(**kw):
            print(f"[{c['priority']}] {c['title']}\n    Action: {c['action']}\n    Why:    {c['reason']}")
