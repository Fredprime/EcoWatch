import { useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import { WorkspacePage } from './WorkspacePage';
import { EmptyState } from '../components/EmptyState';
import { ResourceState } from '../components/ResourceState';
import { SignInPrompt } from '../components/SignInPrompt';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import { listCases } from '../api/cases';

function formatTime(value: string | null | undefined): string {
  if (!value) return 'Not provided';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function CasesPage() {
  const { status } = useAuth();
  const [query, setQuery] = useState('');
  const loadCases = useCallback(() => listCases(), []);
  const cases = useApiResource(loadCases, 'cases', status === 'authenticated');

  return (
    <WorkspacePage
      title="Cases / Investigations"
      description="Case summaries within your permitted scope. Records are grounded in linked evidence and show status with its rationale."
    >
      <div className="card">
        <h2>Cases (list view)</h2>
        <p className="muted">Server status is displayed as recorded; it is not an automated determination. Exact locations are not shown in this list.</p>

        {status !== 'authenticated' ? (
          <SignInPrompt what="Case records require an authenticated account." />
        ) : (
          <>
            <div className="toolbar">
              <div className="field">
                <label htmlFor="case-filter">Filter this page</label>
                <input
                  id="case-filter"
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search the current page by code, title or status"
                  aria-describedby="case-filter-hint"
                />
                <p id="case-filter-hint" className="field-hint">Filters only the records already returned by the server.</p>
              </div>
            </div>

            <ResourceState state={cases.state}>
              {(page) => {
                const q = query.trim().toLowerCase();
                const rows = q
                  ? page.items.filter((item) =>
                      [item.caseCode, item.title, item.status].some((value) => value.toLowerCase().includes(q)),
                    )
                  : page.items;

                if (rows.length === 0) {
                  return (
                    <EmptyState
                      title="No cases in your permitted scope yet."
                      detail="Cases appear here after an authorised reviewer creates them and links observations."
                    />
                  );
                }

                return (
                  <>
                    <div className="table-wrap" role="region" aria-label="Cases table" tabIndex={0}>
                      <table>
                        <thead>
                          <tr>
                            <th scope="col">Case code</th>
                            <th scope="col">Title</th>
                            <th scope="col">Server status</th>
                            <th scope="col">Last reviewed</th>
                            <th scope="col">Updated</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map((item) => (
                            <tr key={item.id}>
                              <th scope="row"><Link to={`/cases/${item.id}`}>{item.caseCode}</Link></th>
                              <td>{item.title}</td>
                              <td>{item.status.replaceAll('_', ' ')}</td>
                              <td>{formatTime(item.lastReviewedAt)}</td>
                              <td>{formatTime(item.updatedAt)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {page.hasMore && (
                      <p className="muted">More cases exist. This view shows the first page only.</p>
                    )}
                  </>
                );
              }}
            </ResourceState>
          </>
        )}
      </div>
    </WorkspacePage>
  );
}
