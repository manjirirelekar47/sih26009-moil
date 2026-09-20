'use client';

import Link from 'next/link';
import { AlertTriangle, ArrowRight, Bell, Info, ShieldAlert } from 'lucide-react';
import { Card, CardHeader } from '@/components/ui/Card';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { cn } from '@/lib/utils';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockAlerts } from '@/data/mock';
import type { AlertSeverity } from '@/types';

const SEVERITY_META: Record<
  AlertSeverity,
  { Icon: React.ElementType; ring: string; icon: string }
> = {
  high: { Icon: ShieldAlert, ring: 'bg-risk-highBg', icon: 'text-risk-high' },
  medium: { Icon: AlertTriangle, ring: 'bg-risk-medBg', icon: 'text-risk-med' },
  low: { Icon: Info, ring: 'bg-risk-lowBg', icon: 'text-risk-low' },
};

/**
 * Active Alerts list — severity icon + text + relative timestamp.
 *
 * TODO(api) → GET {base}{ENDPOINTS.activeAlerts}
 *   Expected: Alert[]  where createdAt is an ISO-8601 string.
 */
export default function ActiveAlerts() {
  const { data: alerts, usingFallback } = useApi(api.activeAlerts, mockAlerts);

  return (
    <Card className="card-pad flex flex-col">
      <CardHeader
        title="Active Alerts"
        icon={<Bell className="h-4 w-4" />}
        action={
          <div className="flex items-center gap-2">
            <DataStateBadge show={usingFallback} />
            <Link
              href="/shortfall-prediction"
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-brand hover:underline"
            >
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        }
      />

      <ul className="mt-4 divide-y divide-line">
        {alerts.map((alert) => {
          const { Icon, ring, icon } = SEVERITY_META[alert.severity];
          return (
            <li key={alert.id} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
              <span className={cn('mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full', ring)}>
                <Icon className={cn('h-[15px] w-[15px]', icon)} strokeWidth={2.2} />
              </span>
              <div className="min-w-0 flex-1">
                <Link
                  href={alert.href ?? '#'}
                  className="block text-[12.5px] font-semibold text-slate-800 hover:text-brand"
                >
                  {alert.title}
                </Link>
                <p className="mt-0.5 text-[11px] leading-snug text-slate-500">{alert.description}</p>
              </div>
              <span className="shrink-0 whitespace-nowrap text-[10.5px] text-slate-400">
                {/* Backend may already send "2h ago" — then render it as-is. */}
                {alert.createdAt.includes('ago') ? alert.createdAt : timeAgo(alert.createdAt)}
              </span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.max(1, Math.round(diff / 60000));
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}
