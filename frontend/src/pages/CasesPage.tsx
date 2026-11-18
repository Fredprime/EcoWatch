import { WorkspacePage } from './WorkspacePage';

const timeline = [
  { label: 'Event start (reported)', date: 'Approx. 2026-03 — dry season', detail: 'Reporter indicates conditions may have begun earlier; date is uncertain.' },
  { label: 'Observed', date: '2026-04-12 09:30 local (reported)', detail: 'Community observation recorded with approximate location.' },
  { label: 'Submitted', date: '2026-04-12 09:42 device time', detail: 'Client submission initiated; device time is not authoritative.' },
  { label: 'Received', date: '2026-04-12 09:43:10Z server', detail: 'Durable server receipt recorded (authoritative receipt time).' },
  { label: 'Sampling / acquisition', date: '2026-04-15', detail: 'Field sample collected by authorised contributor (example).' },
  { label: 'Processing / analysis', date: '2026-04-18', detail: 'Derived analytical artefact linked to source inputs and method version.' },
  { label: 'Intervention milestone', date: 'Pending', detail: 'Approved actions recorded separately from environmental outcome.' },
];

export function CasesPage() {
  return (
    <WorkspacePage
      title="Cases / Investigations"
      description="Case workspace with evidence-grounded summary, map/geographic context, linked observations, relationships, timeline, hypotheses, gaps, and review history. Shown to authorised roles."
    >
      <div className="grid grid-2">
        <div className="card">
          <h2>Case summary (example)</h2>
          <p><strong>Status:</strong> Under review</p>
          <p><strong>Owner:</strong> Assigned investigator (role-scoped)</p>
          <p className="muted">Summaries must be grounded in linked evidence and distinguish claims, measurements, interpretations, and model outputs. Machine-generated content must be labelled.</p>
          <h3>Evidence gaps / next actions</h3>
          <ul>
            <li>Confirm location precision and permissions for sensitive coordinates.</li>
            <li>Request additional field verification or sampling where appropriate.</li>
            <li>Review candidate relationships and alternative explanations.</li>
          </ul>
        </div>

        <div className="card">
          <h2>Map and geographic context</h2>
          <div className="placeholder-map" aria-label="Map placeholder">
            <div>
              <p><strong>Map placeholder (MapLibre proposed)</strong></p>
              <p>Display data quality/uncertainty where relevant. Exact sensitive locations may be restricted or generalised.</p>
            </div>
          </div>
          <p className="muted" style={{ marginTop: '0.75rem' }}>A map is not the only way to understand a record. Provide list and detail views as alternatives.</p>
        </div>
      </div>

      <div className="card">
        <h2>Timeline</h2>
        <p className="muted">Timelines distinguish event-start, observation, submission, receipt, acquisition, sampling, processing and intervention dates.</p>
        <ol className="timeline">
          {timeline.map((item) => (
            <li key={item.label}>
              <time>{item.date}</time>
              <strong>{item.label}</strong>
              <div className="muted">{item.detail}</div>
            </li>
          ))}
        </ol>
      </div>

      <div className="card">
        <h2>Linked observations & evidence (placeholder)</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Source</th><th>Type</th><th>Time precision</th><th>Location precision</th><th>Relationship</th></tr>
            </thead>
            <tbody>
              <tr><td>Community report</td><td>Observation</td><td>Approximate</td><td>Approximate</td><td>Candidate (explainable) — pending review</td></tr>
              <tr><td>Field record</td><td>Measurement</td><td>Exact</td><td>Exact (restricted)</td><td>Linked to case by reviewer</td></tr>
            </tbody>
          </table>
        </div>
        <p className="muted">Original observations/evidence are preserved; links do not overwrite records. Reviewer decisions are audited and reversible through new actions.</p>
      </div>
    </WorkspacePage>
  );
}
