'use client';

import { FileText, Download } from 'lucide-react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockKpis } from '@/data/mock';
import { fmt } from '@/lib/utils';

/**
 * Reports screen — a scaffolded placeholder.
 *
 * TODO(api) → GET {base}{ENDPOINTS.reports}
 *   Expected: { id, title, period, generatedAt, downloadUrl }[]
 *   The table below currently renders the live KPI set as a stand-in summary.
 */
export default function ReportsPage() {
  const { data: kpis, usingFallback } = useApi(api.dashboardKpis, mockKpis);

  return (
    <>
      <PageHeader
        title="Reports"
        subtitle="Exportable summaries for review meetings and statutory filings."
        action={<DataStateBadge show={usingFallback} />}
      />

      <Card className="card-pad">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-brand" />
          <h2 className="card-title">Current period summary</h2>
        </div>

        <table className="mt-4 w-full text-left">
          <thead>
            <tr className="border-b border-line text-[10.5px] uppercase tracking-wide text-slate-400">
              <th className="pb-2 font-semibold">Metric</th>
              <th className="pb-2 font-semibold">Value</th>
              <th className="pb-2 font-semibold">Change</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {kpis.map((k) => (
              <tr key={k.id} className="text-[12px]">
                <td className="py-3 text-slate-600">{k.label}</td>
                <td className="py-3 font-semibold text-slate-800">
                  {k.value === null || k.value === undefined
                    ? 'N/A'
                    : `${fmt(k.value, Number.isInteger(k.value) ? 0 : 1)} ${k.unit}`}
                </td>
                <td className="py-3 text-slate-500">
                  {k.deltaPct !== undefined ? `${k.deltaPct > 0 ? '+' : ''}${k.deltaPct}%` : (k.footnote ?? '—')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <button
          type="button"
          disabled
          title="Wire ENDPOINTS.reports to enable export"
          className="mt-5 inline-flex cursor-not-allowed items-center gap-2 rounded-lg bg-slate-100 px-3.5 py-2 text-[11.5px] font-semibold text-slate-400"
        >
          <Download className="h-3.5 w-3.5" />
          Export PDF (connect ENDPOINTS.reports)
        </button>
      </Card>
    </>
  );
}
