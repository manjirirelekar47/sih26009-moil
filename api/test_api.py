"""Smoke-test every route against the real CSVs.  Run:  python -m api.test_api"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402

c = TestClient(app)
fails = []


def show(route):
    r = c.get(route)
    if r.status_code != 200:
        print(f"FAIL  {r.status_code}  {route}\n      {r.text[:160]}")
        fails.append(route)
        return None
    d = r.json()
    n = len(d) if isinstance(d, list) else f"{len(d)} keys"
    print(f"PASS  {r.status_code}  {route:42s} -> {n}")
    return d


print("=" * 84)
h = show("/api/health")
if h:
    print("      modules:", h["modules_loaded"])
    missing = [k for k, v in h["files_present"].items() if not v]
    print("      missing files:", missing or "none")

print("=" * 84)
k = show("/api/dashboard/kpis")
if k:
    for x in k:
        val = f"{x['value']:,.1f}" if x["value"] is not None else "null"
        print(f"      {x['id']:11s} {val:>12} {x['unit']:6s} {x.get('footnote','')}")

print("-" * 84)
t = show("/api/production/trend?months=12")
if t:
    print(f"      {len(t)} months | first {t[0]['month']} {t[0]['monthIso']} "
          f"actual={t[0]['actual']} fc={t[0]['forecast']} | last {t[-1]['month']} "
          f"actual={t[-1]['actual']} fc={t[-1]['forecast']}")

z = show("/api/reserves/zones?min_score=0.9")
if z:
    print(f"      {len(z)} rings >=0.90 | ring[0] {z[0]['id']} prosp={z[0]['prospectivity']}")

m = show("/api/reserves/mines")
if m:
    for x in m:
        print(f"      {x['name']:7s} {x['lng']},{x['lat']} prosp={x['prospectivity']} {x['status']}")

print("-" * 84)
for r in ("/api/reserves/insights", "/api/reserves/layers/ndvi", "/api/reserves/layers/satelliteImagery"):
    show(r)

fc = show("/api/production/forecast")
if fc:
    print(f"      target={fc['targetMt']:,.0f} forecast={fc['forecastMt']:,.0f} "
          f"var={fc['variancePct']}% risk={fc['riskLevel']} horizon={fc['horizonWeeks']}w unit={fc['unit']}")

show("/api/shortfall/predictions")
print("-" * 84)
w = show("/api/environment/weather")
if w:
    for x in w[-2:]:
        print(f"      {x['day']} rain={x['rainfallMm']}mm lst={x['landTempC']}C note={x['riskNote'][:44]}")

e = show("/api/equipment/health")
if e:
    print(f"      {len(e)} machines | top {e[0]['name']} risk={e[0]['riskScore']} "
          f"band={e[0]['riskBand']} driver={e[0]['mainDriver']} health={e[0]['healthPct']}%")

print("-" * 84)
a = show("/api/actions/prescriptive")
if a:
    for x in a:
        print(f"      [{x['priority']:6s}] {x['title'][:44]:46s} {x['impactValue'][:40]}")

al = show("/api/alerts/active")
if al:
    for x in al:
        print(f"      [{x['severity']:6s}] {x['title'][:60]}")

print("-" * 84)
show("/api/dashboard/quick-actions")
rp = show("/api/reports")
if rp:
    print(f"      artefacts present: {sum(1 for x in rp if x['available'])}/{len(rp)}")
show("/api/settings")
print("=" * 84)
print("RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAILED -> {fails}")
