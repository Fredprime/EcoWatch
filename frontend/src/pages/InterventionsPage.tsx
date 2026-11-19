import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';

export function InterventionsPage() {
  return (
    <WorkspacePage
      title="Interventions"
      description="Approved actions, owners, milestones and records. Activity completion is distinct from environmental outcome."
    >
      <Notice variant="info" role="note" title="Outcome distinction:">
        Recording an intervention or completed activity does not demonstrate environmental recovery. Outcomes are assessed separately with suitable evidence.
      </Notice>
      <div className="grid grid-2" style={{ marginTop: '1rem' }}>
        <div className="card">
          <h2>Intervention records</h2>
          <EmptyState title="No interventions loaded." detail="Approved actions, responsible organisations/owners, approvals, and milestones will appear here when available." />
        </div>
        <div className="card">
          <h2>Baselines & intended outcomes</h2>
          <EmptyState title="No baseline/outcome plan loaded." detail="Baselines, intended outcomes, and monitoring plans must be defined and linked before outcome claims." />
        </div>
      </div>
      <div className="card">
        <h2>Actions (pending backend)</h2>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-secondary" disabled>Record intervention</button>
          <button type="button" className="btn btn-secondary" disabled>Update milestone</button>
          <button type="button" className="btn btn-secondary" disabled>Attach evidence</button>
        </div>
      </div>
    </WorkspacePage>
  );
}
