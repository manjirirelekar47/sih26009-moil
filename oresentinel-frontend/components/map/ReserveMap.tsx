'use client';

import dynamic from 'next/dynamic';
import { useMemo, useState } from 'react';
import { Layers, MapPin } from 'lucide-react';
import PlaceholderMap from './PlaceholderMap';
import ReserveLegend from './ReserveLegend';
import { cn } from '@/lib/utils';
import type { LayerKey, MineMarker, ReserveZone } from '@/types';

/**
 * mapbox-gl is browser-only, so the real canvas is code-split and never
 * server-rendered. Without a token the app silently falls back to the
 * SVG placeholder — the build and the demo keep working either way.
 */
const MapCanvas = dynamic(() => import('./MapCanvas'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center bg-slate-100 text-[11px] text-slate-400">
      Loading map…
    </div>
  ),
});

export type MapViewMode = 'surface' | 'subsurface';

export default function ReserveMap({
  markers,
  zones,
  activeLayers,
  viewMode = 'surface',
  className,
  showLegend = true,
  showToggles = true,
}: {
  markers: MineMarker[];
  zones: ReserveZone[];
  activeLayers: LayerKey[];
  viewMode?: MapViewMode;
  className?: string;
  showLegend?: boolean;
  showToggles?: boolean;
}) {
  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? '';
  const styleUrl = process.env.NEXT_PUBLIC_MAP_STYLE ?? 'mapbox://styles/mapbox/satellite-streets-v12';

  const [showBoundary, setShowBoundary] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  // Sub-surface view greys the surface colouring to read as a cross-section.
  const zonesForView = useMemo(
    () =>
      viewMode === 'subsurface'
        ? zones.map((z) => ({ ...z, prospectivity: z.prospectivity * 0.75 }))
        : zones,
    [zones, viewMode],
  );

  return (
    <div className={cn('relative h-full w-full overflow-hidden rounded-xl', className)}>
      {token ? (
        <MapCanvas
          token={token}
          styleUrl={styleUrl}
          markers={markers}
          zones={zonesForView}
          activeLayers={activeLayers}
          showBoundary={showBoundary}
          showLabels={showLabels}
        />
      ) : (
        <PlaceholderMap
          markers={markers}
          zones={zonesForView}
          showBoundary={showBoundary}
          showLabels={showLabels}
        />
      )}

      {/* Zoom affordance (visual parity with the mockup) */}
      <div className="absolute left-3 top-1/2 flex -translate-y-1/2 flex-col overflow-hidden rounded-lg border border-white/15 bg-white/90 backdrop-blur">
        <button type="button" aria-label="Zoom in" className="px-2 py-1 text-[13px] font-bold text-slate-600 hover:bg-slate-100">+</button>
        <span className="h-px w-full bg-line" />
        <button type="button" aria-label="Zoom out" className="px-2 py-1 text-[13px] font-bold text-slate-600 hover:bg-slate-100">−</button>
      </div>

      {showLegend ? <ReserveLegend /> : null}

      {showToggles ? (
        <div className="absolute bottom-3 left-3 space-y-1.5 rounded-lg border border-white/15 bg-ink/85 p-2.5 backdrop-blur">
          <p className="mb-0.5 flex items-center gap-1.5 text-[10px] font-semibold text-white">
            <Layers className="h-3 w-3" /> Overlays
          </p>
          <MapCheckbox label="Mine Boundary" checked={showBoundary} onChange={setShowBoundary} />
          <MapCheckbox label="Key Locations" checked={showLabels} onChange={setShowLabels} icon />
        </div>
      ) : null}
    </div>
  );
}

function MapCheckbox({
  label,
  checked,
  onChange,
  icon,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  icon?: boolean;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-1.5 text-[10px] text-white/85">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-3 w-3 accent-brand-mid"
      />
      {icon ? <MapPin className="h-2.5 w-2.5 text-white/60" /> : null}
      {label}
    </label>
  );
}
