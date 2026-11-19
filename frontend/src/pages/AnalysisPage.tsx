import { useCallback, useState } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { SignInPrompt } from '../components/SignInPrompt';
import {
  ReadOnlyListCard,
  RecordPicker,
  type ListColumn,
} from '../components/Phase3Views';
import { displayText, formatTime } from '../components/phase3Format';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import {
  listAnalysisOutputs,
  listAnalysisRuns,
  listIntelligenceEntities,
  listIntelligenceRelationships,
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

  const runOptions =
    runs.state.status === 'success'
      ? runs.state.data.items.map((run) => ({
          value: run.id,
          label: `${run.question.slice(0, 60)}${run.question.length > 60 ? '…' : ''} — ${run.status.replaceAll('_', ' ')}`,
        }))
      : [];

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
          <ReadOnlyListCard<EnvironmentalEntityResponse>
            title="Environmental entities"
            note="Named areas or features referenced by analyses. Precise geometry is not rendered in this list."
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
        </div>
      )}
    </WorkspacePage>
  );
}
