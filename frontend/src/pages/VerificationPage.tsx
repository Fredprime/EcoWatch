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
import { errorMessage } from '../api/client';
import {
  createIndicator,
  createVerificationAssessment,
  finaliseVerificationAssessment,
  listIndicators,
  listInterventions,
  listMeasurements,
  listPublications,
  listUnits,
  listVerificationAssessments,
  publishSummary,
  recordMeasurement,
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
  const { options: orgOptions, defaultOrgId } = useOrganisationOptions(authenticated);

  const loadIndicators = useCallback(() => listIndicators(), []);
  const loadMeasurements = useCallback(() => listMeasurements(), []);
  const loadAssessments = useCallback(() => listVerificationAssessments(), []);
  const loadPublications = useCallback(() => listPublications(), []);
  const loadUnits = useCallback(() => listUnits(), []);
  const loadInterventions = useCallback(() => listInterventions(), []);
  const indicators = useApiResource(loadIndicators, 'verification-indicators', authenticated);
  const measurements = useApiResource(loadMeasurements, 'verification-measurements', authenticated);
  const assessments = useApiResource(loadAssessments, 'verification-assessments', authenticated);
  const publications = useApiResource(loadPublications, 'verification-publications', authenticated);
  const units = useApiResource(loadUnits, 'verification-units', authenticated);
  const interventions = useApiResource(loadInterventions, 'verification-interventions', authenticated);

  const [orgId, setOrgId] = useState('');
  const resolvedOrgId = orgId || defaultOrgId;

  const [indCode, setIndCode] = useState('');
  const [indName, setIndName] = useState('');
  const [indDomain, setIndDomain] = useState('water_quality');
  const [indUnitId, setIndUnitId] = useState('');
  const [indBusy, setIndBusy] = useState(false);
  const [indStatus, setIndStatus] = useState<string | null>(null);
  const [indError, setIndError] = useState<string | null>(null);

  const [measIndId, setMeasIndId] = useState('');
  const [measAt, setMeasAt] = useState(() => new Date().toISOString().slice(0, 16));
  const [measQualifier, setMeasQualifier] = useState('exact');
  const [measValue, setMeasValue] = useState('');
  const [measLimit, setMeasLimit] = useState('');
  const [measUnitId, setMeasUnitId] = useState('');
  const [measBusy, setMeasBusy] = useState(false);
  const [measStatus, setMeasStatus] = useState<string | null>(null);
  const [measError, setMeasError] = useState<string | null>(null);

  const [assessIntId, setAssessIntId] = useState('');
  const [assessMethod, setAssessMethod] = useState('before_after_comparison');
  const [assessDirection, setAssessDirection] = useState('decrease');
  const [assessBusy, setAssessBusy] = useState(false);
  const [assessStatus, setAssessStatus] = useState<string | null>(null);
  const [assessError, setAssessError] = useState<string | null>(null);

  const [finAssessId, setFinAssessId] = useState('');
  const [finBusy, setFinBusy] = useState(false);
  const [finStatus, setFinStatus] = useState<string | null>(null);
  const [finError, setFinError] = useState<string | null>(null);

  const [pubText, setPubText] = useState('');
  const [pubAssessId, setPubAssessId] = useState('');
  const [pubBusy, setPubBusy] = useState(false);
  const [pubStatus, setPubStatus] = useState<string | null>(null);
  const [pubError, setPubError] = useState<string | null>(null);

  const unitOptions =
    units.state.status === 'success'
      ? units.state.data.items.map((u) => ({ value: u.id, label: `${u.symbol} (${u.name})` }))
      : [];
  const indicatorOptions =
    indicators.state.status === 'success'
      ? indicators.state.data.items.map((i) => ({ value: i.id, label: `${i.code} — ${i.name}` }))
      : [];
  const interventionOptions =
    interventions.state.status === 'success'
      ? interventions.state.data.items.map((i) => ({
          value: i.id,
          label: `${i.objective.slice(0, 50)}${i.objective.length > 50 ? '…' : ''}`,
        }))
      : [];
  const assessmentOptions =
    assessments.state.status === 'success'
      ? assessments.state.data.items.map((a) => ({
          value: a.id,
          label: `${a.id.slice(0, 8)} — ${a.conclusion} (${a.status})`,
        }))
      : [];

  async function handleCreateIndicator(event: FormEvent) {
    event.preventDefault();
    setIndBusy(true);
    setIndStatus(null);
    setIndError(null);
    try {
      const created = await createIndicator({
        organisationId: resolvedOrgId,
        code: indCode,
        name: indName,
        domain: indDomain,
        unitId: indUnitId,
        methodName: 'standard_method',
        methodVersion: '1.0',
      });
      setIndCode('');
      setIndName('');
      setMeasIndId(created.id);
      setIndStatus(`Indicator "${created.code}" created.`);
      indicators.reload();
    } catch (err) {
      setIndError(errorMessage(err));
    } finally {
      setIndBusy(false);
    }
  }

  async function handleRecordMeasurement(event: FormEvent) {
    event.preventDefault();
    setMeasBusy(true);
    setMeasStatus(null);
    setMeasError(null);
    try {
      const created = await recordMeasurement(measIndId, {
        organisationId: resolvedOrgId,
        measuredAt: new Date(measAt).toISOString(),
        qualifier: measQualifier,
        unitId: measUnitId,
        methodName: 'field_measurement',
        methodVersion: '1.0',
        value: measValue ? Number(measValue) : null,
        detectionLimit: measLimit ? Number(measLimit) : null,
      });
      setMeasValue('');
      setMeasLimit('');
      setMeasStatus(`Measurement recorded (${created.id.slice(0, 8)}).`);
      measurements.reload();
    } catch (err) {
      setMeasError(errorMessage(err));
    } finally {
      setMeasBusy(false);
    }
  }

  async function handleCreateAssessment(event: FormEvent) {
    event.preventDefault();
    setAssessBusy(true);
    setAssessStatus(null);
    setAssessError(null);
    try {
      const created = await createVerificationAssessment({
        organisationId: resolvedOrgId,
        interventionId: assessIntId,
        comparisonMethod: assessMethod,
        direction: assessDirection,
      });
      setFinAssessId(created.id);
      setAssessStatus(`Assessment created (${created.id.slice(0, 8)}, status: ${created.status}).`);
      assessments.reload();
    } catch (err) {
      setAssessError(errorMessage(err));
    } finally {
      setAssessBusy(false);
    }
  }

  async function handleFinalise(event: FormEvent) {
    event.preventDefault();
    setFinBusy(true);
    setFinStatus(null);
    setFinError(null);
    try {
      const updated = await finaliseVerificationAssessment(finAssessId, resolvedOrgId);
      setFinStatus(`Assessment finalised (${updated.conclusion}).`);
      assessments.reload();
    } catch (err) {
      setFinError(errorMessage(err));
    } finally {
      setFinBusy(false);
    }
  }

  async function handlePublish(event: FormEvent) {
    event.preventDefault();
    setPubBusy(true);
    setPubStatus(null);
    setPubError(null);
    try {
      const created = await publishSummary({
        organisationId: resolvedOrgId,
        publishedText: pubText,
        verificationAssessmentId: pubAssessId || null,
      });
      setPubText('');
      setPubStatus(`Publication approved (${created.id.slice(0, 8)}).`);
      publications.reload();
    } catch (err) {
      setPubError(errorMessage(err));
    } finally {
      setPubBusy(false);
    }
  }

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

          <ActionPanel
            title="Create indicator definition"
            summary="Define an approved environmental indicator and measurement unit."
            statusMessage={indStatus}
            errorMessageText={indError}
            submitting={indBusy}
            submitLabel="Create indicator"
            onSubmit={handleCreateIndicator}
          >
            <RecordPicker id="ver-ind-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
            <div className="field">
              <label htmlFor="ver-ind-code">Code</label>
              <input id="ver-ind-code" value={indCode} onChange={(e) => setIndCode(e.target.value)} required placeholder="TURB-NTU" />
            </div>
            <div className="field">
              <label htmlFor="ver-ind-name">Name</label>
              <input id="ver-ind-name" value={indName} onChange={(e) => setIndName(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="ver-ind-dom">Domain</label>
              <input id="ver-ind-dom" value={indDomain} onChange={(e) => setIndDomain(e.target.value)} required />
            </div>
            <RecordPicker id="ver-ind-unit" label="Unit" value={indUnitId} onChange={setIndUnitId} options={unitOptions} />
          </ActionPanel>

          <ActionPanel
            title="Record qualified measurement"
            summary="Record a measurement with explicit qualifier and detection limit."
            statusMessage={measStatus}
            errorMessageText={measError}
            submitting={measBusy}
            submitLabel="Record measurement"
            onSubmit={handleRecordMeasurement}
          >
            <RecordPicker id="ver-m-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
            <RecordPicker id="ver-m-ind" label="Indicator" value={measIndId} onChange={setMeasIndId} options={indicatorOptions} />
            <RecordPicker id="ver-m-unit" label="Unit" value={measUnitId} onChange={setMeasUnitId} options={unitOptions} />
            <div className="field">
              <label htmlFor="ver-m-at">Measured at</label>
              <input id="ver-m-at" type="datetime-local" value={measAt} onChange={(e) => setMeasAt(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="ver-m-qual">Qualifier</label>
              <select id="ver-m-qual" value={measQualifier} onChange={(e) => setMeasQualifier(e.target.value)}>
                <option value="exact">exact</option>
                <option value="less_than">less_than</option>
                <option value="greater_than">greater_than</option>
                <option value="not_detected">not_detected</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="ver-m-val">Value (optional if not_detected)</label>
              <input id="ver-m-val" type="number" step="any" value={measValue} onChange={(e) => setMeasValue(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="ver-m-dl">Detection limit (optional)</label>
              <input id="ver-m-dl" type="number" step="any" min="0" value={measLimit} onChange={(e) => setMeasLimit(e.target.value)} />
            </div>
          </ActionPanel>

          <ActionPanel
            title="Create outcome assessment"
            summary="Create a draft observed-change assessment (never declares recovery)."
            statusMessage={assessStatus}
            errorMessageText={assessError}
            submitting={assessBusy}
            submitLabel="Create assessment"
            onSubmit={handleCreateAssessment}
          >
            <RecordPicker id="ver-a-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
            <RecordPicker id="ver-a-int" label="Intervention" value={assessIntId} onChange={setAssessIntId} options={interventionOptions} />
            <div className="field">
              <label htmlFor="ver-a-method">Comparison method</label>
              <input id="ver-a-method" value={assessMethod} onChange={(e) => setAssessMethod(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="ver-a-dir">Expected direction</label>
              <select id="ver-a-dir" value={assessDirection} onChange={(e) => setAssessDirection(e.target.value)}>
                <option value="decrease">decrease</option>
                <option value="increase">increase</option>
                <option value="either">either</option>
              </select>
            </div>
          </ActionPanel>

          <ActionPanel
            title="Finalise outcome assessment"
            summary="Finalise an existing draft assessment."
            statusMessage={finStatus}
            errorMessageText={finError}
            submitting={finBusy}
            submitLabel="Finalise assessment"
            onSubmit={handleFinalise}
          >
            <RecordPicker id="ver-fin-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
            <RecordPicker id="ver-fin-id" label="Assessment" value={finAssessId} onChange={setFinAssessId} options={assessmentOptions} />
          </ActionPanel>

          <ActionPanel
            title="Publish approved summary"
            summary="Publish an approved public summary linked to an assessment."
            statusMessage={pubStatus}
            errorMessageText={pubError}
            submitting={pubBusy}
            submitLabel="Publish summary"
            onSubmit={handlePublish}
          >
            <RecordPicker id="ver-pub-org" label="Organisation" value={resolvedOrgId} onChange={setOrgId} options={orgOptions} />
            <RecordPicker id="ver-pub-assess" label="Assessment (optional)" value={pubAssessId} onChange={setPubAssessId} options={assessmentOptions} />
            <div className="field">
              <label htmlFor="ver-pub-text">Approved public text</label>
              <textarea id="ver-pub-text" rows={3} value={pubText} onChange={(e) => setPubText(e.target.value)} required />
            </div>
          </ActionPanel>
        </div>
      )}
    </WorkspacePage>
  );
}
