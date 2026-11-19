import { jsonBody, request } from './client';
import type { AuthMeResponse, LoginRequest, LoginResponse } from './types';

const BASE = '/api/v1';

export function login(payload: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>(`${BASE}/auth/login`, jsonBody(payload));
}

export function logout(): Promise<{ revoked: boolean }> {
  return request<{ revoked: boolean }>(`${BASE}/auth/logout`, { method: 'POST' });
}

export function getMe(): Promise<AuthMeResponse> {
  return request<AuthMeResponse>(`${BASE}/auth/me`);
}
