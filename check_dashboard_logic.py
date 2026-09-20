"""
Self-check for dashboard_logic.py on YOUR real data.   Run from the repo root:
    py -3.11 check_dashboard_logic.py
Compare the printed numbers for the latest week with the Streamlit app (same week selected).
"""
import dashboard_logic as DL

ws = DL.weeks()
print(f"{len(ws)} weeks, {ws[0]} to {ws[-1]}")
snap = DL.week_snapshot()                     # latest week, like Streamlit's default
w, f = snap["weather"], snap["fleet"]
print(f"\nWeek {snap['weekStart']}")
print(f"  planned {snap['plannedTonnes']:,.0f} t | actual {snap['actualTonnes']:,.0f} t | shortfall {snap['shortfallPct']:+.1f}%")
print(f"  shortfall risk {snap['shortfallRisk']:.2f} | anomaly {snap['isAnomaly']} | blast delays {snap['blastDelayDays']} d")
print(f"  rain 48h {w['rain48hMm']} mm | rain 7d {w['rain7dMm']} mm | soil moisture {w['soilMoistureIndex']} | dry days {w['dryDays']}")
print(f"  fleet downtime {f['downtimeRisk']} | worst machine {f['worstEquipment']} | weather delay {w['delayFactor']*100:.0f}%")
print("  weather alerts:", ", ".join(f"{a['label']}={a['level']}" for a in w["alerts"]))
print(f"\n{len(snap['cards'])} recommendation card(s):")
for c in snap["cards"]:
    print(f"  [{c['priority']}] {c['title']}")

base = DL.whatif()                            # no overrides = the actual week
assert [c["rule_id"] for c in base["simulated"]["cards"]] == [c["rule_id"] for c in snap["cards"]], "what-if baseline differs"
assert base["delta"] == {"delayPts": 0.0, "alerts": 0}
wet = DL.whatif(rain48hMm=120, rain7dMm=300, soilMoistureIndex=0.9)
print(f"\nWhat-if (heavy rain): delay {wet['simulated']['delayFactor']*100:.0f}% ({wet['delta']['delayPts']:+.0f} pts), "
      f"{wet['simulated']['alertCount']} alert(s), {len(wet['simulated']['cards'])} card(s)")
imp = DL.reserve_importances()
print(f"\nReserve model: top driver {imp['topDriver']} ({imp['topDriverSharePct']}%), demo={imp['isDemo']}")
print("\nSELF-CHECK OK")
