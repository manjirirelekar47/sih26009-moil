"""Run from the repo root:  python -m src.equipment_health.test_health   (pytest also works)"""
import tempfile
from pathlib import Path

import pandas as pd

from src.equipment_health.health import (band, fleet_context, fleet_summary, score_equipment)
from src.prescriptive.engine import recommend


def make_eq(rows):
    """rows: (week, id, type, age, downtime_h, breakdowns)"""
    return pd.DataFrame(rows, columns=["week_start", "equipment_id", "equipment_type", "age_years",
                                       "downtime_hours", "breakdown_events"]).assign(scheduled_hours=140)


def weeks(n):
    return pd.date_range("2025-01-06", periods=n, freq="W-MON")


def two_machines(n=12, good_dt=10, bad_dt=40, good_age=3, bad_age=13, bad_breakdowns=1):
    rows = []
    for w in weeks(n):
        rows.append((w, "GOOD", "loader", good_age, good_dt, 0))
        rows.append((w, "BAD", "loader", bad_age, bad_dt, bad_breakdowns))
    return make_eq(rows)


def test_worse_machine_scores_higher_and_scores_are_0_to_1():
    s = score_equipment(two_machines())
    last = s[s["week_start"] == s["week_start"].max()].set_index("equipment_id")
    assert last.loc["BAD", "risk_score"] > last.loc["GOOD", "risk_score"]
    assert s["risk_score"].between(0, 1).all()


def test_band_edges():
    assert [band(x) for x in (0.0, 0.59, 0.60, 0.77, 0.78, 1.0)] == ["low", "low", "medium", "medium", "high", "high"]


def test_no_peeking_at_the_future():
    a = two_machines()
    b = a.copy()
    b.loc[b["week_start"] == b["week_start"].max(), "downtime_hours"] = 140   # change only the LAST week
    sa, sb = score_equipment(a, dt_ref=20), score_equipment(b, dt_ref=20)
    early = sa["week_start"] < sa["week_start"].max()
    assert (sa[early]["risk_score"].values == sb[early]["risk_score"].values).all()


def test_main_driver_is_reported():
    s = score_equipment(two_machines(good_dt=10, bad_dt=10, bad_age=15, bad_breakdowns=0), dt_ref=20)
    assert s[s["equipment_id"] == "BAD"]["main_driver"].iloc[-1] == "machine age"


def test_fleet_summary_rules():
    def wk(bands):
        return pd.DataFrame({"equipment_id": [f"M{i}" for i in range(len(bands))],
                             "risk_score": [{"low": .3, "medium": .7, "high": .9}[b] for b in bands],
                             "risk_band": bands})
    assert fleet_summary(wk(["high", "high", "low"]))["downtime_risk"] == "high"
    assert fleet_summary(wk(["high", "low", "low"]))["downtime_risk"] == "medium"
    assert fleet_summary(wk(["medium"] * 4 + ["low"]))["downtime_risk"] == "medium"
    assert fleet_summary(wk(["medium"] * 3 + ["low"]))["downtime_risk"] == "low"
    assert fleet_summary(wk(["low", "medium", "high"]))["worst_equipment"] == "M2"


def test_fleet_context_feeds_the_prescriptive_engine():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        eq = score_equipment(two_machines(bad_dt=60, bad_breakdowns=1))
        eq.to_csv(d / "risk.csv", index=False)
        last = eq["week_start"].max().strftime("%Y-%m-%d")
        pd.DataFrame({"week_start": [last], "blast_delay_days": [2]}).to_csv(d / "prod.csv", index=False)
        ctx = fleet_context(last, d / "risk.csv", d / "prod.csv")
        assert ctx["worst_equipment"] == "BAD" and ctx["blast_delay_days"] == 2
        assert ctx["downtime_risk"] in ("low", "medium", "high")
        assert recommend(0.8, [], **ctx)          # runs end to end


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    for name, fn in tests:
        fn()
        print("ok  ", name)
    print(f"\nAll {len(tests)} tests passed")
