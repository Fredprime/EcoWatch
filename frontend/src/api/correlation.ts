import { jsonBody, request } from './client';
import type { CorrelationDecision, CorrelationSuggestion } from './types';

const BASE = '/api/v1/correlation';

/** Backend returns a bare array here, not a CursorPage. */
export function listSuggestions(): Promise<CorrelationSuggestion[]> {
  return request<CorrelationSuggestion[]>(`${BASE}/suggestions?limit=50`);
}

export function decideSuggestion(
  relationshipId: string,
  decision: CorrelationDecision,
  reason?: string,
): Promise<CorrelationSuggestion> {
  return request<CorrelationSuggestion>(
    `${BASE}/suggestions/${encodeURIComponent(relationshipId)}/decision`,
    jsonBody({ decision, ...(reason ? { reason } : {}) }),
  );
}
