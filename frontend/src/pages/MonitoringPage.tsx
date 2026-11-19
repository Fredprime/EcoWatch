import { useCallback, useMemo, useState } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { SignInPrompt } from '../components/SignInPrompt';
import { LazyWktMap } from '../components/LazyWktMap';
import { featuresFromWkt } from '../components/wkt';
import {
  ReadOnlyListCard,
  RecordPicker,
  type ListColumn,
} from '../components/Phase3Views';
import { formatTime } from '../components/phase3Format';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import { listDatasetVersions, listDatasets } from '../api/phase3';
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

  const loadDatasets = useCallback(() => listDatasets(), []);
  const datasets = useApiResource(loadDatasets, 'catalogue-datasets', authenticated);

  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const loadVersions = useCallback(() => listDatasetVersions(selectedDatasetId), [selectedDatasetId]);
  const versions = useApiResource(
    loadVersions,
    `dataset-versions:${selectedDatasetId}`,
    authenticated && Boolean(selectedDatasetId),
  );

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
          </>
        )}
      </div>

      <div className="card notice notice-info" role="note" style={{ marginTop: '1rem' }}>
        Geospatial and environmental analysis capabilities are developed in phases. Deterministic methods and validated datasets come before sophisticated models.
      </div>
    </WorkspacePage>
  );
}
