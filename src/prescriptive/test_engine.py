"""
Tests for the prescriptive engine. Run from the repo root:
    python -m src.prescriptive.test_engine
(also works with pytest if you have it installed)
"""
import itertools
import tempfile
from pathlib import Path

from src.prescriptive.engine import (downtime_band, load_rules, normalise_alerts, recommend,
                                     risk_band, week_context)

W = lambda t, l: {"type": t, "level": l}


def ids(cards):
    return [c["rule_id"] for c in cards]


def test_bands():
    assert [risk_band(x) for x in (0.0, 0.29, 0.30, 0.59, 0.60, 1.0)] == ["low", "low", "medium", "medium", "high", "high"]
    assert downtime_band("HIGH") == "high"
    assert downtime_band(9.0, (10.5, 13.5)) == "low" and downtime_band(12.0, (10.5, 13.5)) == "medium"
    assert downtime_band(20.0, (10.5, 13.5)) == "high"


def test_bad_inputs_raise():
    for bad in (lambda: risk_band(1.4), lambda: normalise_alerts([W("road", "extreme")]),
                lambda: downtime_band("huge"), lambda: downtime_band(12.0)):
        try:
            bad()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


def test_report_example_redeploy():
    """Report: 'high downtime risk, no weather issue -> redeploy equipment'."""
    cards = recommend(0.8, [], "high", worst_equipment="LDR-03")
    assert ids(cards) == ["R01"] and cards[0]["priority"] == "High"
    assert "LDR-03" in cards[0]["action"]


def test_report_example_road_risk():
    """Report: 'high road risk -> shift the schedule / alternate route'."""
    cards = recommend(0.8, [W("road", "warning"), W("haul_friction", "warning")], "medium")
    assert {"R09", "R11"} <= set(ids(cards))


def test_waterlogging_watch_is_medium_priority():
    cards = recommend(0.45, [W("waterlogging", "watch")], "low")
    assert ids(cards) == ["R08"] and cards[0]["priority"] == "Medium"


def test_blasting_rule_needs_delays_and_alert():
    assert "R14" in ids(recommend(0.5, [W("road", "watch")], "low", blast_delay_days=2))
    assert "R14" not in ids(recommend(0.5, [W("road", "watch")], "low", blast_delay_days=0))
    assert "R15" in ids(recommend(0.5, [], "low", blast_delay_days=1))


def test_low_risk_with_alert_only_precaution():
    assert ids(recommend(0.1, [W("waterlogging", "warning")], "low")) == ["R13"]


def test_compound_risk():
    assert "R16" in ids(recommend(0.9, [W("road", "warning")], "high"))


def test_anomaly_adds_data_check():
    assert "R17" in ids(recommend(0.1, [], "low", is_anomaly=True))
    assert "R17" not in ids(recommend(0.1, [], "low", is_anomaly=False))


def test_sorted_high_first():
    order = {"High": 0, "Medium": 1, "Low": 2}
    cards = recommend(0.9, [W("road", "warning")], "high", blast_delay_days=2, is_anomaly=True)
    pr = [order[c["priority"]] for c in cards]
    assert pr == sorted(pr)


def test_alert_level_synonyms():
    assert normalise_alerts([W("Road Risk", "High"), W("road", "watch")]) == {"road": 2}


def test_every_input_combination_gets_a_card_without_fallback():
    """No gaps in the rule table: every combination must match at least one real rule."""
    alert_sets = [[]] + [[W(t, l)] for t in ("waterlogging", "road", "haul_friction") for l in ("watch", "warning")]
    for risk, alerts, dt, blast, anom in itertools.product(
            (0.1, 0.45, 0.8), alert_sets, ("low", "medium", "high"), (0, 2), (False, True)):
        cards = recommend(risk, alerts, dt, blast_delay_days=blast, is_anomaly=anom)
        assert cards and cards[0]["rule_id"] != "FALLBACK", (risk, alerts, dt, blast, anom)


def test_rules_file_is_well_formed():
    rules = load_rules()
    assert len({r["rule_id"] for r in rules}) == len(rules), "duplicate rule_id"
    assert all(r["priority"] in ("High", "Medium", "Low") for r in rules)


def test_week_context_reads_synthetic_files():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "p.csv").write_text("week_start,fleet_downtime_pct,blast_delay_days\n"
                                 "2025-01-06,9,0\n2025-01-13,12,1\n2025-01-20,20,2\n")
        (d / "e.csv").write_text("week_start,equipment_id,downtime_hours\n"
                                 "2025-01-20,DRL-01,10\n2025-01-20,LDR-02,30\n2025-01-13,DRL-01,5\n")
        ctx = week_context("2025-01-20", d / "p.csv", d / "e.csv")
        assert ctx["blast_delay_days"] == 2 and ctx["worst_equipment"] == "LDR-02"
        assert recommend(0.8, [], **ctx)[0]["priority"] == "High"


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    for name, fn in tests:
        fn()
        print("ok  ", name)
    print(f"\nAll {len(tests)} tests passed")
