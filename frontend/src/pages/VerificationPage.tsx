import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';

export function VerificationPage() {
  return (
    <WorkspacePage
      title="Verification"
      description="Baselines, follow-up measurements and outcome assessments. Recovery claims require suitable evidence, comparison, and qualified review."
    >
      <Notice variant="warn" role="note" title="Verification boundary:">
        “Field verified” or “recovery verified” status requires authorised human review and approved criteria with appropriate evidence. Automated outputs do not set these statuses.
      </Notice>
      <div className="grid grid-2" style={{ marginTop: '1rem' }}>
        <div className="card">
          <h2>Follow-up measurements</h2>
          <EmptyState title="No follow-up data loaded." detail="Compare against baselines/reference conditions using documented, comparable methods when available." />
        </div>
        <div className="card">
          <h2>Outcome assessment</h2>
          <EmptyState title="No assessment recorded." detail="Qualified reviewers document supported, inconclusive, no-improvement, or deterioration outcomes with uncertainty and confounding factors." />
        </div>
      </div>
      <div className="card">
        <h2>Assessment structure (placeholder)</h2>
        <ul>
          <li>Baseline and follow-up method comparability</li>
          <li>Indicators and observed changes</li>
          <li>Uncertainty, limitations, and confounding factors</li>
          <li>Reviewer decision and rationale (audited)</li>
        </ul>
      </div>
    </WorkspacePage>
  );
}
