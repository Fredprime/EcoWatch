import { WorkspacePage } from './WorkspacePage';

export function MonitoringPage() {
  return (
    <WorkspacePage
      title="Environmental Monitoring"
      description="Maps, monitored areas, indicators and historical layers. Outputs must show data quality, uncertainty and method limitations where relevant."
    >
      <div className="grid grid-2">
        <div className="card">
          <h2>Map view (placeholder)</h2>
          <div className="placeholder-map" role="note" aria-label="Monitoring map placeholder">
            <div>
              <p><strong>Spatial layers placeholder</strong></p>
              <p>Monitored areas, observations, and selected indicators rendered with uncertainty/quality cues.</p>
            </div>
          </div>
        </div>
        <div className="card">
          <h2>List and detail alternative</h2>
          <p className="muted">Map is not the only way to understand records. Provide accessible list, filter, and detail views.</p>
          <p className="muted">
            No monitored areas or indicators are available in your permitted scope. Method, period, baseline, coverage and seasonality are shown with each record when present.
          </p>
        </div>
      </div>
      <div className="card notice notice-info" role="note">
        Geospatial and environmental analysis capabilities are developed in phases. Deterministic methods and validated datasets come before sophisticated models.
      </div>
    </WorkspacePage>
  );
}
