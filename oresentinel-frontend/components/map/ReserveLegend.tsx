import { PROSPECTIVITY_LEGEND } from '@/data/mock';

/**
 * Floating legend.
 *
 * IMPORTANT (honesty): the prototype's zone_scores.csv stores a unitless
 * `prospectivity_score` between 0 and 1 — there is NO reserve tonnage per
 * hectare in the data. The original mockup legend ("Estimated Reserve, Mt per
 * ha") would therefore be showing a unit that does not exist. This legend says
 * what the number actually is.
 */
export default function ReserveLegend() {
  return (
    <div className="absolute bottom-3 right-3 w-[196px] rounded-lg border border-white/15 bg-ink/85 p-2.5 backdrop-blur">
      <p className="mb-1.5 text-[10px] font-semibold text-white">
        Prospectivity score <span className="font-normal text-white/60">(0&ndash;1, model output)</span>
      </p>
      <ul className="space-y-1">
        {PROSPECTIVITY_LEGEND.map((l) => (
          <li key={l.label} className="flex items-center gap-2 text-[10px] text-white/80">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: l.color }} />
            {l.label}
          </li>
        ))}
      </ul>
      <p className="mt-1.5 border-t border-white/10 pt-1 text-[9px] leading-tight text-white/45">
        Not reserve tonnage &mdash; no Mt/ha field exists in the pipeline.
      </p>
    </div>
  );
}
