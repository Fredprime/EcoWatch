import { request } from './client';
import type { CaseDetail, CaseSummary, CursorPage, TimelineItem } from './types';

const BASE = '/api/v1';

export function listCases(cursor?: string | null): Promise<CursorPage<CaseSummary>> {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}&limit=50` : '?limit=50';
  return request<CursorPage<CaseSummary>>(`${BASE}/cases${query}`);
}

export function getCase(caseId: string): Promise<CaseDetail> {
  return request<CaseDetail>(`${BASE}/cases/${encodeURIComponent(caseId)}`);
}

export function getCaseTimeline(caseId: string): Promise<CursorPage<TimelineItem>> {
  return request<CursorPage<TimelineItem>>(`${BASE}/cases/${encodeURIComponent(caseId)}/timeline?limit=100`);
}
