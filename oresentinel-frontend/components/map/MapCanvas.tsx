'use client';

import { useEffect, useRef } from 'react';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { LayerKey, MineMarker, ReserveZone } from '@/types';
import { reserveColor } from '@/data/mock';

/**
 * Real Mapbox GL canvas. Loaded ONLY via next/dynamic with { ssr: false }
 * (see ReserveMap.tsx) because mapbox-gl touches `window` on import.
 *
 * TODO(api) — data sources:
 *   markers → GET {base}{ENDPOINTS.mineMarkers}
 *   zones   → GET {base}{ENDPOINTS.reserveZones}
 *   raster  → GET {base}{ENDPOINTS.layerTiles} with {layer} replaced by the
 *             active LayerKey (e.g. /api/reserves/layers/ndvi) — return a
 *             { tileUrl, attribution } object and add it as a raster source.
 */
export default function MapCanvas({
  token,
  styleUrl,
  markers,
  zones,
  activeLayers,
  showBoundary,
  showLabels,
}: {
  token: string;
  styleUrl: string;
  markers: MineMarker[];
  zones: ReserveZone[];
  activeLayers: LayerKey[];
  showBoundary: boolean;
  showLabels: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);

  // Init once.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const mapboxgl = (await import('mapbox-gl')).default;
      if (cancelled || !containerRef.current || mapRef.current) return;

      mapboxgl.accessToken = token;
      const map = new mapboxgl.Map({
        container: containerRef.current,
        style: styleUrl,
        center: [79.4, 21.45],
        zoom: 8.6,
        attributionControl: false,
      });
      mapRef.current = map;

      map.on('load', () => {
        // Reserve zone polygons
        map.addSource('reserve-zones', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: zones.map((z) => ({
              type: 'Feature',
              properties: { color: reserveColor(z.prospectivity), name: z.name },
              geometry: { type: 'Polygon', coordinates: [z.coordinates] },
            })),
          },
        });
        map.addLayer({
          id: 'reserve-zones-fill',
          type: 'fill',
          source: 'reserve-zones',
          paint: { 'fill-color': ['get', 'color'], 'fill-opacity': 0.45 },
        });
        map.addLayer({
          id: 'reserve-zones-outline',
          type: 'line',
          source: 'reserve-zones',
          paint: { 'line-color': ['get', 'color'], 'line-width': 1.2 },
        });
      });
    })();

    return () => {
      cancelled = true;
      mapRef.current?.remove?.();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, styleUrl]);

  // Sync markers whenever data changes.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const mapboxgl = (await import('mapbox-gl')).default;
      const map = mapRef.current;
      if (cancelled || !map) return;

      // Remove previous markers, then re-add.
      (map.__markers ?? []).forEach((m: any) => m.remove());
      map.__markers = markers.map((mk) => {
        const el = document.createElement('div');
        el.style.cssText = `width:14px;height:14px;border-radius:9999px;border:2px solid #fff;
          box-shadow:0 1px 4px rgba(0,0,0,.35);background:${reserveColor(mk.prospectivity)}`;
        const marker = new mapboxgl.Marker({ element: el })
          .setLngLat([mk.lng, mk.lat])
          .addTo(map);
        if (showLabels) {
          marker.setPopup(
            new mapboxgl.Popup({ offset: 14, closeButton: false }).setHTML(
              `<strong style="font-size:12px">${mk.name}</strong><br/>
               <span style="font-size:11px;color:#64748B">${mk.prospectivity} Mt/ha</span>`,
            ),
          );
        }
        return marker;
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [markers, showLabels]);

  // Sync the Mine Boundary visibility toggle.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer?.('reserve-zones-fill')) return;
    const v = showBoundary ? 'visible' : 'none';
    map.setLayoutProperty('reserve-zones-fill', 'visibility', v);
    map.setLayoutProperty('reserve-zones-outline', 'visibility', v);
  }, [showBoundary]);

  // Layer toggles: NDVI / soil moisture / land temperature etc.
  // TODO(api): fetch a raster tile URL per layer and add it as a raster source.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    console.info('[OreSentinel] active map layers:', activeLayers);
  }, [activeLayers]);

  return <div ref={containerRef} className="h-full w-full" />;
}
