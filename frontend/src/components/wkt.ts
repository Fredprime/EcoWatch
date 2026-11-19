/**
 * Minimal WKT -> GeoJSON reader for the geometry already returned by the
 * Phase 3 staff read APIs (WGS84 / EPSG:4326). No external parser or network
 * service. Malformed or unsupported values are skipped, never invented.
 */
export type Position = [number, number];

export type WktGeometry =
  | { type: 'Point'; coordinates: Position }
  | { type: 'LineString'; coordinates: Position[] }
  | { type: 'Polygon'; coordinates: Position[][] }
  | { type: 'MultiPoint'; coordinates: Position[] }
  | { type: 'MultiLineString'; coordinates: Position[][] }
  | { type: 'MultiPolygon'; coordinates: Position[][][] };

export interface WktFeature {
  type: 'Feature';
  properties: { label: string };
  geometry: WktGeometry;
}

export interface SpatialItem {
  wkt: string | null | undefined;
  label: string;
}

export interface SpatialFeatures {
  features: WktFeature[];
  skipped: number;
}

type Node = Position | Node[];

function isPosition(node: Node): node is Position {
  return typeof node[0] === 'number';
}

function splitTopLevel(text: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let start = 0;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === '(') depth += 1;
    else if (char === ')') depth -= 1;
    else if (char === ',' && depth === 0) {
      parts.push(text.slice(start, index));
      start = index + 1;
    }
  }
  parts.push(text.slice(start));
  return parts.map((part) => part.trim()).filter(Boolean);
}

function parsePosition(text: string): Position {
  const match = /^\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*$/.exec(text);
  if (!match) throw new Error('Invalid coordinate pair');
  const lon = Number(match[1]);
  const lat = Number(match[2]);
  if (!Number.isFinite(lon) || !Number.isFinite(lat) || lon < -180 || lon > 180 || lat < -90 || lat > 90) {
    throw new Error('Coordinate outside WGS84 bounds');
  }
  return [lon, lat];
}

function parseNode(text: string): Node {
  const trimmed = text.trim();
  if (!trimmed.startsWith('(') || !trimmed.endsWith(')')) throw new Error('Unbalanced WKT group');
  const parts = splitTopLevel(trimmed.slice(1, -1));
  if (parts.length === 0) throw new Error('Empty WKT group');
  if (parts[0].startsWith('(')) return parts.map(parseNode);
  return parts.map(parsePosition);
}

/** POINT and parenthesised MULTIPOINT wrap a position in an extra group. */
function unwrapSingle(node: Node): Node {
  if (!isPosition(node) && node.length === 1) return unwrapSingle(node[0]);
  return node;
}

function asPositions(node: Node): Position[] {
  if (isPosition(node)) return [node];
  return node.map((item) => {
    const position = unwrapSingle(item);
    if (!isPosition(position)) throw new Error('Unexpected WKT nesting');
    return position;
  });
}

function asRings(node: Node): Position[][] {
  if (isPosition(node)) throw new Error('Unexpected WKT nesting');
  return node.map(asPositions);
}

function asPolygons(node: Node): Position[][][] {
  if (isPosition(node)) throw new Error('Unexpected WKT nesting');
  return node.map(asRings);
}

export function parseWkt(raw: string): WktGeometry {
  const text = raw.replace(/^\s*SRID=\d+\s*;\s*/i, '').trim();
  const match = /^(POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON)\s*(\(.*\))$/i.exec(text);
  if (!match) throw new Error('Unsupported WKT type');
  const node = parseNode(match[2]);
  switch (match[1].toUpperCase()) {
    case 'POINT': {
      const position = unwrapSingle(node);
      if (!isPosition(position)) throw new Error('Expected one coordinate');
      return { type: 'Point', coordinates: position };
    }
    case 'LINESTRING': {
      const coordinates = asPositions(node);
      if (coordinates.length < 2) throw new Error('Line needs two coordinates');
      return { type: 'LineString', coordinates };
    }
    case 'POLYGON':
      return { type: 'Polygon', coordinates: asRings(node) };
    case 'MULTIPOINT':
      return { type: 'MultiPoint', coordinates: asPositions(node) };
    case 'MULTILINESTRING':
      return { type: 'MultiLineString', coordinates: asRings(node) };
    case 'MULTIPOLYGON':
      return { type: 'MultiPolygon', coordinates: asPolygons(node) };
    default:
      throw new Error('Unsupported WKT type');
  }
}

export function featuresFromWkt(items: SpatialItem[]): SpatialFeatures {
  const features: WktFeature[] = [];
  let skipped = 0;
  for (const item of items) {
    if (!item.wkt) continue;
    try {
      features.push({
        type: 'Feature',
        properties: { label: item.label },
        geometry: parseWkt(item.wkt),
      });
    } catch {
      skipped += 1;
    }
  }
  return { features, skipped };
}

export function allPositions(geometry: WktGeometry): Position[] {
  const positions: Position[] = [];
  const walk = (value: unknown): void => {
    if (Array.isArray(value) && typeof value[0] === 'number') {
      positions.push([value[0] as number, value[1] as number]);
    } else if (Array.isArray(value)) {
      for (const child of value) walk(child);
    }
  };
  walk(geometry.coordinates);
  return positions;
}
