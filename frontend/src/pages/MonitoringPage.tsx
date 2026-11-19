import { useCallback, useMemo, useState, type FormEvent } from 'react';
import { WorkspacePage } from './WorkspacePage';
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
import { formatTime } from '../components/phase3Format';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import { errorMessage } from '../api/client';
import {
  addDatasetVersion,
  createDataset,
  listDatasetVersions,
  listDatasets,
} from '../api/phase3';
import type { DatasetResponse, DatasetVersionResponse } from '../api/types';

const datasetColumns: ListColumn<DatasetResponse>[] = [
  { header: 'Dataset', cell: (row) => row.name },
  { header: 'Owner', cell: (row) => row.owner },
  { header: 'Licence', cell: (row) => row.licence },
  { header: 'CRS', cell: (row) => row.crs },
  {
    header: 'Coverage',
    cell: (row) =>
      row.coverageStartAt || row.coverageEndAt
        ? `${formatTime(row.coverageStartAt)} – ${formatTime(row.coverageEndAt)}`
        : 'Not provided',
  },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

const versionColumns: ListColumn<DatasetVersionResponse>[] = [
  { header: 'Version', cell: (row) => row.versionLabel },
  { header: 'Acquired', cell: (row) => formatTime(row.sourceAcquisitionAt) },
  { header: 'Resolution', cell: (row) => row.resolution },
  { header: 'Method', cell: (row) => row.method },
  { header: 'Licence snapshot', cell: (row) => row.licenceSnapshot },
  { header: 'Created', cell: (row) => formatTime(row.createdAt) },
];

export function MonitoringPage() {
  const { status } = useAuth();
  const authenticated = status === 'authenticated';
  const { options: orgOptions, defaultOrgId } = useOrganisationOptions(authenticated);

  const loadDatasets = useCallback(() => listDatasets(), []);
  const datasets = useApiResource(loadDatasets, 'catalogue-datasets', authenticated);

  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const loadVersions = useCallback(() => listDatasetVersions(selectedDatasetId), [selectedDatasetId]);
  const versions = useApiResource(
    loadVersions,
    `dataset-versions:${selectedDatasetId}`,
    authenticated && Boolean(selectedDatasetId),
  );

  const [dsOrgId, setDsOrgId] = useState('');
  const [dsName, setDsName] = useState('');
  const [dsOwner, setDsOwner] = useState('');
  const [dsLicence, setDsLicence] = useState('CC-BY-4.0');
  const [dsAttribution, setDsAttribution] = useState('');
  const [dsPermittedUse, setDsPermittedUse] = useState('Monitoring and research');
  const [dsCrs, setDsCrs] = useState('EPSG:4326');
  const [dsGeometry, setDsGeometry] = useState('');
  const [dsBusy, setDsBusy] = useState(false);
  const [dsStatus, setDsStatus] = useState<string | null>(null);
  const [dsError, setDsError] = useState<string | null>(null);

  const [verLabel, setVerLabel] = useState('v1.0');
  const [verResolution, setVerResolution] = useState('10m');
  const [verMethod, setVerMethod] = useState('');
  const [verAcquiredAt, setVerAcquiredAt] = useState(() => new Date().toISOString().slice(0, 16));
  const [verLimitations, setVerLimitations] = useState('');
  const [verBusy, setVerBusy] = useState(false);
  const [verStatus, setVerStatus] = useState<string | null>(null);
  const [verError, setVerError] = useState<string | null>(null);

  const resolvedOrgId = dsOrgId || defaultOrgId;

  async function handleCreateDataset(event: FormEvent) {
    event.preventDefault();
    setDsBusy(true);
    setDsStatus(null);
    setDsError(null);
    try {
      const created = await createDataset({
        organisationId: resolvedOrgId,
        name: dsName,
        owner: dsOwner,
        licence: dsLicence,
        attribution: dsAttribution,
        permittedUse: dsPermittedUse,
        crs: dsCrs,
        coverageGeometry: dsGeometry || null,
      });
      setDsName('');
      setDsOwner('');
      setDsAttribution('');
      setDsGeometry('');
      setSelectedDatasetId(created.id);
      setDsStatus(`Dataset "${created.name}" registered.`);
      datasets.reload();
    } catch (err) {
      setDsError(errorMessage(err));
    } finally {
      setDsBusy(false);
    }
  }

  async function handleAddVersion(event: FormEvent) {
    event.preventDefault();
    if (!selectedDatasetId) {
      setVerError('Select a dataset above first.');
      return;
    }
    setVerBusy(true);
    setVerStatus(null);
    setVerError(null);
    try {
      const created = await addDatasetVersion(selectedDatasetId, {
        organisationId: resolvedOrgId,
        versionLabel: verLabel,
        sourceAcquisitionAt: new Date(verAcquiredAt).toISOString(),
        resolution: verResolution,
        crs: dsCrs,
        method: verMethod,
        licence: dsLicence,
        attribution: dsAttribution || 'Dataset owner attribution',
        permittedUse: dsPermittedUse,
        limitations: verLimitations || null,
      });
      setVerMethod('');
      setVerLimitations('');
      setVerStatus(`Version "${created.versionLabel}" recorded.`);
      versions.reload();
    } catch (err) {
      setVerError(errorMessage(err));
    } finally {
      setVerBusy(false);
    }
  }

  const datasetOptions =
    datasets.state.status === 'success'
      ? datasets.state.data.items.map((dataset) => ({
          value: dataset.id,
          label: dataset.name,
        }))
      : [];

  const spatial = useMemo(
    () => featuresFromWkt(
      datasets.state.status === 'success'
        ? datasets.state.data.items.map((dataset) => ({
            wkt: dataset.coverageGeometry,
            label: dataset.name,
          }))
        : [],
    ),
    [datasets.state],
  );

  return (
    <WorkspacePage
      title="Environmental Monitoring"
      description="Maps, monitored areas, indicators and historical layers. Outputs must show data quality, uncertainty and method limitations where relevant."
    >
      <div className="grid grid-2">
        <div className="card">
          <h2>Stored coverage geometry</h2>
          <LazyWktMap
            features={spatial.features}
            skipped={spatial.skipped}
            ariaLabel="Stored dataset coverage geometry"
            emptyNote="No stored coverage geometry is available in your permitted scope. The dataset list below is unchanged."
          />
        </div>
        <div className="card">
          <h2>List and detail alternative</h2>
          <p className="muted">Map is not the only way to understand records. The accessible list below shows the datasets and versions currently stored within your permitted scope.</p>
          <p className="muted">Method, period, baseline, coverage and seasonality are shown with each record when present. Missing values and locations are never invented.</p>
        </div>
      </div>

      <div style={{ marginTop: '1rem', display: 'grid', gap: '1rem' }}>
        {!authenticated ? (
          <div className="card">
            <SignInPrompt what="Monitoring records require an authenticated account." />
          </div>
        ) : (
          <>
            <ReadOnlyListCard<DatasetResponse>
              title="Datasets"
              note="Each dataset records its licence, attribution and permitted use. Stored coverage geometry is drawn on the map above when present; this list remains the accessible alternative."
              state={datasets.state}
              emptyTitle="No datasets in your permitted scope."
              columns={datasetColumns}
              ariaLabel="Datasets table"
            />
            <div className="card">
              <h2>Dataset versions</h2>
              <RecordPicker
                id="dataset-picker"
                label="Dataset"
                value={selectedDatasetId}
                onChange={setSelectedDatasetId}
                options={datasetOptions}
                hint="Versions are stored per dataset. Select a dataset to load its provenance snapshots."
              />
            </div>
            <ReadOnlyListCard<DatasetVersionResponse>
              title="Versions for the selected dataset"
              note="Each version is a complete, immutable provenance snapshot."
              state={versions.state}
              emptyTitle="No versions recorded for this dataset."
              columns={versionColumns}
              ariaLabel="Dataset versions table"
              idleNote="Choose a dataset above to load its versions."
            />

            <ActionPanel
              title="Register dataset"
              summary="Record a dataset with rights, attribution, permitted use, and CRS."
              statusMessage={dsStatus}
              errorMessageText={dsError}
              submitting={dsBusy}
              submitLabel="Register dataset"
              onSubmit={handleCreateDataset}
            >
              <RecordPicker
                id="mon-ds-org"
                label="Organisation"
                value={resolvedOrgId}
                onChange={setDsOrgId}
                options={orgOptions}
              />
              <div className="field">
                <label htmlFor="mon-ds-name">Dataset name</label>
                <input id="mon-ds-name" value={dsName} onChange={(e) => setDsName(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ds-owner">Owner / provider</label>
                <input id="mon-ds-owner" value={dsOwner} onChange={(e) => setDsOwner(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ds-licence">Licence</label>
                <input id="mon-ds-licence" value={dsLicence} onChange={(e) => setDsLicence(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ds-attr">Attribution</label>
                <input id="mon-ds-attr" value={dsAttribution} onChange={(e) => setDsAttribution(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ds-use">Permitted use</label>
                <input id="mon-ds-use" value={dsPermittedUse} onChange={(e) => setDsPermittedUse(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ds-crs">CRS</label>
                <input id="mon-ds-crs" value={dsCrs} onChange={(e) => setDsCrs(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ds-geom">Coverage geometry WKT (optional)</label>
                <input id="mon-ds-geom" value={dsGeometry} onChange={(e) => setDsGeometry(e.target.value)} placeholder="POINT(-1.6244 6.6885)" />
              </div>
            </ActionPanel>

            <ActionPanel
              title="Append dataset version"
              summary="Record an immutable provenance snapshot for the selected dataset above."
              statusMessage={verStatus}
              errorMessageText={verError}
              submitting={verBusy}
              submitLabel="Add version"
              onSubmit={handleAddVersion}
            >
              <div className="field">
                <label htmlFor="mon-ver-label">Version label</label>
                <input id="mon-ver-label" value={verLabel} onChange={(e) => setVerLabel(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ver-acquired">Source acquisition time</label>
                <input id="mon-ver-acquired" type="datetime-local" value={verAcquiredAt} onChange={(e) => setVerAcquiredAt(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ver-res">Resolution</label>
                <input id="mon-ver-res" value={verResolution} onChange={(e) => setVerResolution(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ver-method">Method</label>
                <input id="mon-ver-method" value={verMethod} onChange={(e) => setVerMethod(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="mon-ver-lim">Limitations (optional)</label>
                <input id="mon-ver-lim" value={verLimitations} onChange={(e) => setVerLimitations(e.target.value)} />
              </div>
            </ActionPanel>
          </>
        )}
      </div>

      <div className="card notice notice-info" role="note" style={{ marginTop: '1rem' }}>
        Geospatial and environmental analysis capabilities are developed in phases. Deterministic methods and validated datasets come before sophisticated models.
      </div>
    </WorkspacePage>
  );
}
