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
          <div className="placeholder-map" aria-label="Monitoring map placeholder">
            <div>
              <p><strong>Spatial layers placeholder</strong></p>
              <p>Monitored areas, observations, and selected indicators rendered with uncertainty/quality cues.</p>
            </div>
          </div>
        </div>
        <div className="card">
          <h2>List and detail alternative</h2>
          <p className="muted">Map is not the only way to understand records. Provide accessible list, filter, and detail views.</p>
          <ul>
            <li><strong>Area:</strong> Pilot area (to be selected) — boundary and source version recorded.</li>
            <li><strong>Indicator:</strong> Example indicator — method, period, and baseline defined before interpretation.</li>
            <li><strong>Quality:</strong> Coverage/seasonality/method limitations must be visible.</li>
          </ul>
        </div>
      </div>
      <div className="card notice notice-info" role="note">
        Geospatial/environmental analysis capabilities are developed in phases. Deterministic methods and validated datasets come before sophisticated models (per docs).
      </div>
    </WorkspacePage>
  );
}
