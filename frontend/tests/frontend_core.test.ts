import test from 'node:test';
import assert from 'node:assert/strict';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

import { parseWkt, featuresFromWkt, allPositions } from '../src/components/wkt.ts';
import { rolesFor, hasAnyRole, CORRELATION_REVIEW_ROLES } from '../src/auth/roles.ts';
import { displayText, formatTime } from '../src/components/phase3Format.ts';
import { ApiError } from '../src/api/client.ts';
import type { AuthMeResponse, IntakeReceiptResponse } from '../src/api/types.ts';
import { CopyButton } from '../src/components/CopyButton.tsx';
import { ReceiptDialog } from '../src/components/ReceiptDialog.tsx';
import { Notice } from '../src/components/Notice.tsx';
import { EmptyState } from '../src/components/EmptyState.tsx';
import { ActionPanel, ReadOnlyListCard, RecordPicker } from '../src/components/Phase3Views.tsx';

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

test('UI components render accessible roles, labels, empty states, and tables', () => {
  const noticeHtml = renderToStaticMarkup(
    createElement(Notice, { variant: 'danger', role: 'alert', title: 'Error:' }, 'Denied'),
  );
  assert.match(noticeHtml, /role="alert"/);
  assert.match(noticeHtml, /Error:/);
  assert.match(noticeHtml, /Denied/);

  const emptyHtml = renderToStaticMarkup(
    createElement(EmptyState, { title: 'No records', detail: 'Nothing recorded yet.' }),
  );
  assert.match(emptyHtml, /No records/);
  assert.match(emptyHtml, /Nothing recorded yet\./);

  const pickerHtml = renderToStaticMarkup(
    createElement(RecordPicker, {
      id: 'org-pick',
      label: 'Organisation',
      value: 'o1',
      onChange: () => {},
      options: [{ value: 'o1', label: 'Org One' }],
    }),
  );
  assert.match(pickerHtml, /for="org-pick"/);
  assert.match(pickerHtml, /Org One/);

  const listHtml = renderToStaticMarkup(
    createElement(ReadOnlyListCard<{ id: string; name: string }>, {
      title: 'Datasets',
      state: {
        status: 'success',
        data: { items: [{ id: '1', name: 'River Turbidity' }], nextCursor: null, hasMore: false },
      },
      emptyTitle: 'None',
      columns: [{ header: 'Name', cell: (row) => row.name }],
      ariaLabel: 'Datasets table',
    }),
  );
  assert.match(listHtml, /aria-label="Datasets table"/);
  assert.match(listHtml, /River Turbidity/);

  const actionHtml = renderToStaticMarkup(
    createElement(
      ActionPanel,
      {
        title: 'Create record',
        submitting: false,
        submitLabel: 'Save',
        onSubmit: () => {},
        statusMessage: 'Created ok',
      },
      createElement('input', { id: 'f1', type: 'text' }),
    ),
  );
  assert.match(actionHtml, /Create record/);
  assert.match(actionHtml, /Created ok/);
  assert.match(actionHtml, /Save/);
});

test('receipt confirmation shows a copyable tracking reference', () => {
  const receipt: IntakeReceiptResponse = {
    observationId: 'obs-1',
    organisationId: 'org-1',
    receivedAt: '2026-11-20T09:00:00Z',
    observationType: 'water',
    timePrecision: 'approximate',
    locationPrecision: 'area',
    currentVersion: 1,
    trackingCode: 'ECO-TRACK-123',
    idempotentReplay: false,
  };

  const copyHtml = renderToStaticMarkup(
    createElement(CopyButton, {
      value: receipt.trackingCode,
      label: 'Copy tracking reference',
      ariaLabel: 'Copy tracking reference',
    }),
  );
  assert.match(copyHtml, /type="button"/);
  assert.match(copyHtml, /Copy tracking reference/);

  const dialogHtml = renderToStaticMarkup(
    createElement(ReceiptDialog, { open: true, receipt, onClose: () => {} }),
  );
  assert.match(dialogHtml, /<dialog/);
  assert.match(dialogHtml, /aria-labelledby="receipt-dialog-title"/);
  assert.match(dialogHtml, /Report received/);
  assert.match(dialogHtml, /ECO-TRACK-123/);
  assert.match(dialogHtml, /Copy tracking reference/);
});
