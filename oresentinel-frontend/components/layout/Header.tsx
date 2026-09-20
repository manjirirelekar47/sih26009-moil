/**
 * Top header. It only shows things that work: the tagline and a data-provenance note.
 * Removed on purpose: the global search, the notification bell and the profile menu.
 * None of them were connected to anything (the profile was a hard-coded name).
 */
export default function Header() {
  return (
    <header className="sticky top-0 z-30 flex h-[var(--header-h)] items-center gap-4 border-b border-line bg-white px-6">
      <p className="hidden font-script text-[19px] leading-none text-slate-400 md:block">
        Manganese for a stronger India
      </p>
      <p className="ml-auto rounded-full border border-line bg-slate-50 px-3 py-1 text-[11px] font-medium text-slate-500">
        Satellite data: real · Mine logs: synthetic
      </p>
    </header>
  );
}
