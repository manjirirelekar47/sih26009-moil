'use client';

import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Cog,
  Database,
  HardHat,
  Target,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { cn, fmt, signedPct } from '@/lib/utils';
import type { Kpi } from '@/types';

/** Icon per KPI id, matching the mockup's icon set. */
const ICONS: Record<string, React.ElementType> = {
  reserves: Database,
  production: HardHat,
  target: Target,
  shortfall: AlertTriangle,
  equipment: Cog,
};

/**
 * A single KPI summary card.
 * Handles all three visual variants from the design:
 *   1. delta + trend arrow   (Reserves, Production, Equipment Health)
 *   2. progress bar          (Production Target — 90%)
 *   3. severity warning      (Shortfall Risk — 2 Mines, High risk)
 */
export default function KpiCard({ kpi, usingFallback }: { kpi: Kpi; usingFallback?: boolean }) {
  const Icon = ICONS[kpi.id] ?? Database;
  const isRisk = kpi.severity === 'high';
  const isWarn = kpi.severity === 'medium';
  const up = kpi.trend === 'up';
  const down = kpi.trend === 'down';

  return (
    <Card className="card-pad animate-fade-up">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'flex h-8 w-8 items-center justify-center rounded-lg',
              isRisk ? 'bg-risk-highBg' : isWarn ? 'bg-risk-medBg' : 'bg-brand-light',
            )}
          >
            <Icon
              className={cn('h-[15px] w-[15px]', isRisk ? 'text-risk-high' : isWarn ? 'text-risk-med' : 'text-brand')}
              strokeWidth={2.2}
            />
          </span>
          <p className="text-[11px] font-medium leading-tight text-slate-500">{kpi.label}</p>
        </div>
        <DataStateBadge show={!!usingFallback} />
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        <span
          className={cn(
            'text-[24px] font-extrabold leading-none tracking-tight',
            isRisk ? 'text-risk-high' : isWarn ? 'text-risk-med' : 'text-slate-900',
          )}
        >
          {kpi.value === null || kpi.value === undefined
            ? '—'
            : fmt(kpi.value, Number.isInteger(kpi.value) ? 0 : 1)}
        </span>
        <span className="text-[11.5px] font-medium text-slate-500">{kpi.unit}</span>
      </div>

      {/* Variant 2 — progress bar */}
      {kpi.progressPct !== undefined ? (
        <div className="mt-3">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-brand transition-[width] duration-500"
              style={{ width: `${kpi.progressPct}%` }}
              role="progressbar"
              aria-valuenow={kpi.progressPct}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
          <p className="muted mt-1.5">{kpi.footnote ?? `${kpi.progressPct}% of monthly goal`}</p>
        </div>
      ) : null}

      {/* Variant 3 — severity footnote */}
      {kpi.severity ? (
        <p className={cn('mt-3 flex items-center gap-1 text-[11px] font-semibold',
          isRisk ? 'text-risk-high' : 'text-risk-med')}>
          <AlertTriangle className="h-3.5 w-3.5" />
          {kpi.footnote ?? 'High risk'}
        </p>
      ) : null}

      {/* Variant 1 — delta */}
      {kpi.deltaPct !== undefined ? (
        <p className="mt-3 flex items-center gap-1 text-[11px]">
          <span
            className={cn(
              'inline-flex items-center gap-0.5 font-semibold',
              up && 'text-risk-ok',
              down && 'text-risk-high',
              !up && !down && 'text-slate-500',
            )}
          >
            {up ? <ArrowUpRight className="h-3.5 w-3.5" /> : null}
            {down ? <ArrowDownRight className="h-3.5 w-3.5" /> : null}
            {signedPct(kpi.deltaPct)}
          </span>
          <span className="text-slate-500">{kpi.footnote}</span>
        </p>
      ) : null}
    </Card>
  );
}
