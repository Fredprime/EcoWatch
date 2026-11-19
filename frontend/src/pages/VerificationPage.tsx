import { useCallback } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { SignInPrompt } from '../components/SignInPrompt';
import { ReadOnlyListCard, type ListColumn } from '../components/Phase3Views';
import { displayText, formatTime } from '../components/phase3Format';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import {
  listIndicators,
  listMeasurements,
  listPublications,
  listVerificationAssessments,
} from '../api/phase3';
import type {
  IndicatorResponse,
  MeasurementResponse,
  PublicationResponse,
  VerificationAssessmentResponse,
} from '../api/types';

const indicatorColumns: ListColumn<IndicatorResponse>[] = [
  { header: 'Code', cell: (row) => row.code },
  { header: 'Name', cell: (row) => row.name },
  { header: 'Domain', cell: (row) => row.domain.replaceAll('_', ' ') },
  { header: 'Method', cell: (row) => `${displayText(row.methodName)} ${displayText(row.methodVersion)}` },
  { header: 'Criteria', cell: (row) => displayText(row.criteriaVersion) },
  { header: 'Approved', cell: (row) => formatTime(row.approvedAt) },
];

/** Censored measurements have no value; show the qualifier and limit, never an invented number. */
function measurementValue(row: MeasurementResponse): string {
  const qualifier = row.qualifier.replaceAll('_', ' ');
  if (row.value !== null) return `${row.value} (${qualifier})`;
  if (row.detectionLimit !== null) return `${qualifier} (limit ${row.detectionLimit})`;
  return qualifier;
}

const measurementColumns: ListColumn<MeasurementResponse>[] = [
  { header: 'Indicator', cell: (row) => row.indicatorDefinitionId.slice(0, 8) },
  { header: 'Measured at', cell: (row) => formatTime(row.measuredAt) },
  { header: 'Value', cell: (row) => measurementValue(row) },
  { header: 'Method', cell: (row) => `${displayText(row.methodName)} ${displayText(row.methodVersion)}` },
  { header: 'Uncertainty', cell: (row) => displayText(row.uncertaintyNote) },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

const assessmentColumns: ListColumn<VerificationAssessmentResponse>[] = [
  { header: 'Intervention', cell: (row) => row.interventionId.slice(0, 8) },
  { header: 'Conclusion', cell: (row) => row.conclusion.replaceAll('_', ' ') },
  { header: 'Status', cell: (row) => row.status.replaceAll('_', ' ') },
  { header: 'Comparison', cell: (row) => row.comparisonMethod },
  { header: 'Criteria', cell: (row) => displayText(row.criteriaVersion) },
  { header: 'Reviewed', cell: (row) => formatTime(row.reviewedAt) },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

const publicationColumns: ListColumn<PublicationResponse>[] = [
  { header: 'Published text', cell: (row) => row.publishedText },
  { header: 'Approved role', cell: (row) => row.approvedRole.replaceAll('_', ' ') },
  { header: 'Approved at', cell: (row) => formatTime(row.approvedAt) },
  { header: 'Retracted', cell: (row) => (row.retractedAt ? formatTime(row.retractedAt) : 'No') },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

export function VerificationPage() {
  const { status } = useAuth();
  const authenticated = status === 'authenticated';

  const loadIndicators = useCallback(() => listIndicators(), []);
  const loadMeasurements = useCallback(() => listMeasurements(), []);
  const loadAssessments = useCallback(() => listVerificationAssessments(), []);
  const loadPublications = useCallback(() => listPublications(), []);
  const indicators = useApiResource(loadIndicators, 'verification-indicators', authenticated);
  const measurements = useApiResource(loadMeasurements, 'verification-measurements', authenticated);
  const assessments = useApiResource(loadAssessments, 'verification-assessments', authenticated);
  const publications = useApiResource(loadPublications, 'verification-publications', authenticated);

  return (
    <WorkspacePage
      title="Verification"
      description="Baselines, follow-up measurements and outcome assessments. Recovery claims require suitable evidence, comparison, and qualified review."
    >
      <Notice variant="warn" role="note" title="Verification boundary:">
        “Field verified” or “recovery verified” status requires authorised human review and approved
        criteria with appropriate evidence. Automated outputs do not set these statuses; these lists
        only display what has been recorded on the server.
      </Notice>

      <Notice variant="info" role="note" title="No spatial view:">
        These read APIs expose no geometry, so no map is rendered here. The lists below are the
        accessible view of every stored record in your permitted scope.
      </Notice>

      {!authenticated ? (
        <div className="card" style={{ marginTop: '1rem' }}>
          <SignInPrompt what="Verification records require an authenticated account." />
        </div>
      ) : (
        <div style={{ marginTop: '1rem', display: 'grid', gap: '1rem' }}>
          <ReadOnlyListCard<IndicatorResponse>
            title="Indicator definitions"
            note="Approved indicators with their method and criteria version."
            state={indicators.state}
            emptyTitle="No indicators in your permitted scope."
            columns={indicatorColumns}
            ariaLabel="Indicators table"
          />
          <ReadOnlyListCard<MeasurementResponse>
            title="Qualified measurements"
            note="Censored values are shown with their qualifier and detection limit; no value is invented."
            state={measurements.state}
            emptyTitle="No measurements in your permitted scope."
            columns={measurementColumns}
            ariaLabel="Measurements table"
          />
          <ReadOnlyListCard<VerificationAssessmentResponse>
            title="Outcome assessments"
            note="Conclusions are displayed only as recorded by an authorised reviewer with approved criteria."
            state={assessments.state}
            emptyTitle="No outcome assessments in your permitted scope."
            columns={assessmentColumns}
            ariaLabel="Verification assessments table"
          />
          <ReadOnlyListCard<PublicationResponse>
            title="Approved publications"
            note="Approved public text with its recorded approver and retraction state."
            state={publications.state}
            emptyTitle="No publications in your permitted scope."
            columns={publicationColumns}
            ariaLabel="Publications table"
          />
        </div>
      )}
    </WorkspacePage>
  );
}
