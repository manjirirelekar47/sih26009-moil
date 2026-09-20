'use client';

import { cn } from '@/lib/utils';
import type { LayerKey, LayerToggle } from '@/types';

/**
 * Reserve Mapping → Layer Controls panel (toggles list).
 *
 * TODO(api) → when a toggle flips, fetch that layer's raster tiles:
 *   GET {base}{ENDPOINTS.layerTiles} with {layer} = the LayerKey
 *   e.g. /api/reserves/layers/ndvi  ->  { tileUrl, attribution }
 */
export default function LayerControls({
  layers,
  active,
  onToggle,
}: {
  layers: LayerToggle[];
  active: LayerKey[];
  onToggle: (key: LayerKey) => void;
}) {
  return (
    <div className="card card-pad">
      <h3 className="card-title">Layer Controls</h3>
      <ul className="mt-3 space-y-2.5">
        {layers.map((l) => {
          const on = active.includes(l.key);
          return (
            <li key={l.key}>
              <button
                type="button"
                role="switch"
                aria-checked={on}
                onClick={() => onToggle(l.key)}
                className="flex w-full items-center justify-between gap-3 rounded-lg px-2 py-1.5 text-left transition hover:bg-slate-50"
              >
                <span className={cn('text-[11.5px]', on ? 'font-semibold text-slate-800' : 'text-slate-600')}>
                  {l.label}
                </span>
                <span
                  className={cn(
                    'relative h-4 w-7 shrink-0 rounded-full transition-colors',
                    on ? 'bg-brand' : 'bg-slate-200',
                  )}
                >
                  <span
                    className={cn(
                      'absolute top-0.5 h-3 w-3 rounded-full bg-white shadow transition-all',
                      on ? 'left-[15px]' : 'left-0.5',
                    )}
                  />
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
