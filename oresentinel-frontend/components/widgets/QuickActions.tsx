'use client';

import Link from 'next/link';
import { AlertTriangle, ChevronRight, Cog, Map, ShieldCheck, TrendingUp } from 'lucide-react';
import { Card, CardHeader } from '@/components/ui/Card';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockQuickActions } from '@/data/mock';

/** Icon keys the backend can send in QuickAction.icon. */
const ICONS: Record<string, React.ElementType> = {
  map: Map,
  trending: TrendingUp,
  alert: AlertTriangle,
  gear: Cog,
  shield: ShieldCheck,
};

/**
 * Quick Actions — vertical list of shortcuts.
 *
 * TODO(api) → GET {base}{ENDPOINTS.quickActions}
 *   Expected: QuickAction[]  { id, label, icon, href }
 */
export default function QuickActions() {
  const { data: actions } = useApi(api.quickActions, mockQuickActions);

  return (
    <Card className="card-pad">
      <CardHeader title="Quick Actions" />
      <div className="mt-4 space-y-2">
        {actions.map(({ id, label, icon, href }) => {
          const Icon = ICONS[icon] ?? ChevronRight;
          return (
            <Link
              key={id}
              href={href}
              className="group flex items-center gap-2.5 rounded-lg border border-line bg-slate-50/60 px-3 py-2.5 text-[12px] font-medium text-slate-700 transition hover:border-brand/30 hover:bg-brand-light/50 hover:text-brand"
            >
              <Icon className="h-[15px] w-[15px] shrink-0 text-brand" strokeWidth={2.2} />
              <span className="flex-1 truncate">{label}</span>
              <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand" />
            </Link>
          );
        })}
      </div>
    </Card>
  );
}
