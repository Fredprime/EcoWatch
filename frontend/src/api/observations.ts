import { jsonBody, request } from './client';
import type { CreateObservationRequest, CursorPage, IntakeReceiptResponse, ObservationDetail, ObservationSummary } from './types';

const BASE = '/api/v1';

export function createObservation(payload: CreateObservationRequest): Promise<IntakeReceiptResponse> {
  return request<IntakeReceiptResponse>(`${BASE}/observations`, jsonBody(payload));
}

export function listObservations(cursor?: string | null): Promise<CursorPage<ObservationSummary>> {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}&limit=50` : '?limit=50';
  return request<CursorPage<ObservationSummary>>(`${BASE}/observations${query}`);
}

export function getObservation(observationId: string): Promise<ObservationDetail> {
  return request<ObservationDetail>(`${BASE}/observations/${encodeURIComponent(observationId)}`);
}
