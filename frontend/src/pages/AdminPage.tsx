import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';

export function AdminPage() {
  return (
    <WorkspacePage
      title="Administration"
      description="Users, organisations, vocabularies, imports, audit and configuration. Access is restricted and audited in production."
    >
      <Notice variant="danger" role="note" title="Restricted workspace:">
        Administrative functions are role-scoped and fully enforced server-side. UI visibility is not a security control. All sensitive actions must be audited.
      </Notice>
      <div className="grid grid-2" style={{ marginTop: '1rem' }}>
        <div className="card">
          <h2>Users & organisations</h2>
          <EmptyState title="No administrative data loaded." detail="Manage scoped users, roles, organisations, and assignments when authorised backend endpoints are available." />
        </div>
        <div className="card">
          <h2>Vocabularies, imports & audit</h2>
          <EmptyState title="No configuration records loaded." detail="Controlled vocabularies, data imports, and audit views will appear here for authorised administrators." />
        </div>
      </div>
    </WorkspacePage>
  );
}
