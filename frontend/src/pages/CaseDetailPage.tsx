import { Link, useParams } from 'react-router-dom';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';

export function CaseDetailPage() {
  const { caseId } = useParams();

  return (
    <WorkspacePage
      title={`Case detail${caseId ? `: ${caseId}` : ''}`}
      description="Case workspace shell. In production this view loads a specific case (within permitted scope) with evidence-grounded summary, timeline, relationships, hypotheses, actions, and audit history."
    >
      <Notice variant="info" role="note" title="Endpoint-independent shell:">
        This route establishes navigation and layout. Case records, evidence, and review actions will load from backend APIs when available.
      </Notice>
      <div style={{ margin: '1rem 0' }}>
        <Link className="btn btn-secondary" to="/cases">Back to cases</Link>
      </div>
      <div className="card">
        <h2>Record status</h2>
        <EmptyState
          title="No case record loaded."
          detail="Connect to the cases API to retrieve case summary, linked observations/evidence, timeline, relationships, hypotheses, and review history for this ID. Ensure access is authorised and locations are handled per sensitivity rules."
        />
      </div>
      <div className="card">
        <h2>Required sections (to populate from backend)</h2>
        <ul>
          <li>Evidence-grounded summary (claims/measurements/interpretations/model outputs distinguished)</li>
          <li>Status, owner, and role-scoped permissions</li>
          <li>Map and geographic context with non-map alternatives and uncertainty/precision</li>
          <li>Linked observations and evidence (originals preserved)</li>
          <li>Relationship explanations and reviewer decisions (audited, reversible)</li>
          <li>Timeline with separated date types</li>
          <li>Hypotheses, evidence gaps, and next actions</li>
          <li>Intervention and verification records (when relevant)</li>
        </ul>
      </div>
    </WorkspacePage>
  );
}
