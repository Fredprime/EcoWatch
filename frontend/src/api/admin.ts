import { jsonBody, request } from './client';
import type {
  AssignMembershipRequest,
  AuditEventSummary,
  CreateOrganisationRequest,
  CreateUserRequest,
  CursorPage,
  JobSummaryResponse,
  MembershipResponse,
  OrganisationSummary,
  UpdateOrganisationRequest,
  UpdateUserRequest,
  UserResponse,
} from './types';

const BASE = '/api/v1';

/** Admin reads and writes. Permissions and scoping are enforced by the server. */
export function listOrganisations(): Promise<CursorPage<OrganisationSummary>> {
  return request<CursorPage<OrganisationSummary>>(`${BASE}/organisations?limit=50`);
}

export function createOrganisation(
  payload: CreateOrganisationRequest,
): Promise<OrganisationSummary> {
  return request<OrganisationSummary>(`${BASE}/organisations`, jsonBody(payload));
}

export function updateOrganisation(
  organisationId: string,
  payload: UpdateOrganisationRequest,
): Promise<OrganisationSummary> {
  return request<OrganisationSummary>(
    `${BASE}/organisations/${encodeURIComponent(organisationId)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
}

export function listUsers(): Promise<CursorPage<UserResponse>> {
  return request<CursorPage<UserResponse>>(`${BASE}/users?limit=50`);
}

export function createUser(payload: CreateUserRequest): Promise<UserResponse> {
  return request<UserResponse>(`${BASE}/users`, jsonBody(payload));
}

export function updateUser(
  userId: string,
  payload: UpdateUserRequest,
): Promise<UserResponse> {
  return request<UserResponse>(`${BASE}/users/${encodeURIComponent(userId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export function assignMembership(
  organisationId: string,
  payload: AssignMembershipRequest,
): Promise<MembershipResponse> {
  return request<MembershipResponse>(
    `${BASE}/organisations/${encodeURIComponent(organisationId)}/memberships`,
    jsonBody(payload),
  );
}

export function listAuditEvents(): Promise<CursorPage<AuditEventSummary>> {
  return request<CursorPage<AuditEventSummary>>(`${BASE}/audit/events?limit=50`);
}

export function getJobsSummary(): Promise<JobSummaryResponse> {
  return request<JobSummaryResponse>(`${BASE}/jobs/summary`);
}
