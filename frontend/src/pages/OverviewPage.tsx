import { useCallback, useMemo, useState } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';
import { ResourceState } from '../components/ResourceState';
import { SignInPrompt } from '../components/SignInPrompt';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import { getHealth } from '../api/health';
import { exportObservations, listObservations } from '../api/observations';
import { downloadCsv, downloadJson } from '../api/exportFile';
import type { ObservationSummary } from '../api/types';

function formatTime(value: string | null | undefined): string {
  if (!value) return 'Not provided';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function OverviewPage() {
  const { status } = useAuth();
  const [query, setQuery] = useState('');
  const loadHealth = useCallback(() => getHealth(), []);
  const loadObservations = useCallback(() => listObservations(), []);
  const health = useApiResource(loadHealth, 'health');
  const observations = useApiResource(loadObservations, 'observations', status === 'authenticated');

  const rows = useMemo<ObservationSummary[]>(() => {
    if (observations.state.status !== 'success') return [];
    const q = query.trim().toLowerCase();
    if (!q) return observations.state.data.items;
    return observations.state.data.items.filter((item) =>
      [item.id, item.observationType, item.description, item.sourceType].some((value) =>
        value.toLowerCase().includes(q),
      ),
    );
  }, [observations.state, query]);

  return (
    <WorkspacePage
      title="Overview"
      description="Recent observations within your permitted scope. Records are shown with their time and location precision; maps are not the only view."
    >
      <div className="grid grid-3">
        <div className="card">
          <h2>Recent observations</h2>
          <p className="muted">Received records appear in the list below once the server confirms receipt.</p>
        </div>
        <div className="card">
          <h2>Service status</h2>
          <ResourceState state={health.state}>
            {(data) => (
              <p className="muted">
                API: {data.status}. Database: {data.database}. PostGIS: {data.postgisVersion ?? 'not reported'}.
              </p>
            )}
          </ResourceState>
        </div>
        <div className="card">
          <h2>Notices</h2>
          <p className="muted">No notices are available in your permitted scope. Machine-generated content is labelled separately.</p>
        </div>
      </div>

      <div className="card">
        <h2>Observations (list view)</h2>
        <p className="muted">
          Event-start, observed, submitted and server receipt times are separate fields. Unknown values stay empty rather than being invented.
        </p>

        {status !== 'authenticated' ? (
          <SignInPrompt what="Observation records require an authenticated account." />
        ) : (
          <>
            <div className="toolbar">
              <div className="field">
                <label htmlFor="obs-filter">Filter this page</label>
                <input
                  id="obs-filter"
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search the current page by id, type, summary or source"
                  aria-describedby="obs-filter-hint"
                />
                <p id="obs-filter-hint" className="field-hint">Filters only the records already returned by the server.</p>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={rows.length === 0}
                  onClick={() =>
                    downloadCsv(
                      'ecowatch-reports.csv',
                      ['id', 'organisationId', 'observationType', 'sourceType', 'description', 'observedAt', 'receivedAt', 'timePrecision', 'locationPrecision', 'publicLat', 'publicLon'],
                      rows.map((r) => [r.id, r.organisationId, r.observationType, r.sourceType, r.description, r.observedAt, r.receivedAt, r.timePrecision, r.locationPrecision, r.publicLocation?.lat ?? '', r.publicLocation?.lon ?? '']),
                    )
                  }
                >
                  Export Reports (CSV)
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={rows.length === 0}
                  onClick={() => {
                    const orgId = rows[0]?.organisationId;
                    if (!orgId) {
                      downloadJson('ecowatch-reports.json', rows);
                      return;
                    }
                    void exportObservations(orgId)
                      .then((full) => downloadJson('ecowatch-reports-archive.json', full))
                      .catch(() => downloadJson('ecowatch-reports.json', rows));
                  }}
                >
                  Export Reports (JSON)
                </button>
              </div>
            </div>

            <ResourceState state={observations.state}>
              {(page) =>
                rows.length === 0 ? (
                  <EmptyState
                    title="No observations in your permitted scope yet."
                    detail={page.hasMore ? 'Records exist beyond this page; clear the filter to see them.' : 'Submit an observation to create the first record.'}
                  />
                ) : (
                  <>
                    <div className="table-wrap" role="region" aria-label="Observations table" tabIndex={0}>
                      <table>
                        <thead>
                          <tr>
                            <th scope="col">ID</th>
                            <th scope="col">Type / summary</th>
                            <th scope="col">Observed time</th>
                            <th scope="col">Public location</th>
                            <th scope="col">Source</th>
                            <th scope="col">Server receipt</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map((item) => (
                            <tr key={item.id}>
                              <th scope="row">{item.id}</th>
                              <td>
                                <div><strong>{item.observationType}</strong></div>
                                <div className="muted">{item.description}</div>
                              </td>
                              <td>
                                <div>{formatTime(item.observedAt)}</div>
                                <div className="muted">Precision: {item.timePrecision}</div>
                              </td>
                              <td>
                                <div>
                                  {item.publicLocation
                                    ? `${item.publicLocation.lat}, ${item.publicLocation.lon}`
                                    : 'Not provided or generalised'}
                                </div>
                                <div className="muted">Precision: {item.locationPrecision}</div>
                              </td>
                              <td>{item.sourceType.replaceAll('_', ' ')}</td>
                              <td>{formatTime(item.receivedAt)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {page.hasMore && (
                      <Notice variant="info" role="note">
                        More records exist. This view shows the first page only.
                      </Notice>
                    )}
                  </>
                )
              }
            </ResourceState>
          </>
        )}
      </div>
    </WorkspacePage>
  );
}
