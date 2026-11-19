import type { ReactNode } from 'react';
import type { CursorPage } from '../api/types';
import type { AsyncState } from '../hooks/useApiResource';
import { ResourceState } from './ResourceState';
import { EmptyState } from './EmptyState';

export interface ListColumn<T> {
  header: string;
  cell: (row: T) => ReactNode;
}

/**
 * A read-only, bounded table of server records. Loading, error and empty states
 * are handled by the shared components; no row is invented when the page is empty.
 */
export function ReadOnlyListCard<T extends { id: string }>({
  title,
  note,
  state,
  emptyTitle,
  emptyDetail,
  columns,
  ariaLabel,
  idleNote = 'Select a parent record above to load this list.',
}: {
  title: string;
  note?: ReactNode;
  state: AsyncState<CursorPage<T>>;
  emptyTitle: string;
  emptyDetail?: string;
  columns: ListColumn<T>[];
  ariaLabel: string;
  idleNote?: string;
}) {
  return (
    <div className="card">
      <h2>{title}</h2>
      {note && <p className="muted">{note}</p>}
      {state.status === 'idle' ? (
        <p className="muted">{idleNote}</p>
      ) : (
        <ResourceState state={state}>
          {(page) =>
            page.items.length === 0 ? (
              <EmptyState title={emptyTitle} detail={emptyDetail} />
            ) : (
              <>
                <div className="table-wrap" role="region" aria-label={ariaLabel} tabIndex={0}>
                  <table>
                    <thead>
                      <tr>
                        {columns.map((column) => (
                          <th scope="col" key={column.header}>
                            {column.header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {page.items.map((row) => (
                        <tr key={row.id}>
                          {columns.map((column) => (
                            <td key={column.header}>{column.cell(row)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {page.hasMore && (
                  <p className="muted">More records exist. This view shows the first page only.</p>
                )}
              </>
            )
          }
        </ResourceState>
      )}
    </div>
  );
}

/** Parent selector for a child list that carries no own organisation scope. */
export function RecordPicker({
  id,
  label,
  value,
  onChange,
  options,
  hint,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  hint?: string;
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Select a record…</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {hint && <p className="field-hint">{hint}</p>}
    </div>
  );
}
