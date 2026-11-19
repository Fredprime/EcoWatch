import { useCallback } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { SignInPrompt } from '../components/SignInPrompt';
import { ReadOnlyListCard, type ListColumn } from '../components/Phase3Views';
import { displayText, formatTime } from '../components/phase3Format';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import { listPrioritisationAssessments } from '../api/phase3';
import type { PrioritisationAssessmentResponse } from '../api/types';

const assessmentColumns: ListColumn<PrioritisationAssessmentResponse>[] = [
  { header: 'Case', cell: (row) => row.caseId.slice(0, 8) },
  { header: 'Method', cell: (row) => `${displayText(row.methodName)} ${displayText(row.methodVersion)}` },
  { header: 'Rank (signal only)', cell: (row) => (row.compositeRank === null ? 'Not provided' : String(row.compositeRank)) },
  { header: 'Decision', cell: (row) => (row.decision ? row.decision.replaceAll('_', ' ') : 'Not recorded') },
  { header: 'Decision rationale', cell: (row) => displayText(row.decisionRationale) },
  { header: 'Reviewed', cell: (row) => formatTime(row.reviewedAt) },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

export function PrioritisationPage() {
  const { status } = useAuth();
  const authenticated = status === 'authenticated';

  const loadAssessments = useCallback(() => listPrioritisationAssessments(), []);
  const assessments = useApiResource(loadAssessments, 'prioritisation-assessments', authenticated);

  return (
    <WorkspacePage
      title="Prioritisation"
      description="Transparent factors and human review decisions. The system supports prioritisation; it does not independently decide enforcement or public-safety action."
    >
      <Notice variant="warn" role="note" title="Decision support only:">
        Prioritisation factors and rankings are aids for authorised human review. They are not
        automated enforcement, severity, or truth determinations. A rank is a ranking signal, not a
        probability, severity or danger level.
      </Notice>

      <Notice variant="info" role="note" title="No spatial view:">
        This read API exposes no geometry, so no map is rendered here. The list below is the
        accessible view of every stored record in your permitted scope.
      </Notice>

      <div style={{ marginTop: '1rem' }}>
        {!authenticated ? (
          <div className="card">
            <SignInPrompt what="Prioritisation records require an authenticated account." />
          </div>
        ) : (
          <ReadOnlyListCard<PrioritisationAssessmentResponse>
            title="Prioritisation records"
            note="Factors, documented gaps and any recorded human decision are shown together. A rank is never a severity determination."
            state={assessments.state}
            emptyTitle="No prioritisation records in your permitted scope."
            emptyDetail="Records appear here after an authorised reviewer records an assessment."
            columns={assessmentColumns}
            ariaLabel="Prioritisation assessments table"
          />
        )}
      </div>
    </WorkspacePage>
  );
}
