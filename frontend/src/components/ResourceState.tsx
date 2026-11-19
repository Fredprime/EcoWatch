import type { ReactNode } from 'react';
import type { AsyncState } from '../hooks/useApiResource';
import { Notice } from './Notice';

export function ResourceState<T>({
  state,
  children,
}: {
  state: AsyncState<T>;
  children: (data: T) => ReactNode;
}) {
  if (state.status === 'idle') return null;
  if (state.status === 'loading') {
    return <p className="muted" role="status">Loading…</p>;
  }
  if (state.status === 'error') {
    const { error } = state;
    return (
      <Notice variant="danger" role="alert" title="Could not load records.">
        {error.message}
        {error.code !== 'REQUEST_FAILED' && <span className="muted"> ({error.code})</span>}
        {error.requestId && <span className="muted"> Request ID: {error.requestId}</span>}
      </Notice>
    );
  }
  return <>{children(state.data)}</>;
}
