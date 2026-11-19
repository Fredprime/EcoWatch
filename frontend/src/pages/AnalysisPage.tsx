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
import { errorMessage } from '../api/client';
import {
  createEntity,
  listAnalysisOutputs,
  listAnalysisRuns,
  listIntelligenceEntities,
  listIntelligenceRelationships,
  proposeRelationship,
  queueAnalysisRun,
} from '../api/phase3';
import type {
  AnalysisOutputResponse,
  AnalysisRunResponse,
  EnvironmentalEntityResponse,
  EnvironmentalRelationshipResponse,
} from '../api/types';

const entityColumns: ListColumn<EnvironmentalEntityResponse>[] = [
  { header: 'Name', cell: (row) => row.name },
  { header: 'Type', cell: (row) => row.entityType.replaceAll('_', ' ') },
  { header: 'CRS', cell: (row) => row.crs },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

const relationshipColumns: ListColumn<EnvironmentalRelationshipResponse>[] = [
  { header: 'Relationship', cell: (row) => row.relationshipType.replaceAll('_', ' ') },
  { header: 'Review state', cell: (row) => row.reviewState.replaceAll('_', ' ') },
  { header: 'Method', cell: (row) => `${displayText(row.methodName)} ${displayText(row.methodVersion)}` },
  { header: 'Evidence summary', cell: (row) => row.evidenceSummary },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

const runColumns: ListColumn<AnalysisRunResponse>[] = [
  { header: 'Question', cell: (row) => row.question },
  { header: 'Analysis type', cell: (row) => row.analysisType.replaceAll('_', ' ') },
  { header: 'Status', cell: (row) => row.status.replaceAll('_', ' ') },
  { header: 'Method', cell: (row) => `${displayText(row.methodName)} ${displayText(row.methodVersion)}` },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

const outputColumns: ListColumn<AnalysisOutputResponse>[] = [
  { header: 'Output type', cell: (row) => row.outputType.replaceAll('_', ' ') },
  { header: 'Summary', cell: (row) => row.summary },
  { header: 'Interpretation', cell: (row) => row.interpretationState.replaceAll('_', ' ') },
  { header: 'Limitations', cell: (row) => row.limitations },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

export function AnalysisPage() {
  const { status } = useAuth();
  const authenticated = status === 'authenticated';
  const { options: orgOptions, defaultOrgId } = useOrganisationOptions(authenticated);

  const loadEntities = useCallback(() => listIntelligenceEntities(), []);
  const loadRelationships = useCallback(() => listIntelligenceRelationships(), []);
  const loadRuns = useCallback(() => listAnalysisRuns(), []);
  const entities = useApiResource(loadEntities, 'intelligence-entities', authenticated);
  const relationships = useApiResource(loadRelationships, 'intelligence-relationships', authenticated);
  const runs = useApiResource(loadRuns, 'analysis-runs', authenticated);

  const [selectedRunId, setSelectedRunId] = useState('');
  const loadOutputs = useCallback(() => listAnalysisOutputs(selectedRunId), [selectedRunId]);
  const outputs = useApiResource(
    loadOutputs,
    `analysis-outputs:${selectedRunId}`,
    authenticated && Boolean(selectedRunId),
  );

  const [orgId, setOrgId] = useState('');
  const resolvedOrgId = orgId || defaultOrgId;

  const [entType, setEntType] = useState('site');
  const [entName, setEntName] = useState('');
  const [entDesc, setEntDesc] = useState('');
  const [entBusy, setEntBusy] = useState(false);
  const [entStatus, setEntStatus] = useState<string | null>(null);
  const [entError, setEntError] = useState<string | null>(null);

  const [relType, setRelType] = useState('upstream_downstream');
  const [relSummary, setRelSummary] = useState('');
  const [relUncertainty, setRelUncertainty] = useState('medium');
  const [relUncertaintyNote, setRelUncertaintyNote] = useState('');
  const [relAlt, setRelAlt] = useState('');
  const [relFromId, setRelFromId] = useState('');
  const [relToId, setRelToId] = useState('');
  const [relBusy, setRelBusy] = useState(false);
  const [relStatus, setRelStatus] = useState<string | null>(null);
  const [relError, setRelError] = useState<string | null>(null);

  const [runQuestion, setRunQuestion] = useState('');
  const [runType, setRunType] = useState('water_quality_comparison');
  const [runMethod, setRunMethod] = useState('deterministic_delta');
  const [runVersion, setRunVersion] = useState('1.0');
  const [runDatasetVerIds, setRunDatasetVerIds] = useState('');
  const [runCrs, setRunCrs] = useState('EPSG:4326');
  const [runLimitations, setRunLimitations] = useState('');
  const [runBusy, setRunBusy] = useState(false);
  const [runStatus, setRunStatus] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  const entityOptions =
    entities.state.status === 'success'
      ? entities.state.data.items.map((e) => ({ value: e.id, label: `${e.name} (${e.entityType})` }))
      : [];

  async function handleCreateEntity(event: FormEvent) {
    event.preventDefault();
    setEntBusy(true);
    setEntStatus(null);
    setEntError(null);
    try {
      const created = await createEntity({
        organisationId: resolvedOrgId,
        entityType: entType,
        name: entName,
        crs: 'EPSG:4326',
        description: entDesc || null,
      });
      setEntName('');
      setEntDesc('');
      setEntStatus(`Entity "${created.name}" created.`);
      entities.reload();
    } catch (err) {
      setEntError(errorMessage(err));
    } finally {
      setEntBusy(false);
    }
  }

  async function handleProposeRelationship(event: FormEvent) {
    event.preventDefault();
    setRelBusy(true);
    setRelStatus(null);
    setRelError(null);
    try {
      const created = await proposeRelationship({
        organisationId: resolvedOrgId,
        relationshipType: relType,
        evidenceSummary: relSummary,
        uncertainty: relUncertainty,
        uncertaintyNote: relUncertaintyNote,
        alternativeExplanations: relAlt,
        methodName: 'manual_assessment',
        methodVersion: '1.0',
        fromEntityId: relFromId || null,
        toEntityId: relToId || null,
      });
      setRelSummary('');
      setRelUncertaintyNote('');
      setRelAlt('');
      setRelStatus(`Relationship proposed (${created.id.slice(0, 8)}).`);
      relationships.reload();
    } catch (err) {
      setRelError(errorMessage(err));
    } finally {
      setRelBusy(false);
    }
  }

  async function handleQueueRun(event: FormEvent) {
    event.preventDefault();
    setRunBusy(true);
    setRunStatus(null);
    setRunError(null);
    try {
      const versionIds = runDatasetVerIds
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const created = await queueAnalysisRun({
        organisationId: resolvedOrgId,
        question: runQuestion,
        analysisType: runType,
        methodName: runMethod,
        methodVersion: runVersion,
        inputDatasetVersionIds: versionIds,
        crs: runCrs,
        limitations: runLimitations,
      });
      setRunQuestion('');
      setRunLimitations('');
      setRunStatus(`Analysis run queued (${created.id.slice(0, 8)}).`);
      runs.reload();
    } catch (err) {
      setRunError(errorMessage(err));
    } finally {
      setRunBusy(false);
    }
  }

  const runOptions =
    runs.state.status === 'success'
      ? runs.state.data.items.map((run) => ({
          value: run.id,
          label: `${run.question.slice(0, 60)}${run.question.length > 60 ? '…' : ''} — ${run.status.replaceAll('_', ' ')}`,
        }))
      : [];

  const spatial = useMemo(
    () => featuresFromWkt(
      entities.state.status === 'success'
        ? entities.state.data.items.map((entity) => ({
            wkt: entity.geometry,
            label: entity.name,
          }))
        : [],
    ),
    [entities.state],
  );

  return (
    <WorkspacePage
      title="Analysis"
      description="Datasets, methods, outputs and interpretation. Derived artefacts are linked to source data and versions; interpretations are separate reviewed records."
    >
      <Notice variant="info" role="note" title="Read-only view:">
        These records are loaded from the server within your permitted scope. Run status is a
        processing state, not an environmental finding; derived outputs await human interpretation.
        Source data, methods, outputs and interpretation remain separate records.
      </Notice>

      {!authenticated ? (
        <div className="card" style={{ marginTop: '1rem' }}>
          <SignInPrompt what="Analysis records require an authenticated account." />
        </div>
      ) : (
        <div style={{ marginTop: '1rem', display: 'grid', gap: '1rem' }}>
          <div className="card">
            <h2>Stored entity geometry</h2>
            <LazyWktMap
              features={spatial.features}
              skipped={spatial.skipped}
              ariaLabel="Stored environmental entity geometry"
              emptyNote="No stored entity geometry is available in your permitted scope. The entity list below is unchanged."
            />
          </div>
          <ReadOnlyListCard<EnvironmentalEntityResponse>
            title="Environmental entities"
            note="Named areas or features referenced by analyses. Stored geometry is drawn on the map above when present; this list remains the accessible alternative."
            state={entities.state}
            emptyTitle="No environmental entities in your permitted scope."
            columns={entityColumns}
            ariaLabel="Environmental entities table"
          />
          <ReadOnlyListCard<EnvironmentalRelationshipResponse>
            title="Recorded relationships"
            note="Proposed pathways with their recorded review state. A relationship is a recorded claim, not a confirmed causal link."
            state={relationships.state}
            emptyTitle="No relationships in your permitted scope."
            columns={relationshipColumns}
            ariaLabel="Environmental relationships table"
          />
          <ReadOnlyListCard<AnalysisRunResponse>
            title="Analysis runs"
            note="Method and input provenance for each run. Status reflects processing, not a result."
            state={runs.state}
            emptyTitle="No analysis runs in your permitted scope."
            columns={runColumns}
            ariaLabel="Analysis runs table"
          />
          <div className="card">
            <h2>Derived outputs</h2>
            <RecordPicker
              id="analysis-run-picker"
              label="Analysis run"
              value={selectedRunId}
              onChange={setSelectedRunId}
              options={runOptions}
              hint="Outputs are stored per analysis run. Select a run to load its derived outputs."
            />
          </div>
          <ReadOnlyListCard<AnalysisOutputResponse>
            title="Outputs for the selected run"
            note="Derived artefacts remain linked to their inputs; interpretation is a separate reviewed record."
            state={outputs.state}
            emptyTitle="No outputs recorded for this run."
            columns={outputColumns}
            ariaLabel="Analysis outputs table"
            idleNote="Choose an analysis run above to load its derived outputs."
          />

          <ActionPanel
            title="Create environmental entity"
            summary="Register a site, catchment, waterbody, habitat, or monitored asset."
            statusMessage={entStatus}
            errorMessageText={entError}
            submitting={entBusy}
            submitLabel="Create entity"
            onSubmit={handleCreateEntity}
          >
            <RecordPicker id="an-ent-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
            <div className="field">
              <label htmlFor="an-ent-type">Entity type</label>
              <select id="an-ent-type" value={entType} onChange={(e) => setEntType(e.target.value)}>
                <option value="site">site</option>
                <option value="catchment">catchment</option>
                <option value="sub_catchment">sub_catchment</option>
                <option value="waterbody">waterbody</option>
                <option value="habitat">habitat</option>
                <option value="monitored_asset">monitored_asset</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="an-ent-name">Name</label>
              <input id="an-ent-name" value={entName} onChange={(e) => setEntName(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="an-ent-desc">Description (optional)</label>
              <input id="an-ent-desc" value={entDesc} onChange={(e) => setEntDesc(e.target.value)} />
            </div>
          </ActionPanel>

          <ActionPanel
            title="Propose environmental relationship"
            summary="Record an evidence-backed, explicitly uncertain pathway between entities."
            statusMessage={relStatus}
            errorMessageText={relError}
            submitting={relBusy}
            submitLabel="Propose relationship"
            onSubmit={handleProposeRelationship}
          >
            <RecordPicker id="an-rel-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
            <RecordPicker id="an-rel-from" label="From entity" value={relFromId} onChange={setRelFromId} options={entityOptions} />
            <RecordPicker id="an-rel-to" label="To entity" value={relToId} onChange={setRelToId} options={entityOptions} />
            <div className="field">
              <label htmlFor="an-rel-type">Relationship type</label>
              <select id="an-rel-type" value={relType} onChange={(e) => setRelType(e.target.value)}>
                <option value="upstream_downstream">upstream_downstream</option>
                <option value="source_pathway_receptor">source_pathway_receptor</option>
                <option value="habitat_connectivity">habitat_connectivity</option>
                <option value="temporal_association">temporal_association</option>
                <option value="spatial_adjacency">spatial_adjacency</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="an-rel-uncertainty">Uncertainty</label>
              <select id="an-rel-uncertainty" value={relUncertainty} onChange={(e) => setRelUncertainty(e.target.value)}>
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
                <option value="unknown">unknown</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="an-rel-summary">Evidence summary</label>
              <input id="an-rel-summary" value={relSummary} onChange={(e) => setRelSummary(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="an-rel-unote">Uncertainty note</label>
              <input id="an-rel-unote" value={relUncertaintyNote} onChange={(e) => setRelUncertaintyNote(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="an-rel-alt">Alternative explanations</label>
              <input id="an-rel-alt" value={relAlt} onChange={(e) => setRelAlt(e.target.value)} required />
            </div>
          </ActionPanel>

          <ActionPanel
            title="Queue analysis run"
            summary="Queue a reproducible analysis run linked to dataset version UUIDs."
            statusMessage={runStatus}
            errorMessageText={runError}
            submitting={runBusy}
            submitLabel="Queue analysis run"
            onSubmit={handleQueueRun}
          >
            <RecordPicker id="an-run-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
            <div className="field">
              <label htmlFor="an-run-q">Research / analysis question</label>
              <input id="an-run-q" value={runQuestion} onChange={(e) => setRunQuestion(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="an-run-type">Analysis type</label>
              <select id="an-run-type" value={runType} onChange={(e) => setRunType(e.target.value)}>
                <option value="water_quality_comparison">water_quality_comparison</option>
                <option value="land_cover_change">land_cover_change</option>
                <option value="historical_comparison">historical_comparison</option>
                <option value="custom">custom</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="an-run-method">Method name</label>
              <input id="an-run-method" value={runMethod} onChange={(e) => setRunMethod(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="an-run-ver">Method version</label>
              <input id="an-run-ver" value={runVersion} onChange={(e) => setRunVersion(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="an-run-dvs">Input dataset version UUIDs (comma-separated)</label>
              <input id="an-run-dvs" value={runDatasetVerIds} onChange={(e) => setRunDatasetVerIds(e.target.value)} required placeholder="uuid1, uuid2" />
            </div>
            <div className="field">
              <label htmlFor="an-run-crs">CRS</label>
              <input id="an-run-crs" value={runCrs} onChange={(e) => setRunCrs(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="an-run-lim">Limitations</label>
              <input id="an-run-lim" value={runLimitations} onChange={(e) => setRunLimitations(e.target.value)} required />
            </div>
          </ActionPanel>
        </div>
      )}
    </WorkspacePage>
  );
}
