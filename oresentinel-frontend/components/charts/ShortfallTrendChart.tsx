'use client';

import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardHeader } from '@/components/ui/Card';
import type { Alert } from '@/types';

interface WeekRisk {
  week: string;
  riskPct: number;
  forecast: number;
  target: number;
}

/**
 * The API sends per-week shortfall risk as prose ("Week of 03 Jul 2023 —
 * risk 100.0%", "Forecast 15,965 t vs target 21,081 t") rather than a typed
 * series — there's no separate numeric endpoint for it. This parses that
 * text back into numbers so it can be charted instead of only read as a
 * list. Anything that doesn't match the expected shape is skipped rather
 * than guessed at.
 */
function parseWeeklyRisk(alerts: Alert[]): WeekRisk[] {
  const rows: WeekRisk[] = [];
  for (const a of alerts) {
    const weekMatch = a.title.match(/Week of ([^—-]+?)\s*[—-]\s*risk\s*([\d.]+)\s*%/i);
    const descMatch = a.description.match(/Forecast\s*([\d,]+)\s*t\s*vs\s*target\s*([\d,]+)\s*t/i);
    if (!weekMatch || !descMatch) continue;
    rows.push({
      week: weekMatch[1].trim(),
      riskPct: parseFloat(weekMatch[2]),
      forecast: parseInt(descMatch[1].replace(/,/g, ''), 10),
      target: parseInt(descMatch[2].replace(/,/g, ''), 10),
    });
  }
  return rows;
}

export default function ShortfallTrendChart({ risks }: { risks: Alert[] }) {
  const data = parseWeeklyRisk(risks);

  if (data.length === 0) return null;

  return (
    <Card className="card-pad">
      <CardHeader
        title="Forecast vs target — at-risk weeks"
        icon={<span className="text-[15px]">📉</span>}
      />
      <div className="mt-2 flex items-center gap-4 text-[10.5px] text-slate-500">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-[3px] w-4 rounded-full bg-actual" />
          Forecast (t)
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-[3px] w-4 rounded-full bg-target" />
          Target (t)
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-risk-high/70" />
          Shortfall risk (%)
        </span>
      </div>
      <div className="mt-2" style={{ height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
            <CartesianGrid stroke="#EDF2F2" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="week" tick={{ fontSize: 9.5, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
            <YAxis
              yAxisId="tonnes"
              tick={{ fontSize: 10, fill: '#94A3B8' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `${Math.round(v / 1000)}k`}
            />
            <YAxis
              yAxisId="risk"
              orientation="right"
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#94A3B8' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 10,
                border: '1px solid #E2E8F0',
                fontSize: 11,
                boxShadow: '0 4px 12px rgb(16 24 40 / 0.08)',
              }}
              formatter={(v: number, name: string) =>
                name === 'Shortfall risk (%)' ? [`${v}%`, name] : [`${v.toLocaleString('en-IN')} t`, name]}
            />
            <Bar yAxisId="tonnes" dataKey="forecast" name="Forecast (t)" fill="#0F6CBD" radius={[5, 5, 0, 0]} maxBarSize={30} />
            <Bar yAxisId="tonnes" dataKey="target" name="Target (t)" fill="#A0AEC0" radius={[5, 5, 0, 0]} maxBarSize={30} />
            <Area
              yAxisId="risk"
              type="monotone"
              dataKey="riskPct"
              name="Shortfall risk (%)"
              stroke="#E53E3E"
              fill="#E53E3E"
              fillOpacity={0.12}
              strokeWidth={2}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
