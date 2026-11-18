import { useCallback } from 'react';
import { Link } from 'react-router-dom';
import { EmptyState } from '../components/EmptyState';
import { ResourceState } from '../components/ResourceState';
import { useApiResource } from '../hooks/useApiResource';
import { listPublicCases } from '../api/publicCases';

function formatTime(value: string | null | undefined): string {
  if (!value) return 'Not provided';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function PublicUpdatesPage() {
  const loadCases = useCallback(() => listPublicCases(), []);
  const cases = useApiResource(loadCases, 'public-cases');

  return (
    <div className="public-page">
      <header className="public-page-header">
        <h1>Public updates</h1>
        <p>
          Approved public case summaries. Internal notes, contributor identities and exact locations are
          not included. A recorded status is a human-reviewed record, not an automated finding.
        </p>
      </header>

      <ResourceState state={cases.state}>
        {(page) =>
          page.items.length === 0 ? (
            <EmptyState
              title="No public updates have been published yet."
              detail="A summary appears here only after an authorised reviewer approves it for publication."
            />
          ) : (
            <>
              <ul className="public-case-list">
                {page.items.map((item) => (
                  <li key={item.id} className="card">
                    <h2><Link to={`/updates/${item.id}`}>{item.title}</Link></h2>
                    <p>
                      <strong>Case code:</strong> {item.caseCode} ·{' '}
                      <strong>Recorded status:</strong> {item.status.replaceAll('_', ' ')}
                    </p>
                    <p>{item.publicSummary}</p>
                    {item.areaReference && <p className="muted">Area reference: {item.areaReference}</p>}
                    <p className="muted">Last reviewed: {formatTime(item.lastReviewedAt)}</p>
                  </li>
                ))}
              </ul>
              {page.hasMore && (
                <p className="muted">More published summaries exist. This view shows the first page only.</p>
              )}
            </>
          )
        }
      </ResourceState>
    </div>
  );
}
