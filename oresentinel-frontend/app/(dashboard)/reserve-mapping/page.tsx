'use client';

import { useState } from 'react';
import { Database, Layers, Satellite, Sparkles } from 'lucide-react';
import PageHeader from '@/components/layout/PageHeader';
import ReserveMap from '@/components/map/ReserveMap';
import LayerControls from '@/components/map/LayerControls';
import { Card } from '@/components/ui/Card';
import { DataStateBadge } from '@/components/ui/DataStateBadge';
import { useApi } from '@/lib/useApi';
import { api } from '@/lib/api';
import { mockLayerToggles, mockMineMarkers, mockReserveInsights, mockReserveZones } from '@/data/mock';
import { fmt } from '@/lib/utils';
import type { LayerKey } from '@/types';

/**
 * Reserve Mapping screen: map + Layer Controls rail + "Key Insights" strip.
 *
 * TODO(api) → GET {base}{ENDPOINTS.reserveInsights}  → ReserveMappingInsights
 *             GET {base}{ENDPOINTS.layerTiles}?layer={LayerKey} → raster tiles
 */
export default function ReserveMappingPage() {
  const [active, setActive] = useState<LayerKey[]>(
    mockLayerToggles.filter((l) => l.defaultOn).map((l) => l.key),
  );

  const { data: markers, usingFallback } = useApi(api.mineMarkers, mockMineMarkers);
  const { data: zones } = useApi(api.reserveZones, mockReserveZones);
  const { data: insights } = useApi(api.reserveInsights, mockReserveInsights);

  const toggle = (key: LayerKey) =>
    setActive((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));

  // NOTE: totalReservesMt and surveyDeltaPct are null because the pipeline has
  // no reserve-tonnage column and only one survey. They render as "N/A" rather
  // than a fabricated number.
  const stats = [
    {
      icon: Database,
      label: 'High-prospectivity zones',
      value: `${insights.newZones} / ${insights.zonesScored ?? '—'}`,
    },
    {
      icon: Sparkles,
      label: 'Reserve tonnage',
      value: insights.totalReservesMt === null ? 'N/A' : `${fmt(insights.totalReservesMt)} Mt`,
    },
    {
      icon: Layers,
      label: 'Mineralised observations',
      value: `${insights.mineralizedObservations ?? '—'}`,
    },
    {
      icon: Satellite,
      label: 'Label source',
      value: (insights.labelSource ?? []).join(', ') || '—',
    },
  ];

  return (
    <>
      <PageHeader
        title="Reserve Mapping"
        subtitle="Explore surface and sub-surface manganese reserves using satellite and geological data."
        action={<DataStateBadge show={usingFallback} />}
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <div className="xl:col-span-9">
          <Card className="card-pad">
            <div className="overflow-hidden rounded-xl" style={{ height: 520 }}>
              <ReserveMap markers={markers} zones={zones} activeLayers={active} showToggles={false} />
            </div>
          </Card>

          {/* Key Insights strip */}
          <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
            {stats.map(({ icon: Icon, label, value }) => (
              <Card key={label} className="card-pad">
                <Icon className="h-4 w-4 text-brand" strokeWidth={2.2} />
                <p className="mt-2.5 text-[20px] font-extrabold leading-none text-slate-900">{value}</p>
                <p className="mt-1.5 text-[11px] leading-tight text-slate-500">{label}</p>
              </Card>
            ))}
          </div>
        </div>

        <div className="xl:col-span-3">
          <LayerControls layers={mockLayerToggles} active={active} onToggle={toggle} />
        </div>
      </div>
    </>
  );
}
