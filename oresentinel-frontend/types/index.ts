/**
 * Shared domain types for OreSentinel.
 *
 * These now match the FastAPI layer in `api/main.py` 1:1, which in turn reads
 * the prototype's CSVs (`docs/DATA_CONTRACT.md`). Any further divergence belongs
 * in the `normalise` helpers at the bottom of `lib/api.ts`, not here.
 */

export type Trend = 'up' | 'down' | 'flat';

export interface Kpi {
  id: string;
  label: string;
  /** null is allowed — the API returns null where the data genuinely has no value. */
  value: number | null;
  unit: string;
  deltaPct?: number;
  trend?: Trend;
  progressPct?: number;
  severity?: 'high' | 'medium' | 'low';
  footnote?: string;
}

export type AlertSeverity = 'high' | 'medium' | 'low';

export interface Alert {
  id: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  createdAt: string;
  href?: string;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: string;
  href: string;
}

export interface MineMarker {
  id: string;
  name: string;
  lng: number;
  lat: number;
  /** 0–1 model prospectivity score. NOT reserve tonnage per hectare. */
  prospectivity: number;
  status: 'operational' | 'warning' | 'inspection';
  distToReferenceMineKm?: number;
}

export interface ReserveZone {
  id: string;
  name: string;
  /** GeoJSON ring: [[lng, lat], ...] */
  coordinates: [number, number][];
  /** 0–1 model prospectivity score. NOT reserve tonnage per hectare. */
  prospectivity: number;
}

export interface ProductionPoint {
  month: string;
  monthIso?: string;
  /** tonnes; null = no actual recorded for that month */
  actual: number | null;
  /** tonnes; null = outside the forecast window */
  forecast: number | null;
  target: number | null;
}

export type LayerKey =
  | 'estimatedReserves'
  | 'ndvi'
  | 'soilMoisture'
  | 'landTemperature'
  | 'geologicalFormations'
  | 'mineBoundary'
  | 'satelliteImagery';

export interface LayerToggle {
  key: LayerKey;
  label: string;
  defaultOn: boolean;
}

export interface ForecastFactor {
  id: string;
  label: string;
  note: string;
  impactPct: number;
}

export interface ForecastSummary {
  /** tonnes */
  targetMt: number;
  /** tonnes */
  forecastMt: number;
  variancePct: number;
  riskLevel: 'High' | 'Medium' | 'Low';
  riskLevelRaw?: string;
  unit?: string;
  horizonWeeks?: number;
  latestWeek?: string;
  factors: ForecastFactor[];
  insight: string;
}

export type Priority = 'high' | 'medium' | 'low';

export interface PrescriptiveAction {
  id: string;
  title: string;
  priority: Priority;
  family?: string;
  rationale: string;
  action?: string;
  impactLabel: string;
  impactValue: string;
  site?: string;
  weekStart?: string;
}

export interface ReserveMappingInsights {
  /** null when the pipeline has no tonnage column (currently the case) */
  totalReservesMt: number | null;
  /** null when there is only one survey and no baseline */
  surveyDeltaPct: number | null;
  newZones: number;
  mappingConfidencePct: number;
  zonesScored?: number;
  mineralizedObservations?: number;
  labelSource?: string[];
}

export interface Equipment {
  id: string;
  name: string;
  type?: string;
  site: string;
  healthPct: number;
  status: 'operational' | 'attention' | 'down';
  nextServiceInDays: number;
  ageYears?: number;
  riskScore?: number;
  riskBand?: string;
  /** e.g. "recent downtime" | "machine age" */
  mainDriver?: string;
  downtimePct8w?: number;
  weekStart?: string;
}

export interface WeatherWeek {
  day: string;
  weekStart?: string;
  rainfallMm: number;
  ndvi?: number;
  soilMoistureIndex?: number;
  landTempC?: number;
  fleetDowntimePct?: number;
  riskNote: string;
}

export interface ReportArtifact {
  id: string;
  title: string;
  available: boolean;
  sizeKb: number | null;
  path: string | null;
  mimeType: string;
}

export interface ReserveLayerValues {
  layer: string;
  column?: string;
  count?: number;
  note?: string;
  values: { id: string; lon: number; lat: number; value: number }[];
}
