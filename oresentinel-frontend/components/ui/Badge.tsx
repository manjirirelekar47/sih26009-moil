import { cn } from '@/lib/utils';
import type { AlertSeverity, Priority } from '@/types';

const SEVERITY_STYLES: Record<AlertSeverity, string> = {
  high: 'bg-risk-highBg text-risk-high ring-risk-high/20',
  medium: 'bg-risk-medBg text-risk-med ring-risk-med/20',
  low: 'bg-risk-lowBg text-risk-low ring-risk-low/20',
};

export function SeverityBadge({
  severity,
  children,
  className,
}: {
  severity: AlertSeverity;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 text-[10.5px] font-semibold ring-1',
        SEVERITY_STYLES[severity],
        className,
      )}
    >
      {children}
    </span>
  );
}

const PRIORITY_STYLES: Record<Priority, string> = {
  high: 'bg-risk-highBg text-risk-high',
  medium: 'bg-risk-medBg text-risk-med',
  low: 'bg-risk-okBg text-risk-ok',
};

const PRIORITY_LABEL: Record<Priority, string> = {
  high: 'High Priority',
  medium: 'Medium',
  low: 'Low',
};

export function PriorityTag({ priority }: { priority: Priority }) {
  return (
    <span
      className={cn(
        'inline-flex shrink-0 items-center rounded-md px-2 py-1 text-[10.5px] font-bold',
        PRIORITY_STYLES[priority],
      )}
    >
      {PRIORITY_LABEL[priority]}
    </span>
  );
}
