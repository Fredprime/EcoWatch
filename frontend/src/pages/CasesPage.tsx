import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
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

const exampleCases = [
  { id: 'CASE-EX-01', title: 'Water discolouration reports (cluster preview)', status: 'Under review', owner: 'Investigator (example)', area: 'Approximate sub-area', updated: '2026-04-18' },
  { id: 'CASE-EX-02', title: 'Vegetation cover concern (follow-up preview)', status: 'Awaiting field verification', owner: 'Reviewer (example)', area: 'Restricted/generalised', updated: '2026-04-16' },
];

export function CasesPage() {
  const [showExamples, setShowExamples] = useState(false);
  const cases = useMemo(() => (showExamples ? exampleCases : []), [showExamples]);

  return (
    <WorkspacePage
      title="Cases / Investigations"
      description="Case workspace with evidence-grounded summary, map/geographic context, linked observations, relationships, timeline, hypotheses, gaps, and review history. Shown to authorised roles."
    >
      <div className="card">
        <h2>Cases (list view)</h2>
        <p className="muted">Non-map alternative to case discovery. In production, cases and records appear only within permitted scope.</p>
        <div className="notice notice-warn" role="note" style={{ marginBottom: '1rem' }}>
          <strong>Scaffold example rows only:</strong> example cases are UI preview content, not real cases or product records.
          <div style={{ marginTop: '0.5rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setShowExamples((v) => !v)}>
              {showExamples ? 'Hide example rows' : 'Show example rows (UI preview)'}
            </button>
          </div>
        </div>

        {!showExamples ? (
          <div className="empty-state" role="status">
            <p><strong>No cases to display.</strong></p>
            <p className="muted">Assigned or permitted cases will appear here when backend integration is available. Use example rows only to preview layout.</p>
          </div>
        ) : (
          <div className="table-wrap" role="region" aria-label="Cases table" tabIndex={0}>
            <table>
              <thead>
                <tr>
                  <th scope="col">Case ID</th>
                  <th scope="col">Title</th>
                  <th scope="col">Status</th>
                  <th scope="col">Owner</th>
                  <th scope="col">Area</th>
                  <th scope="col">Last updated</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => (
                  <tr key={c.id}>
                    <th scope="row"><Link to={`/cases/${c.id}`}>{c.id}</Link></th>
                    <td>{c.title} <em className="muted">(example row)</em></td>
                    <td>{c.status}</td>
                    <td>{c.owner}</td>
                    <td>{c.area}</td>
                    <td>{c.updated}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showExamples && (
        <>
          <div className="grid grid-2">
            <div className="card">
              <h2>Case detail (UI preview)</h2>
              <p><strong>Status:</strong> Under review</p>
              <p><strong>Owner:</strong> Assigned investigator (role-scoped)</p>
              <p className="muted">Summaries must be grounded in linked evidence and distinguish claims, measurements, interpretations, and model outputs. Machine-generated content must be labelled. This is example preview content.</p>
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
            <h2>Timeline (UI preview)</h2>
            <p className="muted">Timelines distinguish event-start, observation, submission, receipt, acquisition, sampling, processing and intervention dates. Example entries below illustrate structure only.</p>
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
            <h2>Linked observations & evidence (UI preview)</h2>
            <div className="table-wrap" role="region" aria-label="Linked observations table" tabIndex={0}>
              <table>
                <thead>
                  <tr><th scope="col">Source</th><th scope="col">Type</th><th scope="col">Time precision</th><th scope="col">Location precision</th><th scope="col">Relationship</th></tr>
                </thead>
                <tbody>
                  <tr><td>Community report (example)</td><td>Observation</td><td>Approximate</td><td>Approximate</td><td>Candidate (explainable) — pending review</td></tr>
                  <tr><td>Field record (example)</td><td>Measurement</td><td>Exact</td><td>Exact (restricted)</td><td>Linked to case by reviewer</td></tr>
                </tbody>
              </table>
            </div>
            <p className="muted">Original observations/evidence are preserved; links do not overwrite records. Reviewer decisions are audited and reversible through new actions.</p>
          </div>
        </>
      )}
    </WorkspacePage>
  );
}