import { useCallback, useEffect, useState } from 'react';
import { ApiError, errorMessage } from '../api/client';

export type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: ApiError };

export interface Resource<T> {
  state: AsyncState<T>;
  reload: () => void;
}

interface Stored<T> {
  key: string;
  nonce: number;
  value: AsyncState<T>;
}

export function useApiResource<T>(load: () => Promise<T>, key: string, enabled = true): Resource<T> {
  const [stored, setStored] = useState<Stored<T>>(() => ({
    key,
    nonce: 0,
    value: enabled ? { status: 'loading' } : { status: 'idle' },
  }));
  const [nonce, setNonce] = useState(0);

  // A changed key or an explicit reload is loading until its own result arrives,
  // so no synchronous setState is needed inside the effect.
  const state: AsyncState<T> =
    stored.key === key && stored.nonce === nonce
      ? stored.value
      : enabled
        ? { status: 'loading' }
        : { status: 'idle' };

  useEffect(() => {
    if (!enabled) return;
    let active = true;
    load().then(
      (data) => {
        if (active) setStored({ key, nonce, value: { status: 'success', data } });
      },
      (cause: unknown) => {
        if (!active) return;
        const error = cause instanceof ApiError ? cause : new ApiError(0, {}, errorMessage(cause));
        setStored({ key, nonce, value: { status: 'error', error } });
      },
    );
    return () => {
      active = false;
    };
  }, [load, key, enabled, nonce]);

  return { state, reload: useCallback(() => setNonce((value) => value + 1), []) };
}
