import { request } from './client';
import type { AuditEventSummary, CursorPage, JobSummaryResponse, OrganisationSummary } from './types';

const BASE = '/api/v1';

/** Read-only admin reads. Permissions and scoping are enforced by the server. */
export function listOrganisations(): Promise<CursorPage<OrganisationSummary>> {
  return request<CursorPage<OrganisationSummary>>(`${BASE}/organisations?limit=50`);
}

export function listAuditEvents(): Promise<CursorPage<AuditEventSummary>> {
  return request<CursorPage<AuditEventSummary>>(`${BASE}/audit/events?limit=50`);
}

export function getJobsSummary(): Promise<JobSummaryResponse> {
  return request<JobSummaryResponse>(`${BASE}/jobs/summary`);
}
