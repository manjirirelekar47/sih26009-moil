'use client';

import { CloudRain, Droplets } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardHeader } from '@/components/ui/Card';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockWeather } from '@/data/mock';

/**
 * Weather & Environment screen: 7-day rainfall outlook + per-day risk notes.
 *
 * TODO(api) → GET {base}{ENDPOINTS.weather} → WeatherWeek[]
 */
export default function WeatherEnvironmentPage() {
  const { data: week, usingFallback } = useApi(api.weather, mockWeather);
  const peak = Math.max(...week.map((d) => d.rainfallMm));

  return (
    <>
      <PageHeader
        title="Weather & Environment"
        subtitle="Rainfall outlook and its operational impact on haul roads and blasting."
        action={<DataStateBadge show={usingFallback} />}
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <Card className="card-pad">
            <CardHeader title="7-day rainfall outlook" icon={<CloudRain className="h-4 w-4" />} />
            <div className="mt-3" style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={week} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
                  <CartesianGrid stroke="#EDF2F2" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#94A3B8' }}
                    axisLine={false}
                    tickLine={false}
                    label={{
                      value: 'Rainfall (mm)',
                      angle: -90,
                      position: 'insideLeft',
                      offset: 22,
                      style: { fontSize: 9.5, fill: '#94A3B8' },
                    }}
                  />
                  <Tooltip
                    contentStyle={{ borderRadius: 10, border: '1px solid #E2E8F0', fontSize: 11 }}
                    formatter={(v: number) => [`${v} mm`, 'Rainfall']}
                  />
                  <Bar dataKey="rainfallMm" radius={[5, 5, 0, 0]} fill="#0F6CBD" maxBarSize={38} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        <div className="xl:col-span-4">
          <Card className="card-pad">
            <CardHeader title="Operational impact" icon={<Droplets className="h-4 w-4" />} />
            <ul className="mt-3.5 space-y-3">
              {week.map((d) => (
                <li key={d.day} className="flex items-center gap-3">
                  <span className="w-8 shrink-0 text-[11.5px] font-semibold text-slate-700">{d.day}</span>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-actual"
                      style={{ width: `${Math.round((d.rainfallMm / peak) * 100)}%` }}
                    />
                  </div>
                  <span className="shrink-0 text-[10.5px] text-slate-400">{d.rainfallMm} mm</span>
                </li>
              ))}
            </ul>
            <div className="mt-4 space-y-2 border-t border-line pt-3">
              {week
                .filter((d) => d.rainfallMm >= 20)
                .map((d) => (
                  <p key={d.day} className="text-[11px] text-slate-600">
                    <span className="font-semibold text-risk-med">{d.day}:</span> {d.riskNote}
                  </p>
                ))}
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}
