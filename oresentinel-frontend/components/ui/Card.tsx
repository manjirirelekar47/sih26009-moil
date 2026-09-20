import { cn } from '@/lib/utils';

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return <section className={cn('card', className)}>{children}</section>;
}

export function CardHeader({
  title,
  subtitle,
  action,
  icon,
  className,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}) {
  return (
    <header className={cn('flex items-start justify-between gap-3', className)}>
      <div className="flex items-start gap-2">
        {icon ? <span className="mt-0.5 text-slate-400">{icon}</span> : null}
        <div>
          <h2 className="card-title">{title}</h2>
          {subtitle ? <p className="muted mt-0.5">{subtitle}</p> : null}
        </div>
      </div>
      {action}
    </header>
  );
}

export default Card;
