import { jsonBody, request } from './client';
import type { ReceiptLookupRequest, ReceiptLookupResponse } from './types';

const BASE = '/api/v1';

/** Anonymous, throttled lookup by tracking code. Never sends or stores contributor identity. */
export function lookupReceipt(payload: ReceiptLookupRequest): Promise<ReceiptLookupResponse> {
  return request<ReceiptLookupResponse>(`${BASE}/observations/receipt-lookup`, jsonBody(payload));
}
