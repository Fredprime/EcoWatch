import { request } from './client';
import type { CursorPage, PublicCaseSummary } from './types';

const BASE = '/api/v1/public';

/** Approved, redacted case summaries. No authentication is required or sent. */
export function listPublicCases(cursor?: string | null): Promise<CursorPage<PublicCaseSummary>> {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}&limit=20` : '?limit=20';
  return request<CursorPage<PublicCaseSummary>>(`${BASE}/cases${query}`);
}

export function getPublicCase(caseId: string): Promise<PublicCaseSummary> {
  return request<PublicCaseSummary>(`${BASE}/cases/${encodeURIComponent(caseId)}`);
}
