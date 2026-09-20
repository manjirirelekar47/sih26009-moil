'use client';

import KpiCard from './KpiCard';
import { Skeleton } from '@/components/ui/Skeleton';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockKpis } from '@/data/mock';

/**
 * KPI summary row — 5 cards.
 *
 * TODO(api) → GET {NEXT_PUBLIC_API_BASE_URL}{ENDPOINTS.dashboardKpis}
 *   Expected: Kpi[]  (see types/index.ts)
 *   e.g. [{ id:'reserves', label:'Total Estimated Reserves', value:245.6,
 *           unit:'Mt', deltaPct:12, trend:'up', footnote:'vs last survey' }, ...]
 */
export default function KpiRow() {
  const { data: kpis, loading, usingFallback } = useApi(api.dashboardKpis, mockKpis);

  if (loading && kpis === mockKpis) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-[132px] rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {kpis.map((kpi) => (
        <KpiCard key={kpi.id} kpi={kpi} usingFallback={usingFallback} />
      ))}
    </div>
  );
}
