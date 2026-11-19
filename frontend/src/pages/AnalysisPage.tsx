import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';

export function AnalysisPage() {
  return (
    <WorkspacePage
      title="Analysis"
      description="Datasets, methods, outputs and interpretation. Derived artefacts are linked to source data and versions; interpretations are separate reviewed records."
    >
      <Notice variant="info" role="note" title="Endpoint-independent shell:">
        Analysis runs, datasets, and outputs will be loaded from backend services. This UI preserves separation between source data, methods, outputs, and interpretation.
      </Notice>
      <div className="grid grid-2" style={{ marginTop: '1rem' }}>
        <div className="card">
          <h2>Datasets & methods</h2>
          <EmptyState title="No datasets or analysis runs loaded." detail="When available, select area/period/indicator, view source dataset versions, and review documented methods and parameters." />
        </div>
        <div className="card">
          <h2>Outputs & interpretation</h2>
          <EmptyState title="No outputs available." detail="Derived outputs must show quality/coverage/seasonality limits and be traceable to inputs. Interpretations remain separate, reviewed records." />
        </div>
      </div>
      <div className="card">
        <h2>Actions (pending backend)</h2>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-secondary" disabled>Define analysis scope</button>
          <button type="button" className="btn btn-secondary" disabled>Run documented analysis</button>
          <button type="button" className="btn btn-secondary" disabled>Add reviewed interpretation</button>
        </div>
      </div>
    </WorkspacePage>
  );
}
