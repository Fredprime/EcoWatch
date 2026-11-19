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
        <EmptyState title="No prioritisation records in your permitted scope." detail="When records are available, review transparent factors, evidence context and uncertainty, then record a human decision with rationale." />
      </div>
    </WorkspacePage>
  );
}
