import { useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError, errorMessage } from '../api/client';
import { lookupReceipt } from '../api/collection';
import type { ReceiptLookupResponse } from '../api/types';

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function TrackPage() {
  const [trackingCode, setTrackingCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<ReceiptLookupResponse | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setReceipt(null);
    try {
      setReceipt(await lookupReceipt({ trackingCode: trackingCode.trim() }));
    } catch (cause) {
      setError(
        cause instanceof ApiError && cause.status === 429
          ? 'Too many attempts. Please wait a little before trying again.'
          : errorMessage(cause),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="public-page public-narrow">
      <header className="public-page-header">
        <h1>Track a report</h1>
        <p>Enter the code from your receipt. You’ll see receipt details only — no identity or exact location.</p>
      </header>

      <form className="card form-grid" onSubmit={(event) => void submit(event)}>
        <div className="field">
          <label htmlFor="tracking-code">Tracking code</label>
          <input
            id="tracking-code"
            name="trackingCode"
            type="text"
            value={trackingCode}
            onChange={(event) => setTrackingCode(event.target.value)}
            autoComplete="off"
            maxLength={256}
            required
            aria-describedby="tracking-hint"
          />
          <p id="tracking-hint" className="field-hint">
            The code is shown on the receipt after a successful submission. Keep it private.
          </p>
        </div>
        <div>
          <button type="submit" className="btn" disabled={busy || !trackingCode.trim()} aria-busy={busy}>
            {busy ? 'Looking up…' : 'Look up receipt'}
          </button>
        </div>
      </form>

      {error && <p className="notice notice-danger" role="alert">{error}</p>}

      {receipt && (
        <section className="card" aria-labelledby="receipt-title">
          <h2 id="receipt-title">Server receipt</h2>
          <p role="status">A durable receipt is confirmed for observation {receipt.observationId}.</p>
          <dl className="public-details">
            <dt>Observation type</dt>
            <dd>{receipt.observationType}</dd>
            <dt>Received at</dt>
            <dd>{formatTime(receipt.receivedAt)}</dd>
            <dt>Time precision</dt>
            <dd>{receipt.timePrecision}</dd>
            <dt>Location precision</dt>
            <dd>{receipt.locationPrecision}</dd>
            <dt>Evidence items</dt>
            <dd>{receipt.evidenceCount}</dd>
          </dl>
          <p className="muted">
            This confirms receipt only. It is not an assessment of the report and makes no finding about it.
          </p>
        </section>
      )}
    </div>
  );
}
