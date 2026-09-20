/** Page title block used at the top of every screen. */
export default function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-[26px] font-bold leading-tight tracking-tight text-slate-900">{title}</h1>
        {subtitle ? <p className="mt-1 text-[12.5px] text-slate-500">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}
