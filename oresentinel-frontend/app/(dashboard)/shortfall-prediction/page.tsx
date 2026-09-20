'use client';

import { AlertTriangle } from 'lucide-react';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardHeader } from '@/components/ui/Card';
import { SeverityBadge } from '@/components/ui/Badge';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockAlerts, mockMineMarkers } from '@/data/mock';

/**
 * Shortfall Prediction screen: per-mine risk table + the risk feed.
 *
 * TODO(api) → GET {base}{ENDPOINTS.shortfallRisk} → Alert[] (or a richer
 *   ShortfallPrediction[] — extend types/index.ts if so).
 */
export default function ShortfallPredictionPage() {
  const { data: risks, usingFallback } = useApi(api.shortfallRisk, mockAlerts);
  const { data: mines } = useApi(api.mineMarkers, mockMineMarkers);

  return (
    <>
      <PageHeader
        title="Shortfall Prediction"
        subtitle="Predicted production gaps by mine, ranked by likelihood and impact."
        action={<DataStateBadge show={usingFallback} />}
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <div className="xl:col-span-7">
          <Card className="card-pad">
            <CardHeader title="Mine-level risk" />
            <table className="mt-4 w-full text-left">
              <thead>
                <tr className="border-b border-line text-[10.5px] uppercase tracking-wide text-slate-400">
                  <th className="pb-2 font-semibold">Mine</th>
                  <th className="pb-2 font-semibold">Reserve (Mt/ha)</th>
                  <th className="pb-2 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {mines.map((m) => (
                  <tr key={m.id} className="text-[12px]">
                    <td className="py-3 font-semibold text-slate-800">{m.name}</td>
                    <td className="py-3 text-slate-600">{m.prospectivity}</td>
                    <td className="py-3">
                      <SeverityBadge
                        severity={
                          m.status === 'warning' ? 'high' : m.status === 'inspection' ? 'medium' : 'low'
                        }
                      >
                        {m.status}
                      </SeverityBadge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>

        <div className="space-y-4 xl:col-span-5">
          {risks.map((r) => (
            <Card key={r.id} className="card-pad">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-risk-highBg">
                  <AlertTriangle className="h-4 w-4 text-risk-high" strokeWidth={2.2} />
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-[12.5px] font-semibold text-slate-800">{r.title}</h3>
                    <SeverityBadge severity={r.severity}>{r.severity}</SeverityBadge>
                  </div>
                  <p className="mt-1 text-[11.5px] leading-snug text-slate-500">{r.description}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </>
  );
}
