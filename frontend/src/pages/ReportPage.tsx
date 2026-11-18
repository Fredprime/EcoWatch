import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { ApiError, errorMessage } from '../api/client';
import { createObservation } from '../api/observations';
import type { IntakeReceiptResponse, LocationPrecision, TimePrecision } from '../api/types';

type FieldName = 'obsType' | 'description';
type SubmitState = 'draft' | 'submitting' | 'received' | 'error';

type FormValues = {
  obsType: string;
  description: string;
  locationWording: string;
  locationPrecision: LocationPrecision;
  timeWording: string;
  timePrecision: TimePrecision;
  firsthand: string;
};

const initialValues: FormValues = {
  obsType: '',
  description: '',
  locationWording: '',
  locationPrecision: 'approximate',
  timeWording: '',
  timePrecision: 'unknown',
  firsthand: 'unsure',
};

function validate(values: FormValues): Partial<Record<FieldName, string>> {
  const errors: Partial<Record<FieldName, string>> = {};
  if (!values.obsType) errors.obsType = 'Select an observation type, or choose "Not sure".';
  if (!values.description.trim()) errors.description = 'Describe what you observed in plain language.';
  return errors;
}

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function ReportPage() {
  const [values, setValues] = useState<FormValues>(initialValues);
  const [submitState, setSubmitState] = useState<SubmitState>('draft');
  const [receipt, setReceipt] = useState<IntakeReceiptResponse | null>(null);
  const [errors, setErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const summaryRef = useRef<HTMLDivElement | null>(null);
  const idempotencyRef = useRef<string | null>(null);

  function update<K extends keyof FormValues>(key: K, value: FormValues[K]) {
    setValues((previous) => ({ ...previous, [key]: value }));
    if (submitAttempted && (key === 'obsType' || key === 'description')) {
      const nextErrors = validate({ ...values, [key]: value } as FormValues);
      setErrors((previous) => ({ ...previous, [key]: nextErrors[key as FieldName] }));
    }
  }

  function onBlurField(field: FieldName) {
    const nextErrors = validate(values);
    setErrors((previous) => ({ ...previous, [field]: nextErrors[field] }));
  }

  async function submitForm() {
    const nextErrors = validate(values);
    setErrors(nextErrors);
    const keys = Object.keys(nextErrors) as FieldName[];
    if (keys.length > 0) {
      setSubmitState('draft');
      setSubmitError(null);
      window.setTimeout(() => summaryRef.current?.focus(), 0);
      return;
    }

    if (!idempotencyRef.current) idempotencyRef.current = crypto.randomUUID();
    setSubmitState('submitting');
    setSubmitError(null);
    setReceipt(null);

    try {
      const result = await createObservation({
        idempotencyKey: idempotencyRef.current,
        observationType: values.obsType,
        description: values.description.trim(),
        timePrecision: values.timePrecision,
        ...(values.timeWording.trim() ? { originalTimeWording: values.timeWording.trim() } : {}),
        locationPrecision: values.locationPrecision,
        ...(values.locationWording.trim() ? { originalLocationWording: values.locationWording.trim() } : {}),
        accessClass: 'restricted',
        ...(values.firsthand === 'yes' ? { isFirsthand: true } : values.firsthand === 'no' ? { isFirsthand: false } : {}),
      });
      setReceipt(result);
      setSubmitState('received');
      setValues(initialValues);
      setSubmitAttempted(false);
      idempotencyRef.current = null;
    } catch (cause) {
      setSubmitState('error');
      setSubmitError(errorMessage(cause));
      if (cause instanceof ApiError) {
        const fieldErrors: Partial<Record<FieldName, string>> = {};
        for (const detail of cause.details) {
          if (detail.field === 'observationType') fieldErrors.obsType = detail.message;
          if (detail.field === 'description') fieldErrors.description = detail.message;
        }
        if (Object.keys(fieldErrors).length > 0) setErrors(fieldErrors);
      }
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitAttempted(true);
    void submitForm();
  }

  const errorEntries = Object.entries(errors).filter(([, message]) => Boolean(message)) as [FieldName, string][];

  return (
    <WorkspacePage
      title="Report / Collect"
      description="Mobile-first reporting for communities and field contributors. Uncertainty about time and location is explicit."
    >
      <div className="card notice notice-warn" role="note">
        <strong>Privacy and safety:</strong> Share only what is safe to share. Avoid identifying people unnecessarily. Sensitive locations may be restricted or generalised in later views. Submission goes directly to the server; there is no local queue.
      </div>

      <div className="card">
        <h2>Submission state</h2>
        <p role="status">
          <strong>
            {submitState === 'draft' && 'Draft — not submitted.'}
            {submitState === 'submitting' && 'Submitting…'}
            {submitState === 'received' && 'Received by server.'}
            {submitState === 'error' && 'Submission failed.'}
          </strong>
        </p>
        {submitState === 'submitting' && <p className="muted">Waiting for a durable server receipt.</p>}
        {submitState === 'error' && submitError && <p className="notice notice-danger" role="alert">{submitError}</p>}
        {submitState === 'error' && (
          <button type="button" className="btn btn-secondary" onClick={() => void submitForm()}>
            Retry with the same idempotency key
          </button>
        )}
        {receipt && (
          <div>
            <p>
              <strong>Tracking reference:</strong>{' '}
              {receipt.trackingCode ?? 'No reference was returned for this replay.'}
            </p>
            <p className="muted">
              Observation {receipt.observationId} · server receipt {formatTime(receipt.receivedAt)} ·
              version {receipt.currentVersion} · time precision {receipt.timePrecision} ·
              location precision {receipt.locationPrecision}
              {receipt.idempotentReplay ? ' · server receipt already recorded' : ''}
            </p>
          </div>
        )}
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
            onChange={(event) => update('obsType', event.target.value)}
            onBlur={() => onBlurField('obsType')}
            aria-required="true"
            aria-invalid={Boolean(errors.obsType)}
            aria-describedby={errors.obsType ? 'obs-type-error obs-type-hint' : 'obs-type-hint'}
          >
            <option value="">Select an option</option>
            <option value="land_or_soil">Land or soil concern</option>
            <option value="water">Water concern</option>
            <option value="vegetation_or_habitat">Vegetation or habitat concern</option>
            <option value="possible_pollution">Possible pollution or dumping</option>
            <option value="other">Other</option>
            <option value="not_sure">Not sure</option>
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
            onChange={(event) => update('description', event.target.value)}
            onBlur={() => onBlurField('description')}
            placeholder="Describe what you saw, heard, smelled, or measured in plain language."
            aria-required="true"
            aria-invalid={Boolean(errors.description)}
            aria-describedby={errors.description ? 'description-error description-hint' : 'description-hint'}
          />
          {errors.description && <p id="description-error" className="field-error">{errors.description}</p>}
          <p id="description-hint" className="field-hint">Provide as much detail as is safe and known. Uncertainty is acceptable.</p>
        </div>

        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="location-wording">Location description</label>
            <input
              id="location-wording"
              name="locationWording"
              type="text"
              value={values.locationWording}
              onChange={(event) => update('locationWording', event.target.value)}
              placeholder="e.g. near bridge, community name, or an approximate area"
              aria-describedby="location-hint"
            />
            <p id="location-hint" className="field-hint">Use a non-map description if coordinates are unavailable or unsafe to share.</p>
          </div>
          <div className="field">
            <label htmlFor="location-precision">Location precision</label>
            <select
              id="location-precision"
              name="locationPrecision"
              value={values.locationPrecision}
              onChange={(event) => update('locationPrecision', event.target.value as LocationPrecision)}
            >
              <option value="exact">Exact</option>
              <option value="approximate">Approximate</option>
              <option value="area">Area only</option>
              <option value="unknown">Not provided</option>
            </select>
          </div>
        </div>

        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="time-wording">When was it observed?</label>
            <input
              id="time-wording"
              name="timeWording"
              type="text"
              value={values.timeWording}
              onChange={(event) => update('timeWording', event.target.value)}
              placeholder="Exact date/time, approximate period, or unknown"
              aria-describedby="time-hint"
            />
            <p id="time-hint" className="field-hint">Recorded as reported wording. Event, observed, submitted and server receipt times stay separate.</p>
          </div>
          <div className="field">
            <label htmlFor="time-precision">Time precision</label>
            <select
              id="time-precision"
              name="timePrecision"
              value={values.timePrecision}
              onChange={(event) => update('timePrecision', event.target.value as TimePrecision)}
            >
              <option value="exact">Exact</option>
              <option value="approximate">Approximate</option>
              <option value="range">Range</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>
        </div>

        <div className="field">
          <label htmlFor="firsthand">Was this firsthand?</label>
          <select id="firsthand" name="firsthand" value={values.firsthand} onChange={(event) => update('firsthand', event.target.value)}>
            <option value="yes">Yes</option>
            <option value="no">No</option>
            <option value="unsure">Not sure / prefer not to say</option>
          </select>
        </div>

        <p className="muted">
          Supporting media upload is not available here. Original files must be preserved with provenance before upload is offered.
        </p>

        <div>
          <button type="submit" className="btn" disabled={submitState === 'submitting'} aria-busy={submitState === 'submitting'}>
            {submitState === 'submitting' ? 'Submitting…' : 'Submit observation'}
          </button>
        </div>
      </form>
    </WorkspacePage>
  );
}
