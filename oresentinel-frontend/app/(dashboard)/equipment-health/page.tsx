'use client';

import { Wrench } from 'lucide-react';
import PageHeader from '@/components/layout/PageHeader';
import EquipmentHealthChart from '@/components/charts/EquipmentHealthChart';
import { Card, CardHeader } from '@/components/ui/Card';
import { SeverityBadge } from '@/components/ui/Badge';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockEquipment } from '@/data/mock';
import { cn } from '@/lib/utils';
import type { Equipment } from '@/types';

const TONE: Record<Equipment['status'], string> = {
  operational: 'bg-risk-ok',
  attention: 'bg-risk-med',
  down: 'bg-risk-high',
};

/**
 * Equipment Health screen: fleet list with health bars and service countdown.
 *
 * TODO(api) → GET {base}{ENDPOINTS.equipment} → Equipment[]
 */
export default function EquipmentHealthPage() {
  const { data: fleet, usingFallback } = useApi(api.equipment, mockEquipment);
  const avg = Math.round(fleet.reduce((s, e) => s + e.healthPct, 0) / (fleet.length || 1));

  return (
    <>
      <PageHeader
        title="Equipment Health"
        subtitle="Live condition monitoring and predictive maintenance windows."
        action={<DataStateBadge show={usingFallback} />}
      />

      <Card className="card-pad mb-4 flex flex-wrap items-center gap-6">
        <div>
          <p className="muted">Fleet average health</p>
          <p className="mt-1.5 text-[26px] font-extrabold leading-none text-slate-900">{avg}%</p>
        </div>
        <div>
          <p className="muted">Units tracked</p>
          <p className="mt-1.5 text-[26px] font-extrabold leading-none text-slate-900">{fleet.length}</p>
        </div>
        <div>
          <p className="muted">Needing attention</p>
          <p className="mt-1.5 text-[26px] font-extrabold leading-none text-risk-med">
            {fleet.filter((e) => e.status !== 'operational').length}
          </p>
        </div>
      </Card>

      <div className="mb-4">
        <EquipmentHealthChart fleet={fleet} />
      </div>

      <Card className="card-pad">
        <CardHeader title="Fleet status" icon={<Wrench className="h-4 w-4" />} />
        <ul className="mt-4 divide-y divide-line">
          {fleet.map((e) => (
            <li key={e.id} className="flex flex-wrap items-center gap-4 py-3.5 first:pt-0 last:pb-0">
              <div className="min-w-[150px] flex-1">
                <p className="text-[12.5px] font-semibold text-slate-800">{e.name}</p>
                <p className="muted mt-0.5">{e.site}</p>
              </div>

              <div className="w-40">
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={cn('h-full rounded-full', TONE[e.status])}
                    style={{ width: `${e.healthPct}%` }}
                  />
                </div>
                <p className="muted mt-1.5">{e.healthPct}% health</p>
              </div>

              <SeverityBadge severity={e.status === 'down' ? 'high' : e.status === 'attention' ? 'medium' : 'low'}>
                {e.status}
              </SeverityBadge>

              <p className="w-32 shrink-0 text-right text-[11px] text-slate-500">
                {e.nextServiceInDays > 0 ? `Service in ${e.nextServiceInDays}d` : 'Service overdue'}
              </p>
            </li>
          ))}
        </ul>
      </Card>
    </>
  );
}
