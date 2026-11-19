import type { ErrorResponse } from './types';

type UnauthorizedHandler = () => void;

let authToken: string | null = null;
let onUnauthorized: UnauthorizedHandler | null = null;

/** The token is held in memory only; a page reload requires signing in again. */
export function setAuthToken(token: string | null): void {
  authToken = token;
}

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  onUnauthorized = handler;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly field?: string | null;
  readonly details: ErrorResponse['details'];
  readonly requestId?: string;
  readonly category: 'permanent' | 'transient';
  readonly retryAfterSeconds: number | null;

  constructor(status: number, body: Partial<ErrorResponse>, fallback: string) {
    super(body.message ?? fallback);
    this.name = 'ApiError';
    this.status = status;
    this.code = body.code ?? 'REQUEST_FAILED';
    this.field = body.field;
    this.details = body.details ?? [];
    this.requestId = body.requestId;
    this.category = body.category ?? 'permanent';
    this.retryAfterSeconds = body.retryAfterSeconds ?? null;
  }
}

async function parseBody(response: Response): Promise<Partial<ErrorResponse> | null> {
  if (response.status === 204 || response.headers.get('content-length') === '0') return null;
  try {
    const value: unknown = await response.json();
    return value && typeof value === 'object' ? (value as Partial<ErrorResponse>) : {};
  } catch {
    return null;
  }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  // JSON bodies are strings; FormData must keep its own multipart boundary.
  if (typeof init.body === 'string') headers.set('Content-Type', 'application/json');
  if (authToken) headers.set('Authorization', `Bearer ${authToken}`);

  const response = await fetch(path, { ...init, headers });
  const body = await parseBody(response);

  if (response.status === 401) onUnauthorized?.();
  if (!response.ok) {
    throw new ApiError(response.status, body ?? {}, `Request failed (${response.status})`);
  }
  return body as T;
}

export function jsonBody(payload: unknown): RequestInit {
  return { method: 'POST', body: JSON.stringify(payload) };
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'The request could not be completed.';
}
