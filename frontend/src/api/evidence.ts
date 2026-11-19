import { request } from './client';
import type { EvidenceAssetResponse } from './types';

const BASE = '/api/v1';

/**
 * Upload an optional photo to an observation using the tracking code issued at intake.
 * No account is needed; the server authorises by matching the high-entropy code.
 * FormData carries its own multipart boundary, so client.ts must not set JSON headers.
 *
 * The idempotency key must stay the same across retries of one photo, so the
 * server can return the original asset if a response was lost in transit.
 */
/** List stored assets and their scan/derivative state for one observation. */
export function listObservationEvidence(
  observationId: string,
): Promise<EvidenceAssetResponse[]> {
  return request<EvidenceAssetResponse[]>(
    `${BASE}/observations/${encodeURIComponent(observationId)}/evidence`,
  );
}

export function uploadEvidence(
  observationId: string,
  file: File,
  trackingCode: string,
  idempotencyKey: string,
): Promise<EvidenceAssetResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('accessClass', 'restricted');

  return request<EvidenceAssetResponse>(
    `${BASE}/observations/${encodeURIComponent(observationId)}/evidence`,
    {
      method: 'POST',
      body: form,
      headers: {
        'X-Tracking-Code': trackingCode,
        'Idempotency-Key': idempotencyKey,
      },
    },
  );
}
