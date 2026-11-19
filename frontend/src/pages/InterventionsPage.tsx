import { useCallback, useMemo, useState } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { SignInPrompt } from '../components/SignInPrompt';
import { LazyWktMap } from '../components/LazyWktMap';
import { featuresFromWkt } from '../components/wkt';
import {
  ReadOnlyListCard,
  RecordPicker,
  type ListColumn,
} from '../components/Phase3Views';
import { displayText, formatTime } from '../components/phase3Format';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import { listInterventions, listMilestones } from '../api/phase3';
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
  const { status } = useAuth();
  const authenticated = status === 'authenticated';

  const loadInterventions = useCallback(() => listInterventions(), []);
  const interventions = useApiResource(loadInterventions, 'interventions', authenticated);

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
        </div>
      )}
    </WorkspacePage>
  );
}
