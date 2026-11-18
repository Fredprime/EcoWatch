import { useState } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';
import { StatusPill } from '../components/StatusPill';

const exampleSuggestions = [
  {
    id: 'REL-EX-01',
    left: 'OBS-1042 (Community report)',
    right: 'OBS-1041 (Field contributor)',
    signal: 'Spatial + temporal proximity (explainable)',
    confidence: 'Ranking signal — not truth/severity',
    state: 'Pending review',
  },
  {
    id: 'REL-EX-02',
    left: 'OBS-1038 (Registered contributor)',
    right: 'OBS-1042 (Community report)',
    signal: 'Semantic similarity (candidate)',
    confidence: 'Ambiguous — possible shared context',
    state: 'Pending review',
  },
];

export function EvidencePage() {
  const [showExamples, setShowExamples] = useState(false);

  return (
    <WorkspacePage
      title="Evidence Intelligence"
      description="Candidate relationships, duplicate review and evidence context. Suggestions must be explainable, reversible, and reviewed by authorised humans. Correlation is a ranking signal, not proof."
    >
      <Notice variant="info" role="note" title="Review principle:">
        Machine suggestions support review; they do not declare sources, causation, illegality, or harm. Similar reports are not independent corroboration without source checks.
      </Notice>

      <div className="grid grid-3" style={{ marginTop: '1rem' }}>
        <div className="card"><h3>Candidate relationships</h3><p className="muted">Explainable suggestions awaiting human review (accept / reject / ambiguous).</p></div>
        <div className="card"><h3>Duplicate review</h3><p className="muted">Identify repeats and dependent sources without deleting original observations.</p></div>
        <div className="card"><h3>Evidence context</h3><p className="muted">Preserve provenance, time/location precision, and source relationships.</p></div>
      </div>

      <div className="card">
        <h2>Relationship review queue</h2>
        <p className="muted">No live suggestions loaded. In production this queue is populated by asynchronous, explainable correlation jobs and scoped by permissions.</p>
        <div style={{ marginBottom: '1rem' }}>
          <Notice variant="warn" role="note" title="Scaffold example rows only:">
            Example suggestions are UI preview content, not real correlation outputs or product records.
            <div style={{ marginTop: '0.5rem' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowExamples((v) => !v)}>
                {showExamples ? 'Hide example rows' : 'Show example rows (UI preview)'}
              </button>
            </div>
          </Notice>
        </div>

        {!showExamples ? (
          <EmptyState title="No candidate relationships to review." detail="When correlation results are available, explainable suggestions will appear here for authorised review." />
        ) : (
          <div className="table-wrap" role="region" aria-label="Candidate relationships table" tabIndex={0}>
            <table>
              <thead>
                <tr>
                  <th scope="col">Suggestion</th>
                  <th scope="col">Evidence pair</th>
                  <th scope="col">Why suggested (explanation)</th>
                  <th scope="col">Interpretation note</th>
                  <th scope="col">State</th>
                </tr>
              </thead>
              <tbody>
                {exampleSuggestions.map((s) => (
                  <tr key={s.id}>
                    <th scope="row">{s.id}</th>
                    <td>
                      <div>{s.left}</div>
                      <div className="muted">↔ {s.right} <em>(example)</em></div>
                    </td>
                    <td>{s.signal}</td>
                    <td className="muted">{s.confidence}</td>
                    <td><StatusPill label={s.state} tone="review" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Reviewer actions (placeholder)</h2>
        <p className="muted">Accept, reject, or mark ambiguous with a reason. Decisions are audited and reversible through new actions; original records remain unchanged. UI actions will be wired to backend endpoints when available.</p>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-secondary" disabled>Accept (requires backend)</button>
          <button type="button" className="btn btn-secondary" disabled>Reject (requires backend)</button>
          <button type="button" className="btn btn-secondary" disabled>Mark ambiguous (requires backend)</button>
        </div>
      </div>
    </WorkspacePage>
  );
}
