'use client';

import { useState } from 'react';
import { Info } from 'lucide-react';
import ReserveMap, { type MapViewMode } from './ReserveMap';
import { Card } from '@/components/ui/Card';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { cn } from '@/lib/utils';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockMineMarkers, mockReserveZones } from '@/data/mock';
import type { LayerKey } from '@/types';

/**
 * "Manganese Reserve Map" dashboard widget:
 * header + Surface/Sub-surface toggle, then the map with legend + overlays.
 *
 * TODO(api) → markers: GET {base}{ENDPOINTS.mineMarkers}
 *             zones:   GET {base}{ENDPOINTS.reserveZones}
 */
export default function ReserveMapCard({ height = 380 }: { height?: number }) {
  const [view, setView] = useState<MapViewMode>('surface');

  const { data: markers, usingFallback } = useApi(api.mineMarkers, mockMineMarkers);
  const { data: zones } = useApi(api.reserveZones, mockReserveZones);

  // Overlays currently on (boundary + key locations are handled inside the map).
  const activeLayers: LayerKey[] = ['estimatedReserves', 'mineBoundary', 'satelliteImagery'];

  return (
    <Card className="card-pad flex flex-col">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <h2 className="card-title">Manganese Reserve Map</h2>
          <Info className="h-3.5 w-3.5 text-slate-300" />
          <DataStateBadge show={usingFallback} />
        </div>

        <div className="seg-group">
          {(
            [
              { id: 'surface', label: 'Surface View' },
              { id: 'subsurface', label: 'Sub-surface View' },
            ] as const
          ).map((v) => (
            <button
              key={v.id}
              type="button"
              onClick={() => setView(v.id)}
              className={cn('seg-item', view === v.id && 'seg-item-active')}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 overflow-hidden rounded-xl" style={{ height }}>
        <ReserveMap markers={markers} zones={zones} activeLayers={activeLayers} viewMode={view} />
      </div>
    </Card>
  );
}
