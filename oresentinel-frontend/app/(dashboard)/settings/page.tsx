'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardHeader } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

/** Settings screen — local UI state only until ENDPOINTS.settings is wired. */
export default function SettingsPage() {
  const [prefs, setPrefs] = useState({
    alertEmails: true,
    pushNotifications: false,
    weeklyDigest: true,
    autoRefresh: true,
  });

  const rows: { key: keyof typeof prefs; label: string; note: string }[] = [
    { key: 'alertEmails', label: 'Email alerts', note: 'Critical shortfall and equipment alerts' },
    { key: 'pushNotifications', label: 'Push notifications', note: 'Browser push for high-severity events' },
    { key: 'weeklyDigest', label: 'Weekly digest', note: 'Monday summary of production vs target' },
    { key: 'autoRefresh', label: 'Auto-refresh dashboard', note: 'Re-fetch widget data every 5 minutes' },
  ];

  return (
    <>
      <PageHeader
        title="Settings"
        subtitle="Notification and data preferences for your analyst account."
      />

      <Card className="card-pad max-w-2xl">
        <CardHeader title="Preferences" />
        <ul className="mt-4 divide-y divide-line">
          {rows.map((r) => {
            const on = prefs[r.key];
            return (
              <li key={r.key} className="flex items-center justify-between gap-4 py-3.5 first:pt-0 last:pb-0">
                <div>
                  <p className="text-[12.5px] font-medium text-slate-800">{r.label}</p>
                  <p className="muted mt-0.5">{r.note}</p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={on}
                  aria-label={r.label}
                  onClick={() => setPrefs((p) => ({ ...p, [r.key]: !p[r.key] }))}
                  className={cn(
                    'relative h-5 w-9 shrink-0 rounded-full transition-colors',
                    on ? 'bg-brand' : 'bg-slate-200',
                  )}
                >
                  <span
                    className={cn(
                      'absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all',
                      on ? 'left-[18px]' : 'left-0.5',
                    )}
                  />
                </button>
              </li>
            );
          })}
        </ul>

        <p className="mt-5 rounded-lg bg-slate-50 p-3 text-[11px] leading-relaxed text-slate-500">
          {/* TODO(api): persist with PUT {base}{ENDPOINTS.settings} */}
          TODO(api): persist these preferences via <code>PUT</code> to{' '}
          <code>{'{base}'}{'{ENDPOINTS.settings}'}</code>.
        </p>
      </Card>
    </>
  );
}
