'use client';

/**
 * Tiny honesty indicator: shows "Demo data" while the backend call has not
 * succeeded, so nobody demos mock numbers believing they are live.
 * Delete this component once every endpoint is wired.
 */
export function DataStateBadge({ show, className }: { show: boolean; className?: string }) {
  if (!show) return null;
  return (
    <span
      title="Backend not reachable — showing the bundled fixture data"
      className={`inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700 ring-1 ring-amber-200 ${className ?? ''}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
      Demo data
    </span>
  );
}
