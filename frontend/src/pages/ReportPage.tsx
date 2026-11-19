import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { ApiError, errorMessage } from '../api/client';
import { uploadEvidence } from '../api/evidence';
import { createObservation } from '../api/observations';
import type { IntakeReceiptResponse, LocationPrecision, TimePrecision } from '../api/types';

type FieldName = 'obsType' | 'description';
type SubmitState = 'draft' | 'submitting' | 'received' | 'error';
type PhotoState = 'pending' | 'uploading' | 'uploaded' | 'failed';

type FormValues = {
  obsType: string;
  description: string;
  locationWording: string;
  locationPrecision: LocationPrecision;
  timeWording: string;
  timePrecision: TimePrecision;
  firsthand: string;
};

type Photo = {
  id: string;
  file: File;
  previewUrl: string;
  state: PhotoState;
  error?: string;
  assetId?: string;
};

const ALLOWED_PHOTO_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
const MAX_PHOTO_BYTES = 15 * 1024 * 1024;
const MAX_PHOTO_MB = MAX_PHOTO_BYTES / (1024 * 1024);

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
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [photosBusy, setPhotosBusy] = useState(false);
  const summaryRef = useRef<HTMLDivElement | null>(null);
  const idempotencyRef = useRef<string | null>(null);
  const previewUrlsRef = useRef<Set<string>>(new Set());

  // Local previews are never sent to the server; release them when the page unmounts.
  useEffect(() => {
    const urls = previewUrlsRef.current;
    return () => {
      for (const url of urls) URL.revokeObjectURL(url);
    };
  }, []);

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

  function clearPhotos() {
    for (const url of previewUrlsRef.current) URL.revokeObjectURL(url);
    previewUrlsRef.current.clear();
    setPhotos([]);
    setPhotoError(null);
  }

  function onPickPhotos(event: ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(event.target.files ?? []);
    event.target.value = ''; // allow selecting the same file again after removal
    if (picked.length === 0) return;

    const accepted: Photo[] = [];
    const rejected: string[] = [];
    for (const file of picked) {
      if (!ALLOWED_PHOTO_TYPES.has(file.type)) {
        rejected.push(`${file.name}: unsupported format`);
        continue;
      }
      if (file.size > MAX_PHOTO_BYTES) {
        rejected.push(`${file.name}: larger than ${MAX_PHOTO_MB} MB`);
        continue;
      }
      const previewUrl = URL.createObjectURL(file);
      previewUrlsRef.current.add(previewUrl);
      accepted.push({ id: crypto.randomUUID(), file, previewUrl, state: 'pending' });
    }

    setPhotoError(rejected.length > 0 ? rejected.join(' · ') : null);
    if (accepted.length > 0) setPhotos((previous) => [...previous, ...accepted]);
  }

  function removePhoto(id: string) {
    const photo = photos.find((item) => item.id === id);
    if (photo) {
      URL.revokeObjectURL(photo.previewUrl);
      previewUrlsRef.current.delete(photo.previewUrl);
    }
    setPhotos((previous) => previous.filter((item) => item.id !== id));
  }

  /** Send one photo and reflect only what the server actually acknowledges. */
  async function sendPhoto(photo: Photo, observationId: string, trackingCode: string) {
    setPhotos((previous) => previous.map((item) =>
      item.id === photo.id ? { ...item, state: 'uploading', error: undefined } : item,
    ));
    try {
      const asset = await uploadEvidence(observationId, photo.file, trackingCode);
      setPhotos((previous) => previous.map((item) =>
        item.id === photo.id
          ? { ...item, state: 'uploaded', error: undefined, assetId: asset.id }
          : item,
      ));
    } catch (cause) {
      setPhotos((previous) => previous.map((item) =>
        item.id === photo.id ? { ...item, state: 'failed', error: errorMessage(cause) } : item,
      ));
    }
  }

  async function uploadPhotos(list: Photo[], observationId: string, trackingCode: string) {
    setPhotosBusy(true);
    try {
      // Sequential: one request at a time keeps anonymous uploads predictable.
      for (const photo of list) await sendPhoto(photo, observationId, trackingCode);
    } finally {
      setPhotosBusy(false);
    }
  }

  async function retryPhoto(photo: Photo) {
    if (!receipt?.trackingCode || photosBusy) return;
    await sendPhoto(photo, receipt.observationId, receipt.trackingCode);
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

    const pendingPhotos = receipt ? [] : photos; // an existing receipt means this is a new report
    if (receipt) clearPhotos();

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

      if (pendingPhotos.length > 0) {
        if (result.trackingCode) {
          await uploadPhotos(pendingPhotos, result.observationId, result.trackingCode);
        } else {
          // No code on an idempotent replay: the server cannot authorise an anonymous upload.
          setPhotos((previous) => previous.map((item) => ({
            ...item,
            state: 'failed',
            error: 'No tracking code was returned for this submission, so photos could not be uploaded.',
          })));
        }
      }
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
  const uploadedCount = photos.filter((photo) => photo.state === 'uploaded').length;
  const failedCount = photos.filter((photo) => photo.state === 'failed').length;
  const uploadingCount = photos.filter((photo) => photo.state === 'uploading').length;

  return (
    <div className="public-page">
      <header className="public-page-header">
        <h1>Report an observation</h1>
        <p>No account is needed. Tell us what you saw and how certain you are about when and where.</p>
      </header>

      <div className="notice notice-warn" role="note">
        <strong>Before you submit:</strong> Share only what is safe to share. Sensitive locations may be
        generalised in later views. Nothing is stored on this device — submission goes straight to the server.
      </div>

      {submitState !== 'draft' && (
        <div className="card">
          <h2>Submission state</h2>
          <p role="status">
            <strong>
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
              {photos.length > 0 && (
                <p className="muted">
                  Photos: {uploadedCount} uploaded to server
                  {uploadingCount > 0 && ` · ${uploadingCount} uploading`}
                  {failedCount > 0 && ` · ${failedCount} failed`}.
                </p>
              )}
            </div>
          )}
        </div>
      )}

      <form className="card form-grid public-report-form" onSubmit={onSubmit} noValidate>
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

        <div className="public-report-main">
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
            <p id="obs-type-hint" className="field-hint">Choose the closest category. “Not sure” is fine.</p>
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
            <p id="description-hint" className="field-hint">Plain language is fine. Include only what is safe and known.</p>
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
              <p id="location-hint" className="field-hint">An area description is enough; exact coordinates are not needed.</p>
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
              <p id="time-hint" className="field-hint">Approximate or unknown is fine. Your wording is kept as given.</p>
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

          <div>
            <button
              type="submit"
              className="btn"
              disabled={submitState === 'submitting' || photosBusy}
              aria-busy={submitState === 'submitting' || photosBusy}
            >
              {submitState === 'submitting' ? 'Submitting…' : photosBusy ? 'Uploading photos…' : 'Submit observation'}
            </button>
          </div>
        </div>

        <aside className="public-report-aside" aria-labelledby="photos-heading">
          <h3 id="photos-heading">Photos <span className="muted">(optional)</span></h3>
          <label className="photo-drop" htmlFor="photo-input">
            <input
              id="photo-input"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              onChange={onPickPhotos}
              disabled={photosBusy}
              aria-describedby="photos-hint"
            />
            <span className="photo-drop-zone">
              <span className="photo-drop-title">Take or choose a photo</span>
              <span>On a phone this opens your camera or photo library.</span>
              <span className="muted">JPG, PNG or WebP · up to {MAX_PHOTO_MB} MB each</span>
            </span>
          </label>
          <p id="photos-hint" className="field-hint">
            Photos stay on this device until you submit. They upload only after the server issues your
            tracking code, and a failed upload can be retried.
          </p>
          {photoError && <p className="notice notice-danger" role="alert">{photoError}</p>}
          {photos.length > 0 && (
            <ul className="photo-list">
              {photos.map((photo) => (
                <li className="photo-item" key={photo.id}>
                  <img className="photo-thumb" src={photo.previewUrl} alt="" />
                  <div className="photo-meta">
                    <div className="photo-name" title={photo.file.name}>{photo.file.name}</div>
                    <div className={`photo-status${photo.state === 'failed' ? ' error' : ''}`}>
                      {photo.state === 'pending' && 'Ready — uploads after submission'}
                      {photo.state === 'uploading' && 'Uploading…'}
                      {photo.state === 'uploaded' && 'Uploaded to server'}
                      {photo.state === 'failed' && `Upload failed — ${photo.error ?? 'unknown error'}`}
                    </div>
                  </div>
                  {photo.state === 'failed' && receipt?.trackingCode && (
                    <button type="button" className="btn btn-secondary" onClick={() => void retryPhoto(photo)}>
                      Retry
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => removePhoto(photo.id)}
                    disabled={photo.state === 'uploading'}
                    aria-label={`Remove ${photo.file.name}`}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </form>

      <p className="muted public-after-form">
        After submitting, keep the tracking reference private — you’ll use it to look up the server receipt.
      </p>
    </div>
  );
}
