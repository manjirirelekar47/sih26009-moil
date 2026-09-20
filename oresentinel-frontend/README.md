# OreSentinel — Frontend (Next.js 15 · TypeScript · Tailwind CSS)

AI-powered mining analytics dashboard for **MOIL Limited** (Ministry of Steel, Govt. of India):
manganese reserve mapping, production forecasting, shortfall prediction and prescriptive actions.

## Quick start

```bash
npm install
cp .env.local.example .env.local     # set NEXT_PUBLIC_API_BASE_URL + Mapbox token
npm run dev                          # http://localhost:3000  ->  redirects to /dashboard
```

```bash
npm run build && npm start           # production
npm run typecheck                    # tsc --noEmit
```

## Wiring your backend — 3 steps

1. Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local`.
2. Open **`lib/api.ts`** and replace the paths in `ENDPOINTS` with the real routes.
3. Done — all nine screens read through `api.*`, so they all light up at once.

> **Note on the endpoint paths.** `https://github.com/manjirirelekar47/sih26009-moil` returns
> **HTTP 404** from the GitHub API (the repo is currently private or renamed), so no route or
> response schema could be verified. Every path in `ENDPOINTS` is therefore an explicit,
> clearly-marked placeholder — **not** a guess dressed up as fact. Grep for `TODO(api)` to find
> every integration point.

While the backend is unreachable the widgets render typed fixtures from `data/mock.ts` and show a
small **"Demo data"** badge, so nobody demos mock numbers believing they are live.

## Folder structure

```
app/
  layout.tsx                    root layout (Inter + Caveat fonts, globals.css)
  page.tsx                      /  ->  redirect to /dashboard
  globals.css                   Tailwind layers + .card / .nav-item component classes
  (dashboard)/
    layout.tsx                  shell: fixed sidebar + sticky header + <main>
    dashboard/page.tsx          KPI row · map · trend · alerts · quick actions · promo
    reserve-mapping/page.tsx    map + Layer Controls rail + Key Insights strip
    production-forecast/page.tsx  variance metrics · chart · factors · AI insight
    shortfall-prediction/page.tsx  per-mine risk table + risk feed
    weather-environment/page.tsx   7-day rainfall outlook + operational impact
    equipment-health/page.tsx      fleet health bars + service countdown
    corrective-actions/page.tsx    priority tabs + recommended actions
    reports/page.tsx            period summary + export scaffold
    settings/page.tsx           notification / data preferences
components/
  layout/    Sidebar.tsx  Header.tsx  PageHeader.tsx
  widgets/   KpiCard.tsx  KpiRow.tsx  ActiveAlerts.tsx  QuickActions.tsx  PromoCard.tsx
  charts/    ProductionTrendChart.tsx
  map/       ReserveMap.tsx  ReserveMapCard.tsx  MapCanvas.tsx  PlaceholderMap.tsx
             ReserveLegend.tsx  LayerControls.tsx
  ui/        Card.tsx  Badge.tsx  Skeleton.tsx  DataStateBadge.tsx
lib/         api.ts  useApi.ts  utils.ts
types/       index.ts
data/        mock.ts
public/      mining-excavator.svg
```

## Geospatial

`mapbox-gl` is code-split via `next/dynamic({ ssr: false })`, so it never runs on the server.
Set `NEXT_PUBLIC_MAPBOX_TOKEN` for the live satellite view; leave it empty and the app renders an
SVG placeholder with the same reserve zones, Mine A–D markers and legend — the build and the demo
keep working either way.

To use **deck.gl** instead of Mapbox, replace the body of `components/map/MapCanvas.tsx`
(`PolygonLayer` / `ScatterplotLayer` over the same `zones` and `markers` props).

## Design tokens

All colours from the mockup live in `tailwind.config.ts`: `ink` (#0B2523 sidebar), `brand`
(#106D63 accent), `canvas` (#F3F6F6 content), `actual` (#0F6CBD), `brand-mid` (#3C9A8E forecast),
`target` (#A0AEC0), plus the `risk.*` severity ramp. Change them in one place.

## Status

`reports` and `settings` are deliberate scaffolds — their endpoints are the only two that still
need real routes. Everything else is wired and ready to swap fixtures for live data.
