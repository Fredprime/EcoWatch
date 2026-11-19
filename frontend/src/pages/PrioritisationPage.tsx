import { useCallback, useState, type FormEvent } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { SignInPrompt } from '../components/SignInPrompt';
import {
  ActionPanel,
  ReadOnlyListCard,
  RecordPicker,
  type ListColumn,
} from '../components/Phase3Views';
import { useOrganisationOptions } from '../hooks/useOrganisationOptions';
import { displayText, formatTime } from '../components/phase3Format';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import { listCases } from '../api/cases';
import { errorMessage } from '../api/client';
import {
  createPrioritisationAssessment,
  listPrioritisationAssessments,
  recordPrioritisationDecision,
} from '../api/phase3';
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
  const { options: orgOptions, defaultOrgId } = useOrganisationOptions(authenticated);

  const loadAssessments = useCallback(() => listPrioritisationAssessments(), []);
  const assessments = useApiResource(loadAssessments, 'prioritisation-assessments', authenticated);
  const loadCases = useCallback(() => listCases(), []);
  const cases = useApiResource(loadCases, 'prioritisation-cases', authenticated);

  const [orgId, setOrgId] = useState('');
  const resolvedOrgId = orgId || defaultOrgId;

  const [caseId, setCaseId] = useState('');
  const [methodName, setMethodName] = useState('transparent_factor_matrix');
  const [methodVersion, setMethodVersion] = useState('1.0');
  const [compositeRank, setCompositeRank] = useState('');
  const [createBusy, setCreateBusy] = useState(false);
  const [createStatus, setCreateStatus] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  const [decisionAssessmentId, setDecisionAssessmentId] = useState('');
  const [decision, setDecision] = useState('priority_set');
  const [rationale, setRationale] = useState('');
  const [decBusy, setDecBusy] = useState(false);
  const [decStatus, setDecStatus] = useState<string | null>(null);
  const [decError, setDecError] = useState<string | null>(null);

  const caseOptions =
    cases.state.status === 'success'
      ? cases.state.data.items.map((c) => ({ value: c.id, label: `${c.caseCode} — ${c.title}` }))
      : [];
  const assessmentOptions =
    assessments.state.status === 'success'
      ? assessments.state.data.items.map((a) => ({
          value: a.id,
          label: `${a.id.slice(0, 8)} (${a.methodName})`,
        }))
      : [];

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setCreateBusy(true);
    setCreateStatus(null);
    setCreateError(null);
    try {
      const created = await createPrioritisationAssessment({
        organisationId: resolvedOrgId,
        caseId,
        methodName,
        methodVersion,
        compositeRank: compositeRank ? Number(compositeRank) : null,
        rankIsNotSeverity: true,
      });
      setCompositeRank('');
      setDecisionAssessmentId(created.id);
      setCreateStatus(`Assessment recorded (${created.id.slice(0, 8)}).`);
      assessments.reload();
    } catch (err) {
      setCreateError(errorMessage(err));
    } finally {
      setCreateBusy(false);
    }
  }

  async function handleDecision(event: FormEvent) {
    event.preventDefault();
    setDecBusy(true);
    setDecStatus(null);
    setDecError(null);
    try {
      const updated = await recordPrioritisationDecision(decisionAssessmentId, {
        organisationId: resolvedOrgId,
        decision,
        rationale,
      });
      setRationale('');
      setDecStatus(`Decision "${updated.decision}" recorded.`);
      assessments.reload();
    } catch (err) {
      setDecError(errorMessage(err));
    } finally {
      setDecBusy(false);
    }
  }

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
          <div style={{ display: 'grid', gap: '1rem' }}>
            <ReadOnlyListCard<PrioritisationAssessmentResponse>
              title="Prioritisation records"
              note="Factors, documented gaps and any recorded human decision are shown together. A rank is never a severity determination."
              state={assessments.state}
              emptyTitle="No prioritisation records in your permitted scope."
              emptyDetail="Records appear here after an authorised reviewer records an assessment."
              columns={assessmentColumns}
              ariaLabel="Prioritisation assessments table"
            />

            <ActionPanel
              title="Create prioritisation assessment"
              summary="Record transparent prioritisation factors for a case. Missing inputs are never imputed."
              statusMessage={createStatus}
              errorMessageText={createError}
              submitting={createBusy}
              submitLabel="Create assessment"
              onSubmit={handleCreate}
            >
              <RecordPicker id="pr-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
              <RecordPicker id="pr-case" label="Case" value={caseId} onChange={setCaseId} options={caseOptions} />
              <div className="field">
                <label htmlFor="pr-method">Method name</label>
                <input id="pr-method" value={methodName} onChange={(e) => setMethodName(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="pr-ver">Method version</label>
                <input id="pr-ver" value={methodVersion} onChange={(e) => setMethodVersion(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="pr-rank">Composite rank signal (optional, never severity)</label>
                <input id="pr-rank" type="number" step="any" min="0" value={compositeRank} onChange={(e) => setCompositeRank(e.target.value)} />
              </div>
            </ActionPanel>

            <ActionPanel
              title="Record human prioritisation decision"
              summary="Record an accountable human decision and rationale on an existing assessment."
              statusMessage={decStatus}
              errorMessageText={decError}
              submitting={decBusy}
              submitLabel="Record decision"
              onSubmit={handleDecision}
            >
              <RecordPicker id="pr-dec-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
              <RecordPicker id="pr-dec-assess" label="Assessment" value={decisionAssessmentId} onChange={setDecisionAssessmentId} options={assessmentOptions} />
              <div className="field">
                <label htmlFor="pr-dec-val">Decision</label>
                <select id="pr-dec-val" value={decision} onChange={(e) => setDecision(e.target.value)}>
                  <option value="priority_set">priority_set</option>
                  <option value="deferred">deferred</option>
                  <option value="no_action">no_action</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="pr-dec-rat">Rationale</label>
                <input id="pr-dec-rat" value={rationale} onChange={(e) => setRationale(e.target.value)} required />
              </div>
            </ActionPanel>
          </div>
        )}
      </div>
    </WorkspacePage>
  );
}
