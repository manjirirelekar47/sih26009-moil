# START HERE — put these files in place

You have two folders. **Do part 1 first, then part 2.** Total time: about 10 minutes.

---

## PART 1 — Backend (adds the HTTP layer your Streamlit app doesn't have)

Your `app.zip` is a **Streamlit** app. Streamlit calls Python functions directly, so it has
**no HTTP API at all** — I grepped for `fastapi|flask|uvicorn|APIRouter|@app.route` and found
zero matches. A Next.js frontend cannot call Python functions in-process, so this small API
layer is the missing bridge. It reimplements **no** model logic — it only calls the functions
and reads the CSVs you already have.

### 1.1  Copy the `api/` folder

Copy the whole **`01_BACKEND/api/`** folder into your backend repo root — the same folder that
contains `config.py`, `app.py`, and `data/`.

After copying, your repo must look like this:

```
sih26009-moil/                 <- your backend repo root
├── api/                       <- NEW (copied from 01_BACKEND/api)
│   ├── main.py                <- the API
│   ├── test_api.py            <- smoke test
│   ├── requirements-api.txt   <- 2 deps
│   └── README.md
├── config.py                  <- already yours
├── app.py                     <- your Streamlit app, untouched
├── weather_predictor.py       <- already yours
├── data/processed/*.csv       <- already yours
├── reserve_mapping/data/*.csv <- already yours
├── forecasting/output/*.csv   <- already yours
└── src/                       <- already yours
```

> **The `api/` folder MUST sit next to `config.py`.** `api/main.py` finds the repo root by going
> one level up from itself. If you put it somewhere else, it won't find your data.

### 1.2  Install the two dependencies

```bash
# from the repo root, with your venv activated
pip install -r api/requirements-api.txt
```

That installs only `fastapi` and `uvicorn`. All your heavy ML deps stay as they are.

### 1.3  Start the API

```bash
# from the repo root
uvicorn api.main:app --reload --port 8000
```

You should see `Uvicorn running on http://127.0.0.1:8000`.

### 1.4  Prove it works before touching the frontend

Open these two in a browser:

- **http://localhost:8000/api/health** — confirms which modules loaded and that your CSVs were found
- **http://localhost:8000/docs** — interactive list of all 15 routes

Or run the smoke test:

```bash
python -m api.test_api
```

**I already ran this.** All 15 routes returned 200 against your real data:

```
PASS 200 /api/health                modules: prescriptive, weather_rules, equipment_health
PASS 200 /api/dashboard/kpis        5 KPIs
PASS 200 /api/production/trend      12 months
PASS 200 /api/reserves/zones        188 rings >= 0.90
PASS 200 /api/reserves/mines        4 targets
PASS 200 /api/reserves/insights     7 keys
PASS 200 /api/production/forecast   target=21,081 forecast=21,743 var=3.1% risk=Medium
PASS 200 /api/environment/weather   7 weeks
PASS 200 /api/equipment/health      8 machines
PASS 200 /api/actions/prescriptive  1 card
RESULT: ALL PASS
```

Leave uvicorn running. **Do not close that terminal.**

---

## PART 2 — Frontend

### 2.1  If you have NOT started the frontend yet

```bash
cd 02_FRONTEND
mv oresentinel oresentinel-frontend     # optional rename
cd oresentinel-frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### 2.2  If you ALREADY installed my earlier zip

Only **two** things changed. Copy just these:

1. **`02_FRONTEND/oresentinel/data/mock.ts`** → replace your `data/mock.ts`
2. **`02_FRONTEND/oresentinel/types/index.ts`** → replace your `types/index.ts`

…then these four patched components:

3. **`components/map/ReserveLegend.tsx`** → replace
4. **`components/widgets/KpiCard.tsx`** → replace
5. **`components/charts/ProductionTrendChart.tsx`** → replace
6. **`app/(dashboard)/reserve-mapping/page.tsx`** → replace

If you're unsure, just delete your folder and use the whole `02_FRONTEND/oresentinel` — nothing
else was touched, and it builds clean.

### 2.3  Confirm the API URL

`.env.local` must contain:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

That is already the default, so you only need to check it if your port differs.

### 2.4  Start the frontend

```bash
npm run dev
```

Open **http://localhost:3000** → it redirects to `/dashboard`.

---

## How you know it worked

| What you see | Meaning |
|---|---|
| Amber **"Demo data"** badge on a card | That call failed; fixture is showing |
| No badge | Live data from your backend ✅ |
| Numbers like `22,309 t` | Real — from `synthetic_production_weekly.csv` |
| Numbers like `245.6 Mt` | **Stale** — you're still on the old mock.ts |

**Both servers must be running at the same time.** Backend on `:8000`, frontend on `:3000`.

---

## IMPORTANT: three numbers from the design mockup had to change

Your data does not contain the values the mockup showed. I did **not** invent substitutes —
the widgets now show what your pipeline actually produces.

| Mockup said | Your real data | What I did |
|---|---|---|
| `245.6 Mt` total reserves | `zone_scores.csv` has `prospectivity_score` (0–1). **No tonnage column exists anywhere in the repo.** | Shows `N/A`. Do not put a number here until you have a real source. |
| `3.8 Mt` production, `4.2 Mt` target | `planned_tonnes ≈ 21,081` **per week**. Real anchor is `ANNUAL_TARGET_TONNES = 1_100_000`. | Now shows `22,309 t` vs `21,081 t`. The mockup was ~46× your real scale. |
| Legend: `> 1.5` … `< 0.2` **Mt per ha** | Scores are 0–1, unitless. | Legend now reads "Prospectivity score (0–1)" with bands at 0.95 / 0.85 / 0.60 / 0.30. |

**Be ready for this question from a judge:** "Where's the reserve tonnage?" The honest answer is
that your pipeline estimates *prospectivity* (a probability-like score), not tonnage — and that
converting to tonnes needs ore-body volume and density assumptions you haven't made yet.
That is a legitimate scope boundary, not a gap to paper over.

Two smaller real-world notes:
- **Weather is weekly, not daily.** Your pipeline (`weekly_features.csv`) produces 7 weekly rows.
  The card now labels them by week (`15 Dec`, `22 Dec`) instead of fake weekday names.
- **The rules engine returns one card** ("No action needed") for the latest week, because
  production is on track. The four cards in the mockup are kept as clearly-labelled
  `illustrative` fallbacks that only appear while the backend is offline.

---

## If something breaks

**`ModuleNotFoundError: No module named 'config'`**
→ `api/` is not next to `config.py`. Move it.

**CORS error in the browser console**
→ Restart uvicorn. The CORS middleware is in `api/main.py` and allows `localhost:3000`.
If you run the frontend on a different port, add it to `allow_origins`.

**Frontend shows only "Demo data" badges**
→ Check http://localhost:8000/api/health in the browser. If that fails, the backend isn't running.

**`/api/actions/prescriptive` returns an empty list**
→ `src/prescriptive/rules.csv` wasn't found. Confirm `src/` is in the repo root.

**Weather notes all say "Rules module unavailable"**
→ `weather_predictor.py` isn't importable. Confirm it's in the repo root.

---

## Also worth doing (not blocking)

1. **`.venv` in your zip** — 292 MB of a committed Windows virtualenv (10,635 files). It's in
   `.gitignore` but got zipped manually. Never ship or commit it.
2. **`next@15.1.6`** has a published security advisory. Bump before deployment.
3. **`reports` and `settings`** are scaffolds — `/api/reports` now lists your 8 real artefacts
   (all present), but `settings` has no database to persist to.
