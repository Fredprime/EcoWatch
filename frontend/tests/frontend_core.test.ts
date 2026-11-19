import test from 'node:test';
import assert from 'node:assert/strict';

import { parseWkt, featuresFromWkt, allPositions } from '../src/components/wkt.ts';
import { rolesFor, hasAnyRole, CORRELATION_REVIEW_ROLES } from '../src/auth/roles.ts';
import { displayText, formatTime } from '../src/components/phase3Format.ts';
import { ApiError } from '../src/api/client.ts';
import type { AuthMeResponse } from '../src/api/types.ts';

test('parseWkt parses POINT, LINESTRING, POLYGON and rejects malformed input', () => {
  const pt = parseWkt('POINT(-1.6244 6.6885)');
  assert.deepEqual(pt, { type: 'Point', coordinates: [-1.6244, 6.6885] });

  const line = parseWkt('LINESTRING(-1.6 6.6, -1.5 6.7)');
  assert.deepEqual(line, {
    type: 'LineString',
    coordinates: [
      [-1.6, 6.6],
      [-1.5, 6.7],
    ],
  });

  const poly = parseWkt('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))');
  assert.equal(poly.type, 'Polygon');
  assert.equal(allPositions(poly).length, 5);

  assert.throws(() => parseWkt('NOT_WKT(1 2)'));
});

test('featuresFromWkt skips malformed or empty geometries without inventing coordinates', () => {
  const result = featuresFromWkt([
    { label: 'Valid site', wkt: 'POINT(-1.62 6.68)' },
    { label: 'Missing', wkt: null },
    { label: 'Bad WKT', wkt: 'POINT(bad)' },
  ]);
  assert.equal(result.features.length, 1);
  assert.equal(result.features[0]?.properties.label, 'Valid site');
  assert.equal(result.skipped, 1);
});

test('rolesFor and hasAnyRole respect active memberships and systemRole', () => {
  const me: AuthMeResponse = {
    id: 'u1',
    email: 'rev@ecowatch.test',
    displayName: 'Reviewer',
    systemRole: null,
    isActive: true,
    createdAt: '2026-11-19T00:00:00Z',
    updatedAt: '2026-11-19T00:00:00Z',
    memberships: [
      {
        id: 'm1',
        userId: 'u1',
        organisationId: 'o1',
        role: 'reviewer',
        isActive: true,
        createdAt: '2026-11-19T00:00:00Z',
      },
      {
        id: 'm2',
        userId: 'u1',
        organisationId: 'o2',
        role: 'organisation_admin',
        isActive: false,
      createdAt: '2026-11-19T00:00:00Z',
      },
    ],
  };

  assert.deepEqual(rolesFor(me), ['reviewer']);
  assert.equal(hasAnyRole(me, CORRELATION_REVIEW_ROLES), true);
  assert.equal(hasAnyRole(me, ['organisation_admin']), false);
  assert.equal(hasAnyRole(null, ['all']), false);
});

test('phase3Format and ApiError preserve absence markers and error categories', () => {
  assert.equal(displayText(''), 'Not recorded');
  assert.equal(displayText('  ok  '), '  ok  ');
  assert.equal(formatTime(null), 'Not provided');

  const err = new ApiError(
    429,
    { code: 'RATE_LIMIT_EXCEEDED', category: 'transient', retryAfterSeconds: 15 },
    'Fallback',
  );
  assert.equal(err.status, 429);
  assert.equal(err.code, 'RATE_LIMIT_EXCEEDED');
  assert.equal(err.category, 'transient');
  assert.equal(err.retryAfterSeconds, 15);
});
