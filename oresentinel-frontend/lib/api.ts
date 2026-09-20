/**
 * ===========================================================================
 *  OreSentinel — SINGLE POINT OF BACKEND INTEGRATION
 * ===========================================================================
 *
 *  HOW TO WIRE YOUR BACKEND (3 steps)
 *  ----------------------------------
 *  1. Set NEXT_PUBLIC_API_BASE_URL in `.env.local` (see `.env.local.example`).
 *  2. Open `ENDPOINTS` below and replace the placeholder paths with the real
 *     route paths from your backend.
 *  3. Nothing else. Every widget already reads through `api.*`, so all nine
 *     screens light up at once.
 *
 *  ⚠️ IMPORTANT — about the paths below
 *  ------------------------------------
 *  I attempted to read https://github.com/manjirirelekar47/sih26009-moil to
 *  extract the real routes. The repository returns **HTTP 404** from the
 *  GitHub API, i.e. it is currently **private or renamed**, so no route or
 *  response schema could be verified. To avoid shipping invented endpoint
 *  names that merely *look* authoritative, the paths below are explicit,
 *  clearly-marked placeholders. They are NOT guesses about your API — they
 *  are a contract you fill in. Grep the project for `TODO(api)` to find
 *  every one of them.
 *
 *  DATA CONTRACT — what each screen sends to the backend
 *  ----------------------------------------------------
 *  All shapes are declared in `types/index.ts`. If your backend nests fields
 *  differently, adapt inside the `normalise` helpers at the bottom of this
 *  file rather than touching the components.
 * ===========================================================================
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ?? 'http://localhost:8000';

/**
 * TODO(api) — replace every value with the real path from your backend.
 * Keep the keys: components import `ENDPOINTS.dashboardKpis`, not the string.
 */
export const ENDPOINTS = {
  dashboardKpis: '/api/dashboard/kpis',
  activeAlerts: '/api/alerts/active',
  quickActions: '/api/dashboard/quick-actions',

  reserveZones: '/api/reserves/zones',
  mineMarkers: '/api/reserves/mines',
  reserveInsights: '/api/reserves/insights',
  layerTiles: '/api/reserves/layers/{layer}', // {layer} = LayerKey

  productionTrend: '/api/production/trend',
  productionForecast: '/api/production/forecast',

  shortfallRisk: '/api/shortfall/predictions',

  weather: '/api/environment/weather',

  equipment: '/api/equipment/health',

  prescriptiveActions: '/api/actions/prescriptive',

  reports: '/api/reports',
  settings: '/api/settings',
} as const;

export type EndpointKey = keyof typeof ENDPOINTS;

/** Resolve a placeholder such as `/api/reserves/layers/{layer}`. */
export function buildPath(key: EndpointKey, params?: Record<string, string>) {
  let path: string = ENDPOINTS[key];
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      path = path.replace(`{${k}}`, encodeURIComponent(v));
    }
  }
  return `${API_BASE_URL}${path}`;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly url: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Thin fetch wrapper: same-origin cookies, JSON in / JSON out, typed result.
 * Swap in your auth header here if the backend needs a bearer token.
 */
export async function request<T>(
  key: EndpointKey,
  params?: Record<string, string>,
  init?: RequestInit & { query?: Record<string, string | number | undefined> },
): Promise<T> {
  const url = new URL(buildPath(key, params));
  if (init?.query) {
    for (const [k, v] of Object.entries(init.query)) {
      if (v !== undefined && v !== '') url.searchParams.set(k, String(v));
    }
  }

  const res = await fetch(url.toString(), {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });

  if (!res.ok) {
    throw new ApiError(`GET ${url.pathname} failed (${res.status})`, res.status, url.toString());
  }
  return (await res.json()) as T;
}

/**
 * Every screen talks to the backend through this object.
 * Add a method here when you add a screen — components never call fetch().
 */
export const api = {
  dashboardKpis: () => request<import('@/types').Kpi[]>('dashboardKpis'),
  activeAlerts: () => request<import('@/types').Alert[]>('activeAlerts'),
  quickActions: () => request<import('@/types').QuickAction[]>('quickActions'),

  mineMarkers: () => request<import('@/types').MineMarker[]>('mineMarkers'),
  reserveZones: () => request<import('@/types').ReserveZone[]>('reserveZones'),
  reserveInsights: () => request<import('@/types').ReserveMappingInsights>('reserveInsights'),

  productionTrend: (months = 12) =>
    request<import('@/types').ProductionPoint[]>('productionTrend', undefined, {
      query: { months },
    }),
  productionForecast: () =>
    request<import('@/types').ForecastSummary>('productionForecast'),

  shortfallRisk: () => request<import('@/types').Alert[]>('shortfallRisk'),
  weather: () => request<import('@/types').WeatherWeek[]>('weather'),
  equipment: () => request<import('@/types').Equipment[]>('equipment'),
  prescriptiveActions: () =>
    request<import('@/types').PrescriptiveAction[]>('prescriptiveActions'),
};

/* -------------------------------------------------------------------------- */
/*  Normalisation hooks                                                       */
/* -------------------------------------------------------------------------- */
// If your backend envelopes responses (e.g. `{ data: [...] }`) or uses
// snake_case, normalise here once and leave the components untouched.
//
// export function normaliseKpis(raw: any): Kpi[] {
//   return raw.data.map((r: any) => ({
//     id: r.id,
//     label: r.label,
//     value: r.value,
//     unit: r.unit,
//     deltaPct: r.delta_pct,
//     trend: r.delta_pct > 0 ? 'up' : r.delta_pct < 0 ? 'down' : 'flat',
//   }));
// }
