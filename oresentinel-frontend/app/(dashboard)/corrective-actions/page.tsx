'use client';

import { useState } from 'react';
import { ArrowUpRight } from 'lucide-react';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardHeader } from '@/components/ui/Card';
import { PriorityTag } from '@/components/ui/Badge';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockActions } from '@/data/mock';
import { cn } from '@/lib/utils';
import type { Priority } from '@/types';

const TABS = [
  { id: 'all', label: 'All' },
  { id: 'high', label: 'High Priority' },
  { id: 'medium', label: 'Medium' },
  { id: 'low', label: 'Low' },
] as const;

/**
 * Prescriptive Actions screen: priority tabs + ranked recommended actions
 * with estimated impact.
 *
 * TODO(api) → GET {base}{ENDPOINTS.prescriptiveActions} → PrescriptiveAction[]
 */
export default function CorrectiveActionsPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]['id']>('all');
  const { data: actions, usingFallback } = useApi(api.prescriptiveActions, mockActions);

  const shown = tab === 'all' ? actions : actions.filter((a) => a.priority === (tab as Priority));

  return (
    <>
      <PageHeader
        title="Prescriptive Actions"
        subtitle="Recommended actions to prevent shortfalls and optimize operations."
        action={<DataStateBadge show={usingFallback} />}
      />

      {/* Priority tabs */}
      <div className="mb-4 inline-flex flex-wrap gap-1 rounded-xl border border-line bg-white p-1 shadow-card">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              'rounded-lg px-3.5 py-1.5 text-[11.5px] font-medium transition',
              tab === t.id ? 'bg-brand text-white' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {shown.map((a) => (
          <Card key={a.id} className="card-pad">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-[13px] font-semibold text-slate-800">{a.title}</h3>
                  {a.site ? <span className="muted">· {a.site}</span> : null}
                </div>
                <p className="mt-1.5 max-w-3xl text-[11.5px] leading-snug text-slate-500">{a.rationale}</p>

                <div className="mt-3 inline-flex items-center gap-2 rounded-lg bg-brand-light/60 px-3 py-1.5">
                  <ArrowUpRight className="h-3.5 w-3.5 text-brand" />
                  <span className="text-[10.5px] font-medium text-slate-500">{a.impactLabel}:</span>
                  <span className="text-[11.5px] font-bold text-brand">{a.impactValue}</span>
                </div>
              </div>

              <PriorityTag priority={a.priority} />
            </div>
          </Card>
        ))}

        {shown.length === 0 ? (
          <Card className="card-pad text-center text-[12px] text-slate-500">
            No actions in this priority band.
          </Card>
        ) : null}
      </div>
    </>
  );
}
