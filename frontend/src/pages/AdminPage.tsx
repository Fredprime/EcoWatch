import { useCallback } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';
import { ResourceState } from '../components/ResourceState';
import { useApiResource } from '../hooks/useApiResource';
import { getJobsSummary, listAuditEvents, listOrganisations } from '../api/admin';

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function AdminPage() {
  const loadOrganisations = useCallback(() => listOrganisations(), []);
  const loadAudit = useCallback(() => listAuditEvents(), []);
  const loadJobs = useCallback(() => getJobsSummary(), []);
  const organisations = useApiResource(loadOrganisations, 'admin:organisations');
  const audit = useApiResource(loadAudit, 'admin:audit');
  const jobs = useApiResource(loadJobs, 'admin:jobs');

  return (
    <WorkspacePage
      title="Administration"
      description="Read-only administration views within your permitted scope. Access is restricted and audited in production."
    >
      <Notice variant="danger" role="note" title="Restricted workspace:">
        Administrative functions are role-scoped and fully enforced server-side. UI visibility is not a security control. This view is read-only; sensitive actions remain audited on the server.
      </Notice>

      <div className="grid grid-2" style={{ marginTop: '1rem' }}>
        <div className="card">
          <h2>Organisations</h2>
          <p className="muted">Organisations visible to your account. Roles and memberships are enforced by the server.</p>
          <ResourceState state={organisations.state}>
            {(page) =>
              page.items.length === 0 ? (
                <EmptyState
                  title="No organisations in your permitted scope."
                  detail="Records appear here only when the server returns them for your role."
                />
              ) : (
                <div className="table-wrap" role="region" aria-label="Organisations table" tabIndex={0}>
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Organisation</th>
                        <th scope="col">Type</th>
                        <th scope="col">Active</th>
                        <th scope="col">Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {page.items.map((org) => (
                        <tr key={org.id}>
                          <th scope="row">{org.name}</th>
                          <td>{org.orgType.replaceAll('_', ' ')}</td>
                          <td>{org.isActive ? 'Yes' : 'No'}</td>
                          <td>{formatTime(org.createdAt)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            }
          </ResourceState>
        </div>

        <div className="card">
          <h2>Queue status</h2>
          <ResourceState state={jobs.state}>
            {(summary) => (
              <>
                <p className="muted">
                  Pending {summary.totalPending}. Processing {summary.totalProcessing}. Processed{' '}
                  {summary.totalProcessed}. Failed {summary.totalFailed}. Dead {summary.totalDead}.
                </p>
                {summary.byType.length === 0 ? (
                  <EmptyState
                    title="No job types reported."
                    detail="Queue counters appear here when the server reports them."
                  />
                ) : (
                  <div className="table-wrap" role="region" aria-label="Job queues table" tabIndex={0}>
                    <table>
                      <thead>
                        <tr>
                          <th scope="col">Job type</th>
                          <th scope="col">Pending</th>
                          <th scope="col">Processing</th>
                          <th scope="col">Processed</th>
                          <th scope="col">Failed</th>
                          <th scope="col">Dead</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.byType.map((row) => (
                          <tr key={row.jobType}>
                            <th scope="row">{row.jobType.replaceAll('_', ' ')}</th>
                            <td>{row.pending}</td>
                            <td>{row.processing}</td>
                            <td>{row.processed}</td>
                            <td>{row.failed}</td>
                            <td>{row.dead}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </ResourceState>
        </div>
      </div>

      <div className="card">
        <h2>Recent audit events</h2>
        <p className="muted">
          Append-only events in your permitted scope. Actor identity and raw event details are not shown here.
        </p>
        <ResourceState state={audit.state}>
          {(page) =>
            page.items.length === 0 ? (
              <EmptyState
                title="No audit events in your permitted scope."
                detail="Events appear here only when the server returns them for your role."
              />
            ) : (
              <div className="table-wrap" role="region" aria-label="Audit events table" tabIndex={0}>
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Recorded</th>
                      <th scope="col">Action</th>
                      <th scope="col">Target</th>
                      <th scope="col">Actor role</th>
                    </tr>
                  </thead>
                  <tbody>
                    {page.items.map((event) => (
                      <tr key={event.id}>
                        <td>{formatTime(event.occurredAt)}</td>
                        <td>{event.action}</td>
                        <td>{event.targetType}</td>
                        <td>{event.actorRole.replaceAll('_', ' ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          }
        </ResourceState>
      </div>
    </WorkspacePage>
  );
}
