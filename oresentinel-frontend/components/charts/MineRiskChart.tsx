'use client';

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardHeader } from '@/components/ui/Card';
import type { MineMarker } from '@/types';

const STATUS_COLOR: Record<MineMarker['status'], string> = {
  operational: '#2F855A',
  warning: '#DD6B20',
  inspection: '#E53E3E',
};

/**
 * Mine-level prospectivity, visualised — same `MineMarker[]` the risk table
 * already renders, so it stays in sync with it automatically.
 */
export default function MineRiskChart({ mines }: { mines: MineMarker[] }) {
  const data = [...mines].sort((a, b) => b.prospectivity - a.prospectivity);

  return (
    <Card className="card-pad">
      <CardHeader title="Mine-level prospectivity" icon={<span className="text-[15px]">⛰️</span>} />
      <div className="mt-3" style={{ height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#EDF2F2" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 10.5, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
            <YAxis
              domain={[0, 1]}
              tick={{ fontSize: 10, fill: '#94A3B8' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => v.toFixed(1)}
            />
            <Tooltip
              cursor={{ fill: '#F3F6F6' }}
              contentStyle={{ borderRadius: 10, border: '1px solid #E2E8F0', fontSize: 11 }}
              formatter={(v: number, _n, item) => [v.toFixed(4), `Prospectivity · ${item?.payload?.status}`]}
            />
            <Bar dataKey="prospectivity" radius={[6, 6, 0, 0]} maxBarSize={54}>
              {data.map((m) => (
                <Cell key={m.id} fill={STATUS_COLOR[m.status]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-4 text-[10.5px] text-slate-500">
        {(Object.keys(STATUS_COLOR) as MineMarker['status'][]).map((s) => (
          <span key={s} className="inline-flex items-center gap-1.5 capitalize">
            <span className="h-2 w-2 rounded-full" style={{ background: STATUS_COLOR[s] }} />
            {s}
          </span>
        ))}
      </div>
    </Card>
  );
}
