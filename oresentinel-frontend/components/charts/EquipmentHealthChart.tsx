'use client';

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardHeader } from '@/components/ui/Card';
import type { Equipment } from '@/types';

const STATUS_COLOR: Record<Equipment['status'], string> = {
  operational: '#2F855A',
  attention: '#DD6B20',
  down: '#E53E3E',
};

const STATUS_LABEL: Record<Equipment['status'], string> = {
  operational: 'Operational',
  attention: 'Needs attention',
  down: 'Down',
};

/**
 * Fleet health — per-unit bar chart (worst first) + a status breakdown donut.
 * Pure presentation: takes the same `Equipment[]` the list view already has,
 * no extra fetch.
 */
export default function EquipmentHealthChart({ fleet }: { fleet: Equipment[] }) {
  const sorted = [...fleet].sort((a, b) => a.healthPct - b.healthPct);

  const counts = fleet.reduce(
    (acc, e) => {
      acc[e.status] += 1;
      return acc;
    },
    { operational: 0, attention: 0, down: 0 } as Record<Equipment['status'], number>,
  );
  const donutData = (Object.keys(counts) as Equipment['status'][])
    .filter((k) => counts[k] > 0)
    .map((k) => ({ name: STATUS_LABEL[k], value: counts[k], key: k }));

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
      <div className="xl:col-span-8">
        <Card className="card-pad">
          <CardHeader title="Fleet health by unit" icon={<span className="text-[15px]">🛠️</span>} />
          <div className="mt-3" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sorted} layout="vertical" margin={{ top: 4, right: 24, bottom: 0, left: 4 }}>
                <CartesianGrid stroke="#EDF2F2" strokeDasharray="3 3" horizontal={false} />
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tick={{ fontSize: 10, fill: '#94A3B8' }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v: number) => `${v}%`}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={92}
                  tick={{ fontSize: 10.5, fill: '#475569' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: '#F3F6F6' }}
                  contentStyle={{ borderRadius: 10, border: '1px solid #E2E8F0', fontSize: 11 }}
                  formatter={(v: number, _n, item) => [`${v}% health`, item?.payload?.site ?? '']}
                />
                <Bar dataKey="healthPct" radius={[0, 5, 5, 0]} maxBarSize={16}>
                  {sorted.map((e) => (
                    <Cell key={e.id} fill={STATUS_COLOR[e.status]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="xl:col-span-4">
        <Card className="card-pad">
          <CardHeader title="Fleet status" icon={<span className="text-[15px]">⚙️</span>} />
          <div className="mt-1" style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={50}
                  outerRadius={78}
                  paddingAngle={3}
                  strokeWidth={0}
                >
                  {donutData.map((d) => (
                    <Cell key={d.key} fill={STATUS_COLOR[d.key]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ borderRadius: 10, border: '1px solid #E2E8F0', fontSize: 11 }}
                  formatter={(v: number, n: string) => [`${v} unit${v === 1 ? '' : 's'}`, n]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-1 space-y-1.5">
            {donutData.map((d) => (
              <li key={d.key} className="flex items-center justify-between text-[11px]">
                <span className="inline-flex items-center gap-1.5 text-slate-600">
                  <span className="h-2 w-2 rounded-full" style={{ background: STATUS_COLOR[d.key] }} />
                  {d.name}
                </span>
                <span className="font-semibold text-slate-800">{d.value}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
