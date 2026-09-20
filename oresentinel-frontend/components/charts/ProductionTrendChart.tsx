'use client';

import { useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardHeader } from '@/components/ui/Card';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockProductionTrend } from '@/data/mock';
import { cn } from '@/lib/utils';

const RANGES = [
  { id: '3m', label: 'Last 3 months', months: 3 },
  { id: '6m', label: 'Last 6 months', months: 6 },
  { id: '12m', label: 'Last 12 months', months: 12 },
] as const;

/**
 * Production Trend — Actual vs Forecast line chart with a shaded forecast zone.
 *
 * TODO(api) → GET {base}{ENDPOINTS.productionTrend}?months={3|6|12}
 *   Expected: ProductionPoint[]  { month, actual|null, forecast|null, target|null }
 *   `null` means "no value for that series in that month" — Recharts renders a gap.
 */
export default function ProductionTrendChart({ height = 260 }: { height?: number }) {
  const [range, setRange] = useState<(typeof RANGES)[number]['id']>('12m');
  const months = RANGES.find((r) => r.id === range)!.months;

  // NOTE: `months` is a real dependency, so changing the range re-fetches.
  const { data: trend, usingFallback } = useApi(
    () => api.productionTrend(months),
    mockProductionTrend,
    [months],
  );

  const data = trend.slice(-months);

  // The mockup hard-coded a 0-5 axis because the fixtures were in Mt.
  // Real values are in tonnes (tens of thousands), so the domain is derived
  // from the data instead of hard-coded.
  const allValues = data.flatMap((d) =>
    [d.actual, d.forecast, d.target].filter((v): v is number => typeof v === 'number'),
  );
  const yMax = allValues.length ? Math.ceil(Math.max(...allValues) / 1000) * 1000 : 5;
  const yMin = allValues.length ? Math.max(0, Math.floor(Math.min(...allValues) / 1000) * 1000 - 2000) : 0;
  const firstForecast = data.find((d) => d.actual === null)?.month;

  return (
    <Card className="card-pad">
      <CardHeader
        title="Production Trend"
        icon={<span className="text-[15px]">📈</span>}
        action={
          <div className="flex items-center gap-2">
            <DataStateBadge show={usingFallback} />
            <select
              value={range}
              onChange={(e) => setRange(e.target.value as typeof range)}
              aria-label="Time range"
              className="rounded-lg border border-line bg-white px-2.5 py-1.5 text-[11px] font-medium text-slate-600 outline-none transition hover:border-brand/40 focus:ring-2 focus:ring-brand/10"
            >
              {RANGES.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        }
      />

      {/* Legend */}
      <div className="mt-3 flex items-center gap-4 text-[10.5px] text-slate-500">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-[3px] w-4 rounded-full bg-actual" />
          Actual Production
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-[3px] w-4 rounded-full bg-brand-mid" />
          Forecast
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-[3px] w-4 rounded-full bg-target" />
          Target
        </span>
      </div>

      <div className="mt-2" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#EDF2F2" strokeDasharray="3 3" vertical={false} />
            {firstForecast ? (
              <ReferenceArea
                x1={firstForecast}
                x2={data[data.length - 1]?.month}
                fill="#3C9A8E"
                fillOpacity={0.07}
                label={{ value: 'Forecast', position: 'insideTopRight', fill: '#3C9A8E', fontSize: 10 }}
              />
            ) : null}
            <XAxis
              dataKey="month"
              tick={{ fontSize: 10, fill: '#94A3B8' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[yMin, yMax]}
              tick={{ fontSize: 10, fill: '#94A3B8' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `${Math.round(v / 1000)}k`}
              label={{
                value: 'Production (tonnes)',
                angle: -90,
                position: 'insideLeft',
                offset: 22,
                style: { fontSize: 9.5, fill: '#94A3B8' },
              }}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 10,
                border: '1px solid #E2E8F0',
                fontSize: 11,
                boxShadow: '0 4px 12px rgb(16 24 40 / 0.08)',
              }}
              formatter={(v: number | string, name: string) =>
                [typeof v === 'number' ? `${v.toLocaleString('en-IN')} t` : `${v}`, name]}
            />
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual Production"
              stroke="#0F6CBD"
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#0F6CBD', strokeWidth: 0 }}
              activeDot={{ r: 4 }}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="forecast"
              name="Forecast"
              stroke="#3C9A8E"
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="target"
              name="Target"
              stroke="#A0AEC0"
              strokeWidth={1.5}
              strokeDasharray="2 4"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export { RANGES };
