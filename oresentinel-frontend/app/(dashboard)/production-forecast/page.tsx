'use client';

import { AlertTriangle, Lightbulb, TrendingDown } from 'lucide-react';
import PageHeader from '@/components/layout/PageHeader';
import ProductionTrendChart from '@/components/charts/ProductionTrendChart';
import { Card, CardHeader } from '@/components/ui/Card';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockForecastSummary } from '@/data/mock';
import { cn, fmt } from '@/lib/utils';

/**
 * Production Forecast screen: variance metrics · Actual vs Forecast vs Target
 * chart · Key Factors Affecting Forecast · AI Insight.
 *
 * TODO(api) → GET {base}{ENDPOINTS.productionForecast} → ForecastSummary
 */
export default function ProductionForecastPage() {
  const { data: f, usingFallback } = useApi(api.productionForecast, mockForecastSummary);

  return (
    <>
      <PageHeader
        title="Production Forecast"
        subtitle="AI-based forecasting using historical production, equipment data, and weather inputs."
        action={<DataStateBadge show={usingFallback} />}
      />

      {/* Variance metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="card-pad">
          <p className="muted">Target (Monthly)</p>
          <p className="mt-2 text-[26px] font-extrabold leading-none text-slate-900">
            {fmt(f.targetMt)} <span className="text-[12px] font-medium text-slate-500">Mt</span>
          </p>
        </Card>
        <Card className="card-pad">
          <p className="muted">Forecast (Next Month)</p>
          <p className="mt-2 text-[26px] font-extrabold leading-none text-slate-900">
            {fmt(f.forecastMt)} <span className="text-[12px] font-medium text-slate-500">Mt</span>
          </p>
        </Card>
        <Card className="card-pad border-risk-med/30 bg-risk-medBg/40">
          <p className="muted">Variance</p>
          <p className="mt-2 flex items-center gap-1.5 text-[26px] font-extrabold leading-none text-risk-med">
            <TrendingDown className="h-5 w-5" />
            {f.variancePct}%
          </p>
          <p className="mt-1.5 flex items-center gap-1 text-[11px] font-semibold text-risk-med">
            <AlertTriangle className="h-3.5 w-3.5" />
            {f.riskLevel} Risk Level
          </p>
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <ProductionTrendChart height={320} />
        </div>

        <div className="space-y-4 xl:col-span-4">
          <Card className="card-pad">
            <CardHeader title="Key Factors Affecting Forecast" />
            <ul className="mt-3.5 space-y-3">
              {f.factors.map((factor) => (
                <li key={factor.id}>
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-[11.5px] font-medium text-slate-700">{factor.label}</span>
                    <span
                      className={cn(
                        'shrink-0 text-[11.5px] font-bold',
                        factor.impactPct < 0 ? 'text-risk-high' : 'text-risk-ok',
                      )}
                    >
                      {factor.impactPct > 0 ? '+' : ''}
                      {factor.impactPct}%
                    </span>
                  </div>
                  <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={cn('h-full rounded-full', factor.impactPct < 0 ? 'bg-risk-high/70' : 'bg-risk-ok/70')}
                      style={{ width: `${Math.min(100, Math.abs(factor.impactPct) * 5)}%` }}
                    />
                  </div>
                  <p className="muted mt-1">{factor.note}</p>
                </li>
              ))}
            </ul>
          </Card>

          <Card className="card-pad border-brand/20 bg-brand-light/40">
            <CardHeader title="AI Insight" icon={<Lightbulb className="h-4 w-4 text-brand" />} />
            <p className="mt-2.5 text-[11.5px] leading-relaxed text-slate-600">{f.insight}</p>
          </Card>
        </div>
      </div>
    </>
  );
}
