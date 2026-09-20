'use client';

import { useEffect, useRef, useState } from 'react';
import { Bell, ChevronDown, LogOut, Search, Settings, User } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Top header: global search · notification bell · profile dropdown.
 * The script line "Manganese for a stronger India" sits on the right of the
 * search bar in the mockup; it is decorative, so it is hidden below lg.
 */
export default function Header() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const menuRef = useRef<HTMLDivElement>(null);

  // Close the profile dropdown on outside click / Escape.
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, []);

  function onSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    // TODO(api): wire to your global search endpoint, e.g.
    //   GET /api/search?q=...  ->  { type: 'mine'|'report'|'location', id, label }[]
    // then router.push(`/...`) based on the result type.
    console.info('[OreSentinel] search query:', query);
  }

  return (
    <header className="sticky top-0 z-30 flex h-[var(--header-h)] items-center gap-4 border-b border-line bg-white px-6">
      {/* Global search */}
      <form onSubmit={onSearchSubmit} className="relative w-full max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-[15px] w-[15px] -translate-y-1/2 text-slate-400" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          type="search"
          placeholder="Search mine, location, or report..."
          aria-label="Search mine, location, or report"
          className="h-10 w-full rounded-lg border border-line bg-slate-50 pl-9 pr-3 text-[12.5px] text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-brand/40 focus:bg-white focus:ring-2 focus:ring-brand/10"
        />
      </form>

      {/* Decorative tagline from the mockup */}
      <p className="ml-auto hidden font-script text-[19px] leading-none text-slate-400 xl:block">
        Manganese for a stronger India
      </p>

      {/* Notification bell */}
      <button
        type="button"
        aria-label="Notifications"
        className="relative ml-auto flex h-10 w-10 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 xl:ml-0"
      >
        <Bell className="h-[18px] w-[18px]" />
        <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-risk-high ring-2 ring-white" />
      </button>

      {/* Profile dropdown */}
      <div ref={menuRef} className="relative">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-haspopup="menu"
          aria-expanded={open}
          className="flex items-center gap-2.5 rounded-lg py-1.5 pl-1.5 pr-2 transition hover:bg-slate-100"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand text-[11.5px] font-bold text-white">
            SP
          </span>
          <span className="hidden text-left leading-tight sm:block">
            <span className="block text-[12.5px] font-semibold text-slate-800">Samiksha Patil</span>
            <span className="block text-[10.5px] text-slate-500">Analyst</span>
          </span>
          <ChevronDown
            className={cn('h-4 w-4 text-slate-400 transition-transform', open && 'rotate-180')}
          />
        </button>

        {open && (
          <div
            role="menu"
            className="absolute right-0 top-[calc(100%+6px)] w-56 animate-fade-up rounded-xl border border-line bg-white p-1.5 shadow-lg"
          >
            <div className="border-b border-line px-3 py-2">
              <p className="text-[12.5px] font-semibold text-slate-800">Samiksha Patil</p>
              <p className="text-[10.5px] text-slate-500">samiksha.patil@moil.nic.in</p>
            </div>
            {[
              { label: 'Profile', icon: User },
              { label: 'Preferences', icon: Settings },
            ].map(({ label, icon: Icon }) => (
              <button
                key={label}
                role="menuitem"
                type="button"
                className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[12.5px] text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
            <button
              role="menuitem"
              type="button"
              className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[12.5px] text-risk-high transition hover:bg-risk-highBg/50"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
