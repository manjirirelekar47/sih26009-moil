'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Activity,
  AlertTriangle,
  ClipboardList,
  CloudRain,
  FileText,
  LayoutDashboard,
  Map,
  Settings,
  ShieldCheck,
  TrendingUp,
  Wrench,
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Navigation items — the single source of truth for both the sidebar and
 * the folder structure under app/(dashboard)/.
 * `icon` values are React components, so adding a route = adding one entry.
 */
export const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/reserve-mapping', label: 'Reserve Mapping', icon: Map },
  { href: '/production-forecast', label: 'Production Forecast', icon: TrendingUp },
  { href: '/shortfall-prediction', label: 'Shortfall Prediction', icon: AlertTriangle },
  { href: '/weather-environment', label: 'Weather & Environment', icon: CloudRain },
  { href: '/equipment-health', label: 'Equipment Health', icon: Wrench },
  { href: '/corrective-actions', label: 'Corrective Actions', icon: ClipboardList },
  { href: '/reports', label: 'Reports', icon: FileText },
  { href: '/settings', label: 'Settings', icon: Settings },
] as const;

/** OreSentinel wordmark: badge + name + tagline. */
function Logo() {
  return (
    <div className="flex items-center gap-2.5 px-1">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand/20 ring-1 ring-brand-mid/40">
        <ShieldCheck className="h-[18px] w-[18px] text-brand-mid" strokeWidth={2.2} />
      </span>
      <div className="leading-tight">
        <p className="text-[15px] font-extrabold tracking-tight text-white">
          Ore<span className="text-brand-mid">Sentinel</span>
        </p>
        <p className="text-[8.5px] font-semibold uppercase tracking-[0.14em] text-white/45">
          Smart Mines, Stronger Tomorrow
        </p>
      </div>
    </div>
  );
}

/** Bottom card: MOIL Limited / Ministry of Steel / Govt. of India. */
function MinistryCard() {
  return (
    <div className="mt-4 rounded-xl border border-white/10 bg-ink-deep/80 p-3">
      <div className="flex items-start gap-2.5">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/10">
          <Activity className="h-4 w-4 text-brand-mid" strokeWidth={2.4} />
        </span>
        <div className="leading-snug">
          <p className="text-[11.5px] font-bold text-white">MOIL Limited</p>
          <p className="text-[9.5px] text-white/55">Ministry of Steel</p>
          <p className="text-[9.5px] text-white/40">Govt. of India</p>
        </div>
      </div>
    </div>
  );
}

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-[var(--sidebar-w)] flex-col bg-ink">
      <div className="px-4 pb-4 pt-5">
        <Logo />
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-2">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className={cn('nav-item', active && 'nav-item-active')}
            >
              <Icon className="h-[16px] w-[16px] shrink-0" strokeWidth={2} />
              <span className="truncate">{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-4">
        <MinistryCard />
      </div>
    </aside>
  );
}
