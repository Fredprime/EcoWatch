/**
 * Offline-first report queue (ADR-018, ADR-036; FR-050/051/052).
 *
 * Native IndexedDB, no PWA dependency. Reports are stored with one stable client
 * UUID used as the intake idempotency key, sent as text before photos, and stay
 * on the device until the server has accepted every phase. Only transient
 * failures retry (bounded exponential backoff with jitter and Retry-After).
 */
import { ApiError, errorMessage } from './client';
import { uploadEvidence } from './evidence';
import { createObservation } from './observations';
import type { CreateObservationRequest, IntakeReceiptResponse } from './types';

const DB_NAME = 'ecowatch-offline';
const STORE = 'reports';
const DB_VERSION = 1;
const MAX_BACKOFF_MS = 60_000;

export const QUEUE_CHANGE_EVENT = 'ecowatch:queue-change';
export const QUEUE_ENQUEUED_EVENT = 'ecowatch:queue-enqueued';
export const QUEUE_SUBMITTED_EVENT = 'ecowatch:queue-submitted';

export type QueueStatus = 'queued' | 'syncing' | 'failed';

export interface QueuedPhoto {
  id: string;
  file: File;
}

export interface QueuedReport {
  id: string;
  payload: CreateObservationRequest;
  photos: QueuedPhoto[];
  status: QueueStatus;
  attempts: number;
  nextAttemptAt: number;
  createdAt: string;
  lastError?: string;
  receipt?: IntakeReceiptResponse;
}

let dbPromise: Promise<IDBDatabase> | null = null;

function openDb(): Promise<IDBDatabase> {
  if (!dbPromise) {
    dbPromise = new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains(STORE)) {
          request.result.createObjectStore(STORE, { keyPath: 'id' });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
  return dbPromise;
}

export async function listQueued(): Promise<QueuedReport[]> {
  const db = await openDb();
  return new Promise<QueuedReport[]>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readonly');
    const request = tx.objectStore(STORE).getAll();
    request.onsuccess = () => resolve(request.result as QueuedReport[]);
    request.onerror = () => reject(request.error);
  });
}

function changed(): void {
  window.dispatchEvent(new Event(QUEUE_CHANGE_EVENT));
}

export async function enqueueReport(report: QueuedReport): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(report);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
  changed();
  window.dispatchEvent(new Event(QUEUE_ENQUEUED_EVENT));
}

export async function patchQueued(id: string, patch: Partial<QueuedReport>): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    const store = tx.objectStore(STORE);
    const get = store.get(id);
    get.onsuccess = () => {
      const current = get.result as QueuedReport | undefined;
      if (current) store.put({ ...current, ...patch });
    };
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
  changed();
}

export async function removeQueued(id: string): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
  changed();
}

export function isTransient(error: unknown): boolean {
  // A fetch that never got a response is safe to retry with the same key.
  if (error instanceof ApiError) return error.category === 'transient';
  return true;
}

/** Back to the queue after a permanent failure, or discard it entirely. */
export async function retryQueued(id: string): Promise<void> {
  await patchQueued(id, {
    status: 'queued',
    attempts: 0,
    nextAttemptAt: Date.now(),
    lastError: undefined,
  });
  window.dispatchEvent(new Event(QUEUE_ENQUEUED_EVENT));
}

export async function discardQueued(id: string): Promise<void> {
  await removeQueued(id);
}

async function processRecord(stored: QueuedReport): Promise<void> {
  const record = stored.status === 'syncing' ? { ...stored, status: 'queued' as const } : stored;
  await patchQueued(record.id, { status: 'syncing', lastError: undefined });
  try {
    // Phase 1: text. The stored receipt means a later media failure never
    // re-creates the observation; the idempotency key covers a lost response.
    let receipt = record.receipt;
    if (!receipt) {
      receipt = await createObservation(record.payload);
      await patchQueued(record.id, { receipt });
    }
    const trackingCode = receipt.trackingCode;
    if (!trackingCode) {
      throw new ApiError(
        0,
        {
          code: 'NO_TRACKING_CODE',
          category: 'permanent',
          message: 'No tracking code was returned, so photos cannot be uploaded.',
        },
        'No tracking code was returned.',
      );
    }

    // Phase 2: media. Every photo reuses its original key, so a retry after a
    // lost response returns the stored asset instead of storing it twice.
    for (const photo of record.photos) {
      await uploadEvidence(receipt.observationId, photo.file, trackingCode, photo.id);
    }

    await removeQueued(record.id);
    window.dispatchEvent(new CustomEvent<IntakeReceiptResponse>(QUEUE_SUBMITTED_EVENT, { detail: receipt }));
  } catch (cause) {
    if (!isTransient(cause)) {
      await patchQueued(record.id, { status: 'failed', lastError: errorMessage(cause) });
      return;
    }
    const attempts = record.attempts + 1;
    const apiError = cause instanceof ApiError ? cause : null;
    const backoff = Math.min(MAX_BACKOFF_MS, 1_000 * 2 ** Math.min(attempts, 6));
    const jitter = Math.floor(Math.random() * 1_000);
    const delay = Math.max(backoff + jitter, (apiError?.retryAfterSeconds ?? 0) * 1_000);
    await patchQueued(record.id, {
      status: 'queued',
      attempts,
      nextAttemptAt: Date.now() + delay,
      lastError: errorMessage(cause),
    });
  }
}

let draining = false;

export async function drainQueue(): Promise<void> {
  if (draining) return;
  let records: QueuedReport[];
  try {
    records = await listQueued();
  } catch {
    return; // IndexedDB unavailable — the driver will try again on the next event.
  }
  if (records.length === 0) return;
  draining = true;
  try {
    for (const record of records) {
      if (record.nextAttemptAt > Date.now()) continue;
      await processRecord(record);
    }
  } finally {
    draining = false;
  }
}

/** Mount once. Drains on startup, on reconnect and after an enqueue. */
export function startQueueDriver(): () => void {
  const run = () => { void drainQueue(); };
  let timer: number | undefined;

  const schedule = () => {
    if (timer !== undefined) return;
    void listQueued().then((items) => {
      const due = items
        .filter((item) => item.status !== 'failed' && item.nextAttemptAt > Date.now())
        .map((item) => item.nextAttemptAt);
      if (due.length === 0) return;
      const delay = Math.min(Math.min(...due) - Date.now(), MAX_BACKOFF_MS);
      timer = window.setTimeout(() => {
        timer = undefined;
        run();
      }, Math.max(delay, 0) + 1);
    }).catch(() => {});
  };

  const onEnqueued = () => { run(); schedule(); };
  window.addEventListener('online', run);
  window.addEventListener(QUEUE_ENQUEUED_EVENT, onEnqueued);
  window.addEventListener(QUEUE_CHANGE_EVENT, schedule);
  run();
  schedule();

  return () => {
    window.removeEventListener('online', run);
    window.removeEventListener(QUEUE_ENQUEUED_EVENT, onEnqueued);
    window.removeEventListener(QUEUE_CHANGE_EVENT, schedule);
    if (timer !== undefined) window.clearTimeout(timer);
  };
}
