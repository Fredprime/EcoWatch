import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import type { SubmissionState } from '../types';
import { WorkspacePage } from './WorkspacePage';

const stateMeta: Record<SubmissionState, { label: string; description: string; className: string }> = {
  draft: { label: 'Local draft', description: 'Saved on this device only. Not submitted to EcoWatch.', className: 'status-draft' },
  queued: { label: 'Queued locally', description: 'Stored on this device and waiting to sync. Not yet received by EcoWatch.', className: 'status-queued' },
  submitted: { label: 'Submitted', description: 'Sent to the server; awaiting durable receipt confirmation.', className: 'status-submitted' },
  received: { label: 'Received by server', description: 'Durable server receipt confirmed. A reference can be shown after this state.', className: 'status-received' },
};

export function ReportPage() {
  const [state, setState] = useState<SubmissionState>('draft');
  const [reference, setReference] = useState<string | null>(null);
  const meta = useMemo(() => stateMeta[state], [state]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setState('submitted');
    setReference(null);
    // Demo only: simulate durable receipt after submit. Real implementation must wait for server confirmation.
    window.setTimeout(() => {
      setState('received');
      setReference('ECO-DEMO-RECEIPT');
    }, 800);
  }

  function markQueued() {
    setState('queued');
    setReference(null);
  }

  return (
    <WorkspacePage
      title="Report / Collect"
      description="Mobile-first reporting for communities and field contributors. Do not require specialist knowledge to submit an observation. Support uncertain dates/locations and make states explicit."
    >
      <div className="card notice notice-warn" role="note">
        <strong>Privacy and safety:</strong> Share only what is safe to share. Avoid identifying people unnecessarily. Sensitive locations may be restricted or generalised in later views. This is a scaffold — no data is sent to a backend.
      </div>

      <div className="card">
        <h2>Submission state</h2>
        <p>
          <span className={`status-pill ${meta.className}`}>{meta.label}</span>
        </p>
        <p className="muted">{meta.description}</p>
        {state === 'received' && reference && <p><strong>Reference (after receipt):</strong> {reference}</p>}
        {state === 'queued' && <p className="muted">A queued item must not be described as received by EcoWatch.</p>}
      </div>

      <form className="card form-grid" onSubmit={onSubmit}>
        <h2>Observation details</h2>

        <div className="field">
          <label htmlFor="obs-type">Observation type</label>
          <select id="obs-type" name="obsType" defaultValue="">
            <option value="">Select an option (or “Not sure”)</option>
            <option value="land">Land or soil concern</option>
            <option value="water">Water concern</option>
            <option value="vegetation">Vegetation or habitat concern</option>
            <option value="pollution">Possible pollution or dumping</option>
            <option value="other">Other</option>
            <option value="unsure">Not sure</option>
          </select>
          <p className="field-hint">Broad categories help routing; contributors can be unsure.</p>
        </div>

        <div className="field">
          <label htmlFor="description">What did you observe?</label>
          <textarea id="description" name="description" placeholder="Describe what you saw, heard, smelled, or measured in plain language." />
        </div>

        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="location">Location (exact, approximate, or description)</label>
            <input id="location" name="location" type="text" placeholder="e.g. near bridge, community name, coordinates if known" />
            <p className="field-hint">Map-based location is optional where appropriate; provide non-map alternatives.</p>
          </div>
          <div className="field">
            <label htmlFor="location-precision">Location precision</label>
            <select id="location-precision" name="locationPrecision" defaultValue="approximate">
              <option value="exact">Exact</option>
              <option value="approximate">Approximate</option>
              <option value="unknown">Unknown / not provided</option>
            </select>
          </div>
        </div>

        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="observed-date">When was it observed?</label>
            <input id="observed-date" name="observedDate" type="text" placeholder="Exact date/time, approximate period, or unknown" />
            <p className="field-hint">Event/observed/submitted/received times are recorded separately in the full system.</p>
          </div>
          <div className="field">
            <label htmlFor="firsthand">Was this firsthand?</label>
            <select id="firsthand" name="firsthand" defaultValue="unsure">
              <option value="yes">Yes</option>
              <option value="no">No</option>
              <option value="unsure">Not sure / prefer not to say</option>
            </select>
          </div>
        </div>

        <div className="field">
          <label htmlFor="media">Supporting media (optional)</label>
          <input id="media" name="media" type="file" multiple aria-describedby="media-hint" />
          <p id="media-hint" className="field-hint">Original files must be preserved with provenance in the full implementation. Upload handling is not wired in this scaffold.</p>
        </div>

        <div className="notice notice-info" role="note">
          <strong>Why we ask:</strong> source, time, place, and method details help reviewers understand evidence without treating all observations as equivalent.
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-secondary" onClick={markQueued}>Save as queued locally (demo)</button>
          <button type="submit" className="btn">Submit observation (demo)</button>
        </div>
      </form>
    </WorkspacePage>
  );
}
