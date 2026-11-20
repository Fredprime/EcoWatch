import { useEffect, useMemo, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { FeatureCollection } from 'geojson';
import { allPositions, type WktFeature } from './wkt';

interface WktMapProps {
  features: WktFeature[];
  skipped: number;
  emptyNote: string;
  ariaLabel: string;
}

/**
 * Renders only stored WKT geometry on a locally built blank style (ADR-038).
 * There is no tile source, basemap URL, API key or external request. The
 * accessible list/detail view for the same records stays on the page.
 */
export function WktMap({ features, skipped, emptyNote, ariaLabel }: WktMapProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [failed, setFailed] = useState(false);
  const positions = useMemo(
    () => features.flatMap((feature) => allPositions(feature.geometry)),
    [features],
  );

  useEffect(() => {
    const host = hostRef.current;
    if (!host || features.length === 0) return;
    setFailed(false);

    const styles = getComputedStyle(document.documentElement);
    const token = (name: string, fallback: string) => styles.getPropertyValue(name).trim() || fallback;
    const background = token('--color-surface-alt', '#e9eee8');
    const accent = token('--color-accent', '#1f6f8b');

    const configuredStyleUrl = import.meta.env.VITE_MAP_STYLE_URL?.trim();
    let map: maplibregl.Map | null = null;
    try {
      map = new maplibregl.Map({
        container: host,
        style: configuredStyleUrl || {
          version: 8 as const,
          sources: {},
          layers: [
            { id: 'background', type: 'background', paint: { 'background-color': background } },
          ],
        },
        attributionControl: false,
      });
    } catch {
      setFailed(true);
      return;
    }
    const activeMap = map;
    activeMap.on('error', () => setFailed(true));
    activeMap.on('load', () => {
      activeMap.addSource('stored-geometry', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features } as unknown as FeatureCollection,
      });
      activeMap.addLayer({
        id: 'stored-areas',
        type: 'fill',
        source: 'stored-geometry',
        filter: ['match', ['geometry-type'], ['Polygon', 'MultiPolygon'], true, false],
        paint: { 'fill-color': accent, 'fill-opacity': 0.25 },
      });
      activeMap.addLayer({
        id: 'stored-lines',
        type: 'line',
        source: 'stored-geometry',
        filter: ['match', ['geometry-type'], ['LineString', 'MultiLineString'], true, false],
        paint: { 'line-color': accent, 'line-width': 2 },
      });
      activeMap.addLayer({
        id: 'stored-points',
        type: 'circle',
        source: 'stored-geometry',
        filter: ['match', ['geometry-type'], ['Point', 'MultiPoint'], true, false],
        paint: { 'circle-color': accent, 'circle-radius': 6 },
      });

      if (positions.length > 0) {
        const [firstLon, firstLat] = positions[0];
        const singlePoint = positions.every(([lon, lat]) => lon === firstLon && lat === firstLat);
        if (singlePoint) {
          activeMap.setCenter([firstLon, firstLat]);
          activeMap.setZoom(9);
        } else {
          const bounds = new maplibregl.LngLatBounds();
          for (const [lon, lat] of positions) bounds.extend([lon, lat]);
          activeMap.fitBounds(bounds, { padding: 40, maxZoom: 12 });
        }
      }
    });
    return () => activeMap.remove();
  }, [features, positions]);

  if (features.length === 0) {
    return <div className="notice notice-info" role="note">{emptyNote}</div>;
  }

  return (
    <div>
      {failed ? (
        <SvgWktFallback features={features} positions={positions} ariaLabel={ariaLabel} />
      ) : (
        <div ref={hostRef} className="spatial-map" role="img" aria-label={ariaLabel} />
      )}
      {skipped > 0 && (
        <p className="notice notice-warn" role="note">
          {skipped} stored geometry value(s) could not be drawn. Those records remain in the list below.
        </p>
      )}
      <p className="muted">
        Stored geometry only — no basemap, tile service or external request. Shown:{' '}
        {features.map((feature) => feature.properties.label).join(', ')}.
      </p>
    </div>
  );
}

function SvgWktFallback({
  features,
  positions,
  ariaLabel,
}: {
  features: WktFeature[];
  positions: Array<[number, number]>;
  ariaLabel: string;
}) {
  const width = 600;
  const height = 320;
  const pad = 28;

  const lons = positions.map(([lon]) => lon);
  const lats = positions.map(([, lat]) => lat);
  const rawMinLon = Math.min(...lons, 0);
  const rawMaxLon = Math.max(...lons, 0);
  const rawMinLat = Math.min(...lats, 0);
  const rawMaxLat = Math.max(...lats, 0);
  const spanLon = Math.max(rawMaxLon - rawMinLon, 0.25);
  const spanLat = Math.max(rawMaxLat - rawMinLat, 0.25);
  const minLon = rawMinLon - spanLon * 0.08;
  const minLat = rawMinLat - spanLat * 0.08;
  const scale = Math.min((width - pad * 2) / (spanLon * 1.16), (height - pad * 2) / (spanLat * 1.16));
  const offsetX = (width - spanLon * 1.16 * scale) / 2;
  const offsetY = (height - spanLat * 1.16 * scale) / 2;
  const project = ([lon, lat]: [number, number]): [number, number] => [
    offsetX + (lon - minLon) * scale,
    height - (offsetY + (lat - minLat) * scale),
  ];
  const ringPoints = (ring: Array<[number, number]>) =>
    ring.map((pt) => project(pt).map((n) => n.toFixed(1)).join(',')).join(' ');

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="spatial-map"
      role="img"
      aria-label={ariaLabel}
      style={{ background: 'var(--color-surface-alt, #e9eee8)', display: 'block', width: '100%' }}
    >
      {features.map((feature, index) => {
        const g = feature.geometry;
        const label = feature.properties.label;
        if (g.type === 'Polygon') {
          return (
            <polygon
              key={index}
              points={ringPoints(g.coordinates[0] ?? [])}
              fill="var(--color-accent, #1f6f8b)"
              fillOpacity={0.22}
              stroke="var(--color-accent, #1f6f8b)"
              strokeWidth={1.75}
            >
              <title>{label}</title>
            </polygon>
          );
        }
        if (g.type === 'MultiPolygon') {
          return g.coordinates.map((poly, pIdx) => (
            <polygon
              key={`${index}-${pIdx}`}
              points={ringPoints(poly[0] ?? [])}
              fill="var(--color-accent, #1f6f8b)"
              fillOpacity={0.22}
              stroke="var(--color-accent, #1f6f8b)"
              strokeWidth={1.75}
            >
              <title>{label}</title>
            </polygon>
          ));
        }
        if (g.type === 'LineString') {
          return (
            <polyline
              key={index}
              points={ringPoints(g.coordinates)}
              fill="none"
              stroke="var(--color-accent, #1f6f8b)"
              strokeWidth={2}
            >
              <title>{label}</title>
            </polyline>
          );
        }
        if (g.type === 'MultiLineString') {
          return g.coordinates.map((line, lIdx) => (
            <polyline
              key={`${index}-${lIdx}`}
              points={ringPoints(line)}
              fill="none"
              stroke="var(--color-accent, #1f6f8b)"
              strokeWidth={2}
            >
              <title>{label}</title>
            </polyline>
          ));
        }
        if (g.type === 'Point') {
          const [cx, cy] = project(g.coordinates);
          return (
            <circle key={index} cx={cx} cy={cy} r={6} fill="var(--color-accent, #1f6f8b)">
              <title>{label}</title>
            </circle>
          );
        }
        if (g.type === 'MultiPoint') {
          return g.coordinates.map((pt, ptIdx) => {
            const [cx, cy] = project(pt);
            return (
              <circle key={`${index}-${ptIdx}`} cx={cx} cy={cy} r={6} fill="var(--color-accent, #1f6f8b)">
                <title>{label}</title>
              </circle>
            );
          });
        }
        return null;
      })}
    </svg>
  );
}
