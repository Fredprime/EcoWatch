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
    const map = new maplibregl.Map({
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
    map.on('error', () => setFailed(true));
    map.on('load', () => {
      map.addSource('stored-geometry', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features } as unknown as FeatureCollection,
      });
      map.addLayer({
        id: 'stored-areas',
        type: 'fill',
        source: 'stored-geometry',
        filter: ['match', ['geometry-type'], ['Polygon', 'MultiPolygon'], true, false],
        paint: { 'fill-color': accent, 'fill-opacity': 0.25 },
      });
      map.addLayer({
        id: 'stored-lines',
        type: 'line',
        source: 'stored-geometry',
        filter: ['match', ['geometry-type'], ['LineString', 'MultiLineString'], true, false],
        paint: { 'line-color': accent, 'line-width': 2 },
      });
      map.addLayer({
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
          map.setCenter([firstLon, firstLat]);
          map.setZoom(9);
        } else {
          const bounds = new maplibregl.LngLatBounds();
          for (const [lon, lat] of positions) bounds.extend([lon, lat]);
          map.fitBounds(bounds, { padding: 40, maxZoom: 12 });
        }
      }
    });
    return () => map.remove();
  }, [features, positions]);

  if (features.length === 0) {
    return <div className="notice notice-info" role="note">{emptyNote}</div>;
  }

  return (
    <div>
      <div ref={hostRef} className="spatial-map" role="img" aria-label={ariaLabel} />
      {skipped > 0 && (
        <p className="notice notice-warn" role="note">
          {skipped} stored geometry value(s) could not be drawn. Those records remain in the list below.
        </p>
      )}
      {failed && (
        <p className="notice notice-danger" role="alert">
          The map could not be initialised. The list/detail view below is unchanged.
        </p>
      )}
      <p className="muted">
        Stored geometry only — no basemap, tile service or external request. Shown:{' '}
        {features.map((feature) => feature.properties.label).join(', ')}.
      </p>
    </div>
  );
}
