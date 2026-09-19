# prescriptive (Member 5) - if/then rule table -> recommendation cards

Files
- `rules.csv`    the rule table (17 rules). Edit it in Excel; the code only reads it.
- `engine.py`    `recommend(...)` returns plain-language cards; `week_context(...)` pulls downtime/blast/equipment inputs from Member 1's data.
- `test_engine.py`  14 tests, including a "no gaps in the rule table" check.

Use (Member 6):
```python
from src.prescriptive.engine import recommend, week_context
cards = recommend(shortfall_risk, alerts, **week_context("2025-08-04"))
# each card: rule_id, family, priority (High/Medium/Low), title, action, reason
```
- `shortfall_risk`: number 0-1 from Member 3 (bands: <0.30 low, <0.60 medium, else high; edit `RISK_CUTS` in engine.py)
- `alerts`: list of `{"type": "waterlogging"|"road"|"haul_friction", "level": "watch"|"warning"}` from Member 4
- optional `is_anomaly=True` from Member 3's anomaly flag

Run: `python -m src.prescriptive.test_engine`   and   `python -m src.prescriptive.engine` (demo)
Prototype rules are expert-reasoned and need validation by mine engineers.
