import { useMemo, useState } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { mockObservations } from '../data/mockObservations';

function stateLabel(state: string) {
  if (state === 'review') return 'In review';
  if (state === 'queued') return 'Queued locally';
  if (state === 'submitted') return 'Submitted';
  if (state === 'received') return 'Received';
  return 'Draft';
}

function stateClass(state: string) {
  if (state === 'queued') return 'status-queued';
  if (state === 'submitted') return 'status-submitted';
  if (state === 'received') return 'status-received';
  return 'status-draft';
}

export function OverviewPage() {
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return mockObservations;
    return mockObservations.filter((o) =>
      [o.id, o.type, o.summary, o.location, o.source, stateLabel(o.state)].some((v) => v.toLowerCase().includes(q)),
    );
  }, [query]);

  return (
    <WorkspacePage
      title="Overview"
      description="Active cases, recent observations, assigned work and system notices. This view is role-scoped in the full product."
    >
      <div className="grid grid-3">
        <div className="card"><h3>Recent observations</h3><p className="muted">Showing a demo list view below (non-map alternative). Records appear after server receipt and within permitted scope.</p></div>
        <div className="card"><h3>Active cases</h3><p className="muted">Case summaries, owners and status will be shown to authorised users.</p></div>
        <div className="card"><h3>Notices</h3><p className="muted">System, review and assignment notices appear here. Machine-generated content must be labelled distinctly.</p></div>
      </div>

      <div className="card">
        <h2>Observations (list view)</h2>
        <p className="muted">Demo data only. List/detail views complement maps; sensitive locations may be restricted or generalised and time/location precision is shown explicitly.</p>

        <div className="toolbar">
          <div className="field">
            <label htmlFor="obs-filter">Filter observations</label>
            <input
              id="obs-filter"
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by id, type, summary, location, source, or state"
            />
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="empty-state" role="status">
            <p><strong>No observations match this filter.</strong></p>
            <p className="muted">Try a different search, or clear the filter to view available records.</p>
          </div>
        ) : (
          <div className="table-wrap" role="region" aria-label="Observations table" tabIndex={0}>
            <table>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Type / summary</th>
                  <th scope="col">Observed time</th>
                  <th scope="col">Location</th>
                  <th scope="col">Source</th>
                  <th scope="col">State</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((o) => (
                  <tr key={o.id}>
                    <th scope="row">{o.id}</th>
                    <td>
                      <div><strong>{o.type}</strong></div>
                      <div className="muted">{o.summary}</div>
                    </td>
                    <td>
                      <div>{o.observedTime}</div>
                      <div className="muted">Precision: {o.observedPrecision}</div>
                    </td>
                    <td>
                      <div>{o.location}</div>
                      <div className="muted">Precision: {o.locationPrecision}</div>
                    </td>
                    <td>{o.source}</td>
                    <td><span className={`status-pill ${stateClass(o.state)}`}>{stateLabel(o.state)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card notice notice-info" role="note">
        <strong>Design baseline:</strong> EcoWatch follows Collect → Analyse → Prioritise → Intervene → Verify. This frontend scaffold reflects documented workspaces and states; data, integrations and approvals are not yet implemented.
      </div>
    </WorkspacePage>
  );
}
