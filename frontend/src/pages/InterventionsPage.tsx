import { useCallback, useMemo, useState, type FormEvent } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { SignInPrompt } from '../components/SignInPrompt';
import { LazyWktMap } from '../components/LazyWktMap';
import { featuresFromWkt } from '../components/wkt';
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
  addMilestone,
  completeMilestone,
  createIntervention,
  listInterventions,
  listMilestones,
  transitionIntervention,
} from '../api/phase3';
import type { InterventionResponse, MilestoneResponse } from '../api/types';

const interventionColumns: ListColumn<InterventionResponse>[] = [
  { header: 'Objective', cell: (row) => row.objective },
  { header: 'Status', cell: (row) => row.status.replaceAll('_', ' ') },
  { header: 'Case', cell: (row) => row.caseId.slice(0, 8) },
  { header: 'Planned start', cell: (row) => formatTime(row.plannedStartAt) },
  { header: 'Baseline', cell: (row) => displayText(row.baselineSummary) },
  { header: 'Intended outcome', cell: (row) => displayText(row.intendedOutcome) },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

const milestoneColumns: ListColumn<MilestoneResponse>[] = [
  { header: 'Milestone', cell: (row) => row.name },
  { header: 'Status', cell: (row) => row.status.replaceAll('_', ' ') },
  { header: 'Planned', cell: (row) => formatTime(row.plannedAt) },
  { header: 'Completed', cell: (row) => formatTime(row.completedAt) },
  { header: 'Description', cell: (row) => displayText(row.description) },
];

export function InterventionsPage() {
  const { status, me } = useAuth();
  const authenticated = status === 'authenticated';
  const { options: orgOptions, defaultOrgId } = useOrganisationOptions(authenticated);

  const loadInterventions = useCallback(() => listInterventions(), []);
  const interventions = useApiResource(loadInterventions, 'interventions', authenticated);
  const loadCases = useCallback(() => listCases(), []);
  const cases = useApiResource(loadCases, 'intervention-cases', authenticated);

  const [selectedInterventionId, setSelectedInterventionId] = useState('');
  const loadMilestones = useCallback(
    () => listMilestones(selectedInterventionId),
    [selectedInterventionId],
  );
  const milestones = useApiResource(
    loadMilestones,
    `intervention-milestones:${selectedInterventionId}`,
    authenticated && Boolean(selectedInterventionId),
  );

  const [orgId, setOrgId] = useState('');
  const resolvedOrgId = orgId || defaultOrgId;

  const [caseId, setCaseId] = useState('');
  const [objective, setObjective] = useState('');
  const [rationale, setRationale] = useState('');
  const [createBusy, setCreateBusy] = useState(false);
  const [createStatus, setCreateStatus] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  const [msName, setMsName] = useState('');
  const [msDesc, setMsDesc] = useState('');
  const [msBusy, setMsBusy] = useState(false);
  const [msStatus, setMsStatus] = useState<string | null>(null);
  const [msError, setMsError] = useState<string | null>(null);

  const [completeMsId, setCompleteMsId] = useState('');
  const [compBusy, setCompBusy] = useState(false);
  const [compStatus, setCompStatus] = useState<string | null>(null);
  const [compError, setCompError] = useState<string | null>(null);

  const [targetStatus, setTargetStatus] = useState('approved');
  const [transRationale, setTransRationale] = useState('');
  const [transBusy, setTransBusy] = useState(false);
  const [transStatus, setTransStatus] = useState<string | null>(null);
  const [transError, setTransError] = useState<string | null>(null);

  const caseOptions =
    cases.state.status === 'success'
      ? cases.state.data.items.map((c) => ({ value: c.id, label: `${c.caseCode} — ${c.title}` }))
      : [];
  const milestoneOptions =
    milestones.state.status === 'success'
      ? milestones.state.data.items.map((m) => ({ value: m.id, label: `${m.name} (${m.status})` }))
      : [];

  async function handleCreateIntervention(event: FormEvent) {
    event.preventDefault();
    setCreateBusy(true);
    setCreateStatus(null);
    setCreateError(null);
    try {
      const created = await createIntervention({
        organisationId: resolvedOrgId,
        caseId,
        objective,
        responsibleOrganisationId: resolvedOrgId,
        authorisedLeadUserId: me?.id ?? '',
        rationale: rationale || null,
      });
      setObjective('');
      setRationale('');
      setSelectedInterventionId(created.id);
      setCreateStatus(`Intervention created (${created.id.slice(0, 8)}).`);
      interventions.reload();
    } catch (err) {
      setCreateError(errorMessage(err));
    } finally {
      setCreateBusy(false);
    }
  }

  async function handleAddMilestone(event: FormEvent) {
    event.preventDefault();
    if (!selectedInterventionId) {
      setMsError('Select an intervention above first.');
      return;
    }
    setMsBusy(true);
    setMsStatus(null);
    setMsError(null);
    try {
      const created = await addMilestone(selectedInterventionId, {
        organisationId: resolvedOrgId,
        name: msName,
        description: msDesc || null,
      });
      setMsName('');
      setMsDesc('');
      setMsStatus(`Milestone "${created.name}" added.`);
      milestones.reload();
    } catch (err) {
      setMsError(errorMessage(err));
    } finally {
      setMsBusy(false);
    }
  }

  async function handleCompleteMilestone(event: FormEvent) {
    event.preventDefault();
    setCompBusy(true);
    setCompStatus(null);
    setCompError(null);
    try {
      const updated = await completeMilestone(completeMsId, resolvedOrgId);
      setCompStatus(`Milestone "${updated.name}" marked completed.`);
      milestones.reload();
    } catch (err) {
      setCompError(errorMessage(err));
    } finally {
      setCompBusy(false);
    }
  }

  async function handleTransition(event: FormEvent) {
    event.preventDefault();
    if (!selectedInterventionId) {
      setTransError('Select an intervention above first.');
      return;
    }
    setTransBusy(true);
    setTransStatus(null);
    setTransError(null);
    try {
      const updated = await transitionIntervention(selectedInterventionId, {
        organisationId: resolvedOrgId,
        targetStatus,
        rationale: transRationale,
      });
      setTransRationale('');
      setTransStatus(`Intervention transitioned to "${updated.status}".`);
      interventions.reload();
    } catch (err) {
      setTransError(errorMessage(err));
    } finally {
      setTransBusy(false);
    }
  }

  const interventionOptions =
    interventions.state.status === 'success'
      ? interventions.state.data.items.map((intervention) => ({
          value: intervention.id,
          label: `${intervention.objective.slice(0, 60)}${intervention.objective.length > 60 ? '…' : ''}`,
        }))
      : [];

  const spatial = useMemo(
    () => featuresFromWkt(
      interventions.state.status === 'success'
        ? interventions.state.data.items.map((intervention) => ({
            wkt: intervention.location,
            label: intervention.objective.slice(0, 60),
          }))
        : [],
    ),
    [interventions.state],
  );

  return (
    <WorkspacePage
      title="Interventions"
      description="Approved actions, owners, milestones and records. Activity completion is distinct from environmental outcome."
    >
      <Notice variant="info" role="note" title="Outcome distinction:">
        Recording an intervention or completed activity does not demonstrate environmental recovery.
        Outcomes are assessed separately with suitable evidence by an authorised reviewer.
      </Notice>

      {!authenticated ? (
        <div className="card" style={{ marginTop: '1rem' }}>
          <SignInPrompt what="Intervention records require an authenticated account." />
        </div>
      ) : (
        <div style={{ marginTop: '1rem', display: 'grid', gap: '1rem' }}>
          <div className="card">
            <h2>Stored intervention locations</h2>
            <LazyWktMap
              features={spatial.features}
              skipped={spatial.skipped}
              ariaLabel="Stored intervention location geometry"
              emptyNote="No stored intervention location geometry is available in your permitted scope. The intervention list below is unchanged."
            />
          </div>
          <ReadOnlyListCard<InterventionResponse>
            title="Intervention records"
            note="Approved actions with their recorded accountable owner and status. Stored locations are drawn on the map above when present; this list remains the accessible alternative. Responsible organisation and lead are recorded on the server, not exposed as a public view."
            state={interventions.state}
            emptyTitle="No interventions in your permitted scope."
            columns={interventionColumns}
            ariaLabel="Interventions table"
          />
          <div className="card">
            <h2>Delivery milestones</h2>
            <RecordPicker
              id="intervention-picker"
              label="Intervention"
              value={selectedInterventionId}
              onChange={setSelectedInterventionId}
              options={interventionOptions}
              hint="Milestones are stored per intervention. Select an intervention to load its milestones."
            />
          </div>
          <ReadOnlyListCard<MilestoneResponse>
            title="Milestones for the selected intervention"
            note="A completed milestone is an activity record, not evidence of an environmental outcome."
            state={milestones.state}
            emptyTitle="No milestones recorded for this intervention."
            columns={milestoneColumns}
            ariaLabel="Intervention milestones table"
            idleNote="Choose an intervention above to load its milestones."
          />

          <ActionPanel
            title="Create intervention"
            summary="Record an approved or proposed intervention linked to a case."
            statusMessage={createStatus}
            errorMessageText={createError}
            submitting={createBusy}
            submitLabel="Create intervention"
            onSubmit={handleCreateIntervention}
          >
            <RecordPicker id="int-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
            <RecordPicker id="int-case" label="Case" value={caseId} onChange={setCaseId} options={caseOptions} />
            <div className="field">
              <label htmlFor="int-obj">Objective</label>
              <input id="int-obj" value={objective} onChange={(e) => setObjective(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="int-rat">Rationale (optional)</label>
              <input id="int-rat" value={rationale} onChange={(e) => setRationale(e.target.value)} />
            </div>
          </ActionPanel>

          <ActionPanel
            title="Add milestone"
            summary="Add a delivery milestone to the selected intervention above."
            statusMessage={msStatus}
            errorMessageText={msError}
            submitting={msBusy}
            submitLabel="Add milestone"
            onSubmit={handleAddMilestone}
          >
            <div className="field">
              <label htmlFor="int-ms-name">Milestone name</label>
              <input id="int-ms-name" value={msName} onChange={(e) => setMsName(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="int-ms-desc">Description (optional)</label>
              <input id="int-ms-desc" value={msDesc} onChange={(e) => setMsDesc(e.target.value)} />
            </div>
          </ActionPanel>

          <ActionPanel
            title="Complete milestone"
            summary="Record activity completion for a milestone (never sets environmental outcome)."
            statusMessage={compStatus}
            errorMessageText={compError}
            submitting={compBusy}
            submitLabel="Complete milestone"
            onSubmit={handleCompleteMilestone}
          >
            <RecordPicker id="int-comp-ms" label="Milestone" value={completeMsId} onChange={setCompleteMsId} options={milestoneOptions} />
          </ActionPanel>

          <ActionPanel
            title="Transition intervention status"
            summary="Record an explicit status transition with rationale for the selected intervention."
            statusMessage={transStatus}
            errorMessageText={transError}
            submitting={transBusy}
            submitLabel="Transition status"
            onSubmit={handleTransition}
          >
            <div className="field">
              <label htmlFor="int-tr-status">Target status</label>
              <select id="int-tr-status" value={targetStatus} onChange={(e) => setTargetStatus(e.target.value)}>
                <option value="approved">approved</option>
                <option value="scheduled">scheduled</option>
                <option value="in_progress">in_progress</option>
                <option value="activity_completed">activity_completed</option>
                <option value="outcome_monitoring">outcome_monitoring</option>
                <option value="cancelled">cancelled</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="int-tr-rat">Rationale</label>
              <input id="int-tr-rat" value={transRationale} onChange={(e) => setTransRationale(e.target.value)} required />
            </div>
          </ActionPanel>
        </div>
      )}
    </WorkspacePage>
  );
}
