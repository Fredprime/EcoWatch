import { useCallback, useState, type FormEvent } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';
import { ResourceState } from '../components/ResourceState';
import { ActionPanel, RecordPicker } from '../components/Phase3Views';
import { useApiResource } from '../hooks/useApiResource';
import {
  assignMembership,
  createOrganisation,
  createUser,
  getJobsSummary,
  listAuditEvents,
  listOrganisations,
} from '../api/admin';
import { errorMessage } from '../api/client';

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

  const [orgName, setOrgName] = useState('');
  const [orgType, setOrgType] = useState('REGULATOR');
  const [orgBusy, setOrgBusy] = useState(false);
  const [orgStatus, setOrgStatus] = useState<string | null>(null);
  const [orgError, setOrgError] = useState<string | null>(null);

  const [userEmail, setUserEmail] = useState('');
  const [userDisplayName, setUserDisplayName] = useState('');
  const [userPassword, setUserPassword] = useState('');
  const [userSystemRole, setUserSystemRole] = useState('');
  const [userBusy, setUserBusy] = useState(false);
  const [userStatus, setUserStatus] = useState<string | null>(null);
  const [userError, setUserError] = useState<string | null>(null);

  const [memberOrgId, setMemberOrgId] = useState('');
  const [memberUserId, setMemberUserId] = useState('');
  const [memberRole, setMemberRole] = useState('reviewer');
  const [memberReason, setMemberReason] = useState('');
  const [memberBusy, setMemberBusy] = useState(false);
  const [memberStatus, setMemberStatus] = useState<string | null>(null);
  const [memberError, setMemberError] = useState<string | null>(null);

  const orgOptions =
    organisations.state.status === 'success'
      ? organisations.state.data.items.map((o) => ({ value: o.id, label: o.name }))
      : [];

  async function handleCreateOrg(event: FormEvent) {
    event.preventDefault();
    setOrgBusy(true);
    setOrgStatus(null);
    setOrgError(null);
    try {
      const created = await createOrganisation({ name: orgName, orgType, isActive: true });
      setOrgName('');
      setOrgStatus(`Organisation "${created.name}" created (${created.id}).`);
      organisations.reload();
      audit.reload();
    } catch (err) {
      setOrgError(errorMessage(err));
    } finally {
      setOrgBusy(false);
    }
  }

  async function handleCreateUser(event: FormEvent) {
    event.preventDefault();
    setUserBusy(true);
    setUserStatus(null);
    setUserError(null);
    try {
      const created = await createUser({
        email: userEmail,
        displayName: userDisplayName,
        password: userPassword,
        systemRole: userSystemRole || null,
        isActive: true,
      });
      setUserEmail('');
      setUserDisplayName('');
      setUserPassword('');
      setUserStatus(`User ${created.email} created (ID: ${created.id}).`);
      setMemberUserId(created.id);
      audit.reload();
    } catch (err) {
      setUserError(errorMessage(err));
    } finally {
      setUserBusy(false);
    }
  }

  async function handleAssignMembership(event: FormEvent) {
    event.preventDefault();
    setMemberBusy(true);
    setMemberStatus(null);
    setMemberError(null);
    try {
      const created = await assignMembership(memberOrgId, {
        userId: memberUserId,
        role: memberRole,
        isActive: true,
        reason: memberReason || null,
      });
      setMemberReason('');
      setMemberStatus(`Membership assigned (${created.role}) for user ${created.userId}.`);
      audit.reload();
    } catch (err) {
      setMemberError(errorMessage(err));
    } finally {
      setMemberBusy(false);
    }
  }

  return (
    <WorkspacePage
      title="Administration"
      description="Organisation, user, membership, audit and queue management within your permitted scope. Access is restricted and audited."
    >
      <Notice variant="danger" role="note" title="Restricted workspace:">
        Administrative functions are role-scoped and enforced server-side. UI controls do not bypass server permissions; all changes are audited.
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

      <div style={{ marginTop: '1rem', display: 'grid', gap: '1rem' }}>
        <ActionPanel
          title="Create organisation"
          summary="System-admin action to register a new tenant organisation."
          statusMessage={orgStatus}
          errorMessageText={orgError}
          submitting={orgBusy}
          submitLabel="Create organisation"
          onSubmit={handleCreateOrg}
        >
          <div className="field">
            <label htmlFor="admin-org-name">Organisation name</label>
            <input
              id="admin-org-name"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              required
              minLength={2}
            />
          </div>
          <div className="field">
            <label htmlFor="admin-org-type">Organisation type</label>
            <input
              id="admin-org-type"
              value={orgType}
              onChange={(e) => setOrgType(e.target.value)}
              required
              minLength={2}
              placeholder="REGULATOR, NGO, RESEARCH"
            />
          </div>
        </ActionPanel>

        <ActionPanel
          title="Create user account"
          summary="System-admin action to provision a staff or contributor account."
          statusMessage={userStatus}
          errorMessageText={userError}
          submitting={userBusy}
          submitLabel="Create user"
          onSubmit={handleCreateUser}
        >
          <div className="field">
            <label htmlFor="admin-user-email">Email</label>
            <input
              id="admin-user-email"
              type="email"
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="admin-user-name">Display name</label>
            <input
              id="admin-user-name"
              value={userDisplayName}
              onChange={(e) => setUserDisplayName(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="admin-user-password">Password (min 8 characters)</label>
            <input
              id="admin-user-password"
              type="password"
              value={userPassword}
              onChange={(e) => setUserPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>
          <div className="field">
            <label htmlFor="admin-user-sysrole">System role (optional)</label>
            <select
              id="admin-user-sysrole"
              value={userSystemRole}
              onChange={(e) => setUserSystemRole(e.target.value)}
            >
              <option value="">None (org-scoped only)</option>
              <option value="system_admin">system_admin</option>
            </select>
          </div>
        </ActionPanel>

        <ActionPanel
          title="Assign organisation membership"
          summary="Grant or update a user role within a specific organisation."
          statusMessage={memberStatus}
          errorMessageText={memberError}
          submitting={memberBusy}
          submitLabel="Assign membership"
          onSubmit={handleAssignMembership}
        >
          <RecordPicker
            id="admin-member-org"
            label="Organisation"
            value={memberOrgId}
            onChange={setMemberOrgId}
            options={orgOptions}
          />
          <div className="field">
            <label htmlFor="admin-member-user">User ID (UUID)</label>
            <input
              id="admin-member-user"
              value={memberUserId}
              onChange={(e) => setMemberUserId(e.target.value)}
              required
              placeholder="UUID of existing user"
            />
          </div>
          <div className="field">
            <label htmlFor="admin-member-role">Role</label>
            <select
              id="admin-member-role"
              value={memberRole}
              onChange={(e) => setMemberRole(e.target.value)}
            >
              <option value="registered_contributor">registered_contributor</option>
              <option value="reviewer">reviewer</option>
              <option value="investigator">investigator</option>
              <option value="environmental_specialist">environmental_specialist</option>
              <option value="intervention_manager">intervention_manager</option>
              <option value="organisation_admin">organisation_admin</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="admin-member-reason">Reason (optional)</label>
            <input
              id="admin-member-reason"
              value={memberReason}
              onChange={(e) => setMemberReason(e.target.value)}
            />
          </div>
        </ActionPanel>
      </div>
    </WorkspacePage>
  );
}
