import { useMemo, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import type { SubmissionState } from '../types';
import { WorkspacePage } from './WorkspacePage';

type FieldName = 'obsType' | 'description';

type FormValues = {
  obsType: string;
  description: string;
  location: string;
  locationPrecision: string;
  observedDate: string;
  firsthand: string;
};

const initialValues: FormValues = {
  obsType: '',
  description: '',
  location: '',
  locationPrecision: 'approximate',
  observedDate: '',
  firsthand: 'unsure',
};

const stateMeta: Record<SubmissionState, { label: string; description: string; className: string }> = {
  draft: { label: 'Local draft', description: 'Saved on this device only. Not submitted to EcoWatch.', className: 'status-draft' },
  queued: { label: 'Queued locally', description: 'Stored on this device and waiting to sync. Not yet received by EcoWatch.', className: 'status-queued' },
  submitted: { label: 'Submitting…', description: 'Sending to the server and awaiting durable receipt confirmation.', className: 'status-submitted' },
  received: { label: 'Received by server', description: 'Durable server receipt confirmed. A reference can be shown after this state.', className: 'status-received' },
};

function validate(values: FormValues): Partial<Record<FieldName, string>> {
  const errors: Partial<Record<FieldName, string>> = {};
  if (!values.obsType) errors.obsType = 'Select an observation type, or choose “Not sure”.';
  if (!values.description.trim()) errors.description = 'Describe what you observed in plain language.';
  return errors;
}

export function ReportPage() {
  const [values, setValues] = useState<FormValues>(initialValues);
  const [state, setState] = useState<SubmissionState>('draft');
  const [reference, setReference] = useState<string | null>(null);
  const [errors, setErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const summaryRef = useRef<HTMLDivElement | null>(null);
  const meta = useMemo(() => stateMeta[state], [state]);

  function update<K extends keyof FormValues>(key: K, value: FormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
    if (submitAttempted && (key === 'obsType' || key === 'description')) {
      const next = { ...values, [key]: value } as FormValues;
      const nextErrors = validate(next);
      setErrors((prevErrors) => ({ ...prevErrors, [key]: nextErrors[key as FieldName] }));
    }
  }

  function onBlurField(field: FieldName) {
    const nextErrors = validate(values);
    setErrors((prev) => ({ ...prev, [field]: nextErrors[field] }));
  }

  function markQueued() {
    setState('queued');
    setReference(null);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitAttempted(true);
    const nextErrors = validate(values);
    setErrors(nextErrors);
    const keys = Object.keys(nextErrors) as FieldName[];
    if (keys.length > 0) {
      setState('draft');
      setReference(null);
      window.setTimeout(() => summaryRef.current?.focus(), 0);
      return;
    }

    setIsSubmitting(true);
    setState('submitted');
    setReference(null);
    // Demo only: simulate durable receipt after submit. Real implementation must wait for server confirmation.
    window.setTimeout(() => {
      setIsSubmitting(false);
      setState('received');
      setReference('ECO-DEMO-RECEIPT');
    }, 900);
  }

  const errorEntries = Object.entries(errors).filter(([, msg]) => Boolean(msg)) as [FieldName, string][];

  return (
    <WorkspacePage
      title="Report / Collect"
      description="Mobile-first reporting for communities and field contributors. Do not require specialist knowledge to submit an observation. Support uncertain dates/locations and make states explicit."
    >
      <div className="card notice notice-warn" role="note">
        <strong>Privacy and safety:</strong> Share only what is safe to share. Avoid identifying people unnecessarily. Sensitive locations may be restricted or generalised in later views. This is a scaffold — no data is sent to a backend.
      </div>

      <div className="card" aria-live="polite">
        <h2>Submission state</h2>
        <p>
          <span className={`status-pill ${meta.className}`}>{meta.label}</span>
        </p>
        <p className="muted">{meta.description}</p>
        {state === 'received' && reference && <p><strong>Reference (after receipt):</strong> {reference}</p>}
        {state === 'queued' && <p className="muted">A queued item must not be described as received by EcoWatch.</p>}
      </div>

      <form className="card form-grid" onSubmit={onSubmit} noValidate>
        <h2>Observation details</h2>

        {errorEntries.length > 0 && (
          <div
            ref={summaryRef}
            className="notice notice-danger error-summary"
            role="alert"
            aria-labelledby="error-summary-title"
            tabIndex={-1}
          >
            <h3 id="error-summary-title">There is a problem</h3>
            <p>Please fix the following before submitting:</p>
            <ul>
              {errorEntries.map(([field, message]) => (
                <li key={field}>
                  <a href={`#${field === 'obsType' ? 'obs-type' : 'description'}`}>{message}</a>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="field">
          <label htmlFor="obs-type">Observation type <span aria-hidden="true">*</span></label>
          <select
            id="obs-type"
            name="obsType"
            value={values.obsType}
            onChange={(e) => update('obsType', e.target.value)}
            onBlur={() => onBlurField('obsType')}
            aria-invalid={Boolean(errors.obsType)}
            aria-describedby={errors.obsType ? 'obs-type-error obs-type-hint' : 'obs-type-hint'}
          >
            <option value="">Select an option</option>
            <option value="land">Land or soil concern</option>
            <option value="water">Water concern</option>
            <option value="vegetation">Vegetation or habitat concern</option>
            <option value="pollution">Possible pollution or dumping</option>
            <option value="other">Other</option>
            <option value="unsure">Not sure</option>
          </select>
          {errors.obsType && <p id="obs-type-error" className="field-error">{errors.obsType}</p>}
          <p id="obs-type-hint" className="field-hint">Broad categories help routing; contributors can be unsure.</p>
        </div>

        <div className="field">
          <label htmlFor="description">What did you observe? <span aria-hidden="true">*</span></label>
          <textarea
            id="description"
            name="description"
            value={values.description}
            onChange={(e) => update('description', e.target.value)}
            onBlur={() => onBlurField('description')}
            placeholder="Describe what you saw, heard, smelled, or measured in plain language."
            aria-invalid={Boolean(errors.description)}
            aria-describedby={errors.description ? 'description-error description-hint' : 'description-hint'}
          />
          {errors.description && <p id="description-error" className="field-error">{errors.description}</p>}
          <p id="description-hint" className="field-hint">Provide as much detail as is safe and known. Uncertainty is acceptable.</p>
        </div>

        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="location">Location (exact, approximate, or description)</label>
            <input
              id="location"
              name="location"
              type="text"
              value={values.location}
              onChange={(e) => update('location', e.target.value)}
              placeholder="e.g. near bridge, community name, coordinates if known"
              aria-describedby="location-hint"
            />
            <p id="location-hint" className="field-hint">Map-based location is optional where appropriate; provide non-map alternatives. Unknown/approximate is allowed.</p>
          </div>
          <div className="field">
            <label htmlFor="location-precision">Location precision</label>
            <select
              id="location-precision"
              name="locationPrecision"
              value={values.locationPrecision}
              onChange={(e) => update('locationPrecision', e.target.value)}
            >
              <option value="exact">Exact</option>
              <option value="approximate">Approximate</option>
              <option value="unknown">Unknown / not provided</option>
            </select>
          </div>
        </div>

        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="observed-date">When was it observed?</label>
            <input
              id="observed-date"
              name="observedDate"
              type="text"
              value={values.observedDate}
              onChange={(e) => update('observedDate', e.target.value)}
              placeholder="Exact date/time, approximate period, or unknown"
              aria-describedby="observed-date-hint"
            />
            <p id="observed-date-hint" className="field-hint">Event/observed/submitted/received times are recorded separately in the full system. Unknown is allowed.</p>
          </div>
          <div className="field">
            <label htmlFor="firsthand">Was this firsthand?</label>
            <select id="firsthand" name="firsthand" value={values.firsthand} onChange={(e) => update('firsthand', e.target.value)}>
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
          <button type="button" className="btn btn-secondary" onClick={markQueued} disabled={isSubmitting}>
            Save as queued locally (demo)
          </button>
          <button type="submit" className="btn" disabled={isSubmitting} aria-busy={isSubmitting}>
            {isSubmitting ? 'Submitting…' : 'Submit observation (demo)'}
          </button>
        </div>
      </form>
    </WorkspacePage>
  );
}
