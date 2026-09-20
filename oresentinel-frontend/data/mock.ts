import type {
  Alert,
  Equipment,
  ForecastSummary,
  Kpi,
  LayerToggle,
  MineMarker,
  PrescriptiveAction,
  ProductionPoint,
  QuickAction,
  ReserveMappingInsights,
  ReserveZone,
  WeatherWeek,
} from '@/types';

/**
 * ===========================================================================
 *  FIXTURE DATA — REAL values, captured from the FastAPI layer.
 * ===========================================================================
 *  Every number below came out of `api/main.py` reading the prototype's own
 *  CSVs — it is not transcribed from the design mockup any more. The mockup's
 *  figures (245.6 Mt, 3.8 Mt) could not be reproduced because no such data
 *  exists in the pipeline; see START_HERE.md.
 *
 *  These render only while the backend is unreachable (see lib/useApi.ts).
 *  Once uvicorn is running, the live values replace them and the "Demo data"
 *  badge disappears.
 * ===========================================================================
 */

export const mockKpis: Kpi[] = [
  {
    id: "reserves",
    label: "High-prospectivity Zones",
    value: 188,
    unit: "zones",
    footnote: "score \u2265 0.90 \u00b7 900 cells scored",
  },
  {
    id: "production",
    label: "Current Production (weekly)",
    value: 22309.0,
    unit: "t",
    deltaPct: 5.8,
    trend: "up",
    footnote: "vs weekly plan",
  },
  {
    id: "target",
    label: "Planned Production (weekly)",
    value: 21081.0,
    unit: "t",
    progressPct: 106,
    footnote: "105.8% of weekly plan achieved",
  },
  {
    id: "shortfall",
    label: "Shortfall Risk (model)",
    value: 23.6,
    unit: "%",
    severity: "high",
    footnote: "Moderate risk",
  },
  {
    id: "equipment",
    label: "Fleet Health",
    value: 88,
    unit: "%",
    footnote: "8 machines \u00b7 week 22 Dec 2025",
  },
];

export const mockAlerts: Alert[] = [
  {
    id: "act-0", severity: "low", title: "No action needed",
    description: "Shortfall risk is low (0.24), there is no weather alert and fleet downtime is medium.",
    createdAt: "2026-09-20T14:11:40.644425Z", href: "/corrective-actions",
  },
  {
    id: "risk-0", severity: "high", title: "Week of 03 Jul 2023 \u2014 risk 100.0%",
    description: "Forecast 15,965 t vs target 21,081 t",
    createdAt: "2026-09-20T14:11:40.647800Z", href: "/shortfall-prediction",
  },
  {
    id: "risk-1", severity: "high", title: "Week of 10 Jul 2023 \u2014 risk 100.0%",
    description: "Forecast 15,097 t vs target 21,081 t",
    createdAt: "2026-09-20T14:11:40.647804Z", href: "/shortfall-prediction",
  },
];

export const mockQuickActions: QuickAction[] = [
  { id: "q1", label: "View Reserve Map", icon: "map", href: "/reserve-mapping" },
  { id: "q2", label: "Check Forecast", icon: "trending", href: "/production-forecast" },
  { id: "q3", label: "See Shortfall Risks", icon: "alert", href: "/shortfall-prediction" },
  { id: "q4", label: "Equipment Status", icon: "gear", href: "/equipment-health" },
  { id: "q5", label: "Recommended Actions", icon: "shield", href: "/corrective-actions" },
];

/** Top exploration targets from reserve_mapping/data/top_exploration_targets.csv */
export const mockMineMarkers: MineMarker[] = [
  { id: 'mine-a', name: 'Mine A', lng: 80.185, lat: 21.825, prospectivity: 0.9942, status: 'operational' },
  { id: 'mine-b', name: 'Mine B', lng: 80.215, lat: 21.795, prospectivity: 0.9917, status: 'operational' },
  { id: 'mine-c', name: 'Mine C', lng: 80.235, lat: 21.815, prospectivity: 0.9877, status: 'warning' },
  { id: 'mine-d', name: 'Mine D', lng: 80.255, lat: 21.855, prospectivity: 0.9838, status: 'warning' },
];

/** Highest-prospectivity grid cells from reserve_mapping/data/zone_scores.csv */
export const mockReserveZones: ReserveZone[] = [
  {
    id: 'r17_c13',
    name: 'Zone r17_c13',
    prospectivity: 0.9942,
    coordinates: [
      [80.18, 21.82],
      [80.19, 21.82],
      [80.19, 21.83],
      [80.18, 21.83],
      [80.18, 21.82],
    ],
  },
  {
    id: 'r15_c14',
    name: 'Zone r15_c14',
    prospectivity: 0.9926,
    coordinates: [
      [80.19, 21.8],
      [80.2, 21.8],
      [80.2, 21.81],
      [80.19, 21.81],
      [80.19, 21.8],
    ],
  },
  {
    id: 'r14_c16',
    name: 'Zone r14_c16',
    prospectivity: 0.9917,
    coordinates: [
      [80.21, 21.79],
      [80.22, 21.79],
      [80.22, 21.8],
      [80.21, 21.8],
      [80.21, 21.79],
    ],
  },
  {
    id: 'r15_c15',
    name: 'Zone r15_c15',
    prospectivity: 0.9913,
    coordinates: [
      [80.2, 21.8],
      [80.21, 21.8],
      [80.21, 21.81],
      [80.2, 21.81],
      [80.2, 21.8],
    ],
  },
  {
    id: 'r16_c15',
    name: 'Zone r16_c15',
    prospectivity: 0.9893,
    coordinates: [
      [80.2, 21.81],
      [80.21, 21.81],
      [80.21, 21.82],
      [80.2, 21.82],
      [80.2, 21.81],
    ],
  },
  {
    id: 'r16_c14',
    name: 'Zone r16_c14',
    prospectivity: 0.9886,
    coordinates: [
      [80.19, 21.81],
      [80.2, 21.81],
      [80.2, 21.82],
      [80.19, 21.82],
      [80.19, 21.81],
    ],
  },
  {
    id: 'r14_c18',
    name: 'Zone r14_c18',
    prospectivity: 0.9881,
    coordinates: [
      [80.23, 21.79],
      [80.24, 21.79],
      [80.24, 21.8],
      [80.23, 21.8],
      [80.23, 21.79],
    ],
  },
  {
    id: 'r17_c15',
    name: 'Zone r17_c15',
    prospectivity: 0.9881,
    coordinates: [
      [80.2, 21.82],
      [80.21, 21.82],
      [80.21, 21.83],
      [80.2, 21.83],
      [80.2, 21.82],
    ],
  },
  {
    id: 'r16_c18',
    name: 'Zone r16_c18',
    prospectivity: 0.9877,
    coordinates: [
      [80.23, 21.81],
      [80.24, 21.81],
      [80.24, 21.82],
      [80.23, 21.82],
      [80.23, 21.81],
    ],
  },
  {
    id: 'r15_c12',
    name: 'Zone r15_c12',
    prospectivity: 0.9873,
    coordinates: [
      [80.17, 21.8],
      [80.18, 21.8],
      [80.18, 21.81],
      [80.17, 21.81],
      [80.17, 21.8],
    ],
  },
  {
    id: 'r17_c16',
    name: 'Zone r17_c16',
    prospectivity: 0.9872,
    coordinates: [
      [80.21, 21.82],
      [80.22, 21.82],
      [80.22, 21.83],
      [80.21, 21.83],
      [80.21, 21.82],
    ],
  },
  {
    id: 'r17_c12',
    name: 'Zone r17_c12',
    prospectivity: 0.9869,
    coordinates: [
      [80.17, 21.82],
      [80.18, 21.82],
      [80.18, 21.83],
      [80.17, 21.83],
      [80.17, 21.82],
    ],
  },
  {
    id: 'r17_c14',
    name: 'Zone r17_c14',
    prospectivity: 0.9864,
    coordinates: [
      [80.19, 21.82],
      [80.2, 21.82],
      [80.2, 21.83],
      [80.19, 21.83],
      [80.19, 21.82],
    ],
  },
  {
    id: 'r14_c15',
    name: 'Zone r14_c15',
    prospectivity: 0.9847,
    coordinates: [
      [80.2, 21.79],
      [80.21, 21.79],
      [80.21, 21.8],
      [80.2, 21.8],
      [80.2, 21.79],
    ],
  },
];

/**
 * Legend bands for the map.
 *
 * HONESTY NOTE: the pipeline stores a unitless `prospectivity_score` in 0–1.
 * There is NO "estimated reserve in Mt per hectare" field anywhere in the repo,
 * so the mockup's "> 1.5 / 1.0–1.5 / … Mt per ha" legend would label a unit
 * that does not exist. These bands describe the real quantity.
 */
export const PROSPECTIVITY_LEGEND = [
  { label: '≥ 0.95 — very high', min: 0.95, color: '#2F855A' },
  { label: '0.85 – 0.95 high', min: 0.85, color: '#3C9A8E' },
  { label: '0.60 – 0.85 moderate', min: 0.6, color: '#D69E2E' },
  { label: '0.30 – 0.60 low', min: 0.3, color: '#DD6B20' },
  { label: '< 0.30 negligible', min: 0, color: '#E53E3E' },
] as const;

export function reserveColor(v: number): string {
  const hit = PROSPECTIVITY_LEGEND.find((l) => v >= l.min);
  return hit?.color ?? '#E53E3E';
}

/** Monthly sums from forecasting/output/forecast_results.csv (tonnes). */
export const mockProductionTrend: ProductionPoint[] = [
  { month: 'Apr', monthIso: '2025-04', actual: 88643.0, forecast: null, target: 84324.0 },
  { month: 'May', monthIso: '2025-05', actual: 83939.0, forecast: null, target: 84324.0 },
  { month: 'Jun', monthIso: '2025-06', actual: 99560.0, forecast: null, target: 105405.0 },
  { month: 'Jul', monthIso: '2025-07', actual: 60035.0, forecast: null, target: 84324.0 },
  { month: 'Aug', monthIso: '2025-08', actual: 68362.0, forecast: null, target: 84324.0 },
  { month: 'Sep', monthIso: '2025-09', actual: 90387.0, forecast: null, target: 105405.0 },
  { month: 'Oct', monthIso: '2025-10', actual: 84498.0, forecast: null, target: 84324.0 },
  { month: 'Nov', monthIso: '2025-11', actual: 85993.0, forecast: null, target: 84324.0 },
  { month: 'Dec', monthIso: '2025-12', actual: 85793.0, forecast: 107556.1, target: 84324.0 },
  { month: 'Jan', monthIso: '2026-01', actual: null, forecast: 88234.5, target: 0.0 },
  { month: 'Feb', monthIso: '2026-02', actual: null, forecast: 85978.2, target: 0.0 },
  { month: 'Mar', monthIso: '2026-03', actual: null, forecast: 64338.8, target: 0.0 },
];

export const mockForecastSummary: ForecastSummary = {
  targetMt: 21081.0,
  forecastMt: 21743.3,
  variancePct: 3.1,
  riskLevel: 'Medium',
  unit: 'tonnes',
  horizonWeeks: 12,
  latestWeek: '2026-03-16',
  factors: [
    { id: 'f-risk', label: 'Model risk score (latest week)', note: 'forecasting/output/forecast_results.csv', impactPct: -23.6 },
    { id: 'f-anomaly', label: 'Anomalous weeks detected', note: '13 flagged weeks', impactPct: -13 },
    { id: 'f-corr', label: 'Risk score vs production change', note: 'Pearson correlation on weekly data', impactPct: -0.2 },
  ],
  insight: "Weekly production plan is 21,081 t against a 12-week forecast averaging 21,743 t (+3.1%). Model risk level is Moderate; 13 anomalous weeks were detected. Risk score and production change correlate at -0.02, so the risk signal alone does not explain the variance.",
};

export const mockReserveInsights: ReserveMappingInsights = {
  totalReservesMt: null,
  surveyDeltaPct: null,
  newZones: 188,
  mappingConfidencePct: 86,
  zonesScored: 900,
  mineralizedObservations: 276,
  labelSource: ["REAL_GEOLOGICAL"],
};

export const mockLayerToggles: LayerToggle[] = [
  { key: 'estimatedReserves', label: 'Estimated Reserves (prospectivity)', defaultOn: true },
  { key: 'ndvi', label: 'Vegetation Index (NDVI)', defaultOn: false },
  { key: 'soilMoisture', label: 'Soil Moisture (Sentinel-1 VV)', defaultOn: false },
  { key: 'landTemperature', label: 'Land Temperature (MODIS LST)', defaultOn: false },
  { key: 'geologicalFormations', label: 'Geological Formations', defaultOn: false },
  { key: 'mineBoundary', label: 'Mine Boundary', defaultOn: true },
  { key: 'satelliteImagery', label: 'Satellite Imagery', defaultOn: true },
];

/**
 * Offline fallback for Prescriptive Actions.
 *
 * NOTE: the live rules engine currently returns ONE card ("No action needed")
 * because the most recent week is on track. These four are the design mockup's
 * cards, kept so the screen demonstrates its layout while offline. They are
 * labelled as illustrative, not as live output.
 */
export const mockActions: PrescriptiveAction[] = [
  {
    id: 'ILLUSTRATIVE-1',
    title: 'Redeploy Excavator EX-12 to Mine B',
    priority: 'high',
    family: 'Fleet redeployment',
    site: 'Mine B',
    rationale: 'Predicted equipment shortage at Mine B. Redeployment can increase production by ~12%. (illustrative)',
    action: 'Move EX-12 to Mine B for the next two weeks.',
    impactLabel: 'Estimated impact',
    impactValue: '+12% production',
  },
  {
    id: 'ILLUSTRATIVE-2',
    title: 'Reschedule Blasting at Mine C',
    priority: 'medium',
    family: 'Schedule change',
    site: 'Mine C',
    rationale: 'Heavy rainfall expected on 21-23 Sep. Consider rescheduling to avoid delays. (illustrative)',
    action: 'Shift blasting window past the rainfall peak.',
    impactLabel: 'Estimated impact',
    impactValue: 'Avoid 2-3 day delay',
  },
  {
    id: 'ILLUSTRATIVE-3',
    title: 'Optimize Haulage Routes',
    priority: 'medium',
    family: 'Haulage',
    site: 'Mine C',
    rationale: 'Potential waterlogging on main access road. Use alternate route R-2. (illustrative)',
    action: 'Switch to alternate route R-2.',
    impactLabel: 'Estimated impact',
    impactValue: 'Maintain 90% transport efficiency',
  },
  {
    id: 'ILLUSTRATIVE-4',
    title: 'Advance Maintenance for Drill Rig DR-05',
    priority: 'low',
    family: 'Maintenance',
    site: 'Mine A',
    rationale: 'Maintenance due in 3 days. Early servicing can prevent downtime. (illustrative)',
    action: 'Bring the service forward.',
    impactLabel: 'Estimated impact',
    impactValue: 'Reduce downtime risk by 20%',
  },
];

/** Latest week from data/processed/equipment_risk.csv */
export const mockEquipment: Equipment[] = [
  {
    id: 'DMP-03', name: 'Dumper DMP-03', site: 'Balaghat', healthPct: 15, status: 'down',
    nextServiceInDays: 3, ageYears: 12.0, riskScore: 0.8463, riskBand: 'high',
    mainDriver: 'recent downtime', downtimePct8w: 16.34, weekStart: '2025-12-22',
  },
  {
    id: 'LDR-03', name: 'Loader LDR-03', site: 'Balaghat', healthPct: 43, status: 'operational',
    nextServiceInDays: 30, ageYears: 13.0, riskScore: 0.5695, riskBand: 'low',
    mainDriver: 'machine age', downtimePct8w: 11.16, weekStart: '2025-12-22',
  },
  {
    id: 'DMP-02', name: 'Dumper DMP-02', site: 'Balaghat', healthPct: 44, status: 'operational',
    nextServiceInDays: 30, ageYears: 8.0, riskScore: 0.5629, riskBand: 'low',
    mainDriver: 'recent downtime', downtimePct8w: 12.5, weekStart: '2025-12-22',
  },
  {
    id: 'DRL-02', name: 'Drill DRL-02', site: 'Balaghat', healthPct: 49, status: 'operational',
    nextServiceInDays: 30, ageYears: 11.0, riskScore: 0.5142, riskBand: 'low',
    mainDriver: 'machine age', downtimePct8w: 11.06, weekStart: '2025-12-22',
  },
  {
    id: 'LDR-02', name: 'Loader LDR-02', site: 'Balaghat', healthPct: 56, status: 'operational',
    nextServiceInDays: 30, ageYears: 9.0, riskScore: 0.4352, riskBand: 'low',
    mainDriver: 'machine age', downtimePct8w: 9.78, weekStart: '2025-12-22',
  },
  {
    id: 'DMP-01', name: 'Dumper DMP-01', site: 'Balaghat', healthPct: 59, status: 'operational',
    nextServiceInDays: 30, ageYears: 3.0, riskScore: 0.4098, riskBand: 'low',
    mainDriver: 'recent downtime', downtimePct8w: 11.51, weekStart: '2025-12-22',
  },
  {
    id: 'DRL-01', name: 'Drill DRL-01', site: 'Balaghat', healthPct: 60, status: 'operational',
    nextServiceInDays: 30, ageYears: 6.0, riskScore: 0.4025, riskBand: 'low',
    mainDriver: 'recent downtime', downtimePct8w: 12.14, weekStart: '2025-12-22',
  },
  {
    id: 'LDR-01', name: 'Loader LDR-01', site: 'Balaghat', healthPct: 78, status: 'operational',
    nextServiceInDays: 30, ageYears: 4.0, riskScore: 0.2218, riskBand: 'low',
    mainDriver: 'recent downtime', downtimePct8w: 5.77, weekStart: '2025-12-22',
  },
];

/** Weekly aggregates from data/processed/weekly_features.csv (NOT daily). */
export const mockWeather: WeatherWeek[] = [
  { day: '10 Nov', weekStart: '2025-11-10', rainfallMm: 0.0, ndvi: 0.493, soilMoistureIndex: 0.595, landTempC: 22.6, riskNote: 'Moderate road risk: Surface slickness detected.' },
  { day: '17 Nov', weekStart: '2025-11-17', rainfallMm: 2.7, ndvi: 0.427, soilMoistureIndex: 0.464, landTempC: 22.4, riskNote: 'Moderate road risk: Surface slickness detected.' },
  { day: '24 Nov', weekStart: '2025-11-24', rainfallMm: 5.6, ndvi: 0.458, soilMoistureIndex: 0.613, landTempC: 22.2, riskNote: 'Moderate road risk: Surface slickness detected.' },
  { day: '01 Dec', weekStart: '2025-12-01', rainfallMm: 5.7, ndvi: 0.339, soilMoistureIndex: 0.498, landTempC: 20.8, riskNote: 'Moderate road risk: Surface slickness detected.' },
  { day: '08 Dec', weekStart: '2025-12-08', rainfallMm: 0.0, ndvi: 0.443, soilMoistureIndex: 0.426, landTempC: 20.9, riskNote: 'Moderate road risk: Surface slickness detected.' },
  { day: '15 Dec', weekStart: '2025-12-15', rainfallMm: 0.0, ndvi: 0.436, soilMoistureIndex: 0.536, landTempC: 20.0, riskNote: 'Moderate road risk: Surface slickness detected.' },
  { day: '22 Dec', weekStart: '2025-12-22', rainfallMm: 0.0, ndvi: 0.431, soilMoistureIndex: 0.418, landTempC: 18.5, riskNote: 'Moderate road risk: Surface slickness detected.' },
];
