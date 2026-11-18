import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';

export function PrioritisationPage() {
  return (
    <WorkspacePage
      title="Prioritisation"
      description="Transparent factors and human review decisions. The system supports prioritisation; it does not independently decide enforcement or public-safety action."
    >
      <Notice variant="warn" role="note" title="Decision support only:">
        Prioritisation factors and rankings are aids for authorised human review. They are not automated enforcement, severity, or truth determinations.
      </Notice>
      <div className="card" style={{ marginTop: '1rem' }}>
        <h2>Prioritisation queue</h2>
        <EmptyState title="No prioritisation records loaded." detail="When available, review transparent factors, evidence context, uncertainty, and record a human decision with rationale." />
        <div className="table-wrap" role="region" aria-label="Prioritisation factors example structure" tabIndex={0} style={{ marginTop: '1rem' }}>
          <table>
            <thead><tr><th scope="col">Factor</th><th scope="col">Value / status</th><th scope="col">Notes</th></tr></thead>
            <tbody>
              <tr><td>Evidence strength & provenance</td><td className="muted">Pending backend</td><td className="muted">Based on linked, reviewed evidence (not correlation score as truth)</td></tr>
              <tr><td>Uncertainty & gaps</td><td className="muted">Pending backend</td><td className="muted">Missing data and limitations must remain visible</td></tr>
              <tr><td>Human decision & rationale</td><td className="muted">Required</td><td className="muted">Recorded by authorised reviewer/lead</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </WorkspacePage>
  );
}
