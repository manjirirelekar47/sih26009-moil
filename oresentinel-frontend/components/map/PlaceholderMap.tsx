'use client';

import { MapPin } from 'lucide-react';
import { reserveColor } from '@/data/mock';
import type { MineMarker, ReserveZone } from '@/types';

/**
 * Token-free fallback map. Renders the same reserve zones and Mine A–D
 * markers as an SVG using a simple equirectangular projection, so the
 * dashboard is fully demoable before NEXT_PUBLIC_MAPBOX_TOKEN is set.
 */
export default function PlaceholderMap({
  markers,
  zones,
  showBoundary,
  showLabels,
}: {
  markers: MineMarker[];
  zones: ReserveZone[];
  showBoundary: boolean;
  showLabels: boolean;
}) {
  const all = [
    ...zones.flatMap((z) => z.coordinates),
    ...markers.map((m) => [m.lng, m.lat] as [number, number]),
  ];
  const lngs = all.map((c) => c[0]);
  const lats = all.map((c) => c[1]);
  const pad = 0.06;
  const minLng = Math.min(...lngs) - pad;
  const maxLng = Math.max(...lngs) + pad;
  const minLat = Math.min(...lats) - pad;
  const maxLat = Math.max(...lats) + pad;

  const px = (lng: number) => ((lng - minLng) / (maxLng - minLng)) * 100;
  const py = (lat: number) => 100 - ((lat - minLat) / (maxLat - minLat)) * 100;

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#243B33]">
      {/* Terrain wash */}
      <div className="absolute inset-0 opacity-90"
        style={{
          background:
            'radial-gradient(60% 55% at 30% 25%, #4E6B4A 0%, transparent 60%),' +
            'radial-gradient(55% 50% at 75% 70%, #6B5A3E 0%, transparent 62%),' +
            'radial-gradient(45% 45% at 55% 40%, #3E5C50 0%, transparent 65%),' +
            'linear-gradient(160deg, #2C4239 0%, #1D3029 100%)',
        }}
      />
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
        {zones.map((z) => {
          const pts = z.coordinates.map(([lng, lat]) => `${px(lng)},${py(lat)}`).join(' ');
          const c = reserveColor(z.prospectivity);
          return (
            <g key={z.id}>
              {showBoundary ? (
                <polygon points={pts} fill={c} fillOpacity={0.42} stroke={c} strokeWidth={0.35} />
              ) : null}
            </g>
          );
        })}
      </svg>

      {/* Mine markers */}
      {markers.map((m) => (
        <div
          key={m.id}
          className="absolute -translate-x-1/2 -translate-y-1/2"
          style={{ left: `${px(m.lng)}%`, top: `${py(m.lat)}%` }}
        >
          <span
            className="flex h-3.5 w-3.5 items-center justify-center rounded-full ring-2 ring-white/90"
            style={{ background: reserveColor(m.prospectivity) }}
            title={`${m.name} — ${m.prospectivity} Mt/ha`}
          />
          {showLabels ? (
            <span className="absolute left-1/2 top-full mt-1 flex -translate-x-1/2 items-center gap-1 whitespace-nowrap rounded-md bg-ink/85 px-1.5 py-0.5 text-[9.5px] font-medium text-white backdrop-blur">
              <MapPin className="h-2.5 w-2.5" />
              {m.name}
            </span>
          ) : null}
        </div>
      ))}

      <p className="absolute left-3 top-3 rounded-md bg-black/35 px-2 py-1 text-[9.5px] font-medium text-white/80 backdrop-blur">
        Add NEXT_PUBLIC_MAPBOX_TOKEN for the live satellite view
      </p>
    </div>
  );
}
