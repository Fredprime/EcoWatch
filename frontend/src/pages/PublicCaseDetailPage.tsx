import { useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ResourceState } from '../components/ResourceState';
import { useApiResource } from '../hooks/useApiResource';
import { getPublicCase } from '../api/publicCases';

function formatTime(value: string | null | undefined): string {
  if (!value) return 'Not provided';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function PublicCaseDetailPage() {
  const { caseId } = useParams();
  const loadCase = useCallback(() => getPublicCase(caseId ?? ''), [caseId]);
  const record = useApiResource(loadCase, `public-case:${caseId ?? ''}`, Boolean(caseId));

  return (
    <div className="public-page public-narrow">
      <p><Link to="/updates">Back to public updates</Link></p>
      <ResourceState state={record.state}>
        {(item) => (
          <article className="card">
            <p className="public-eyebrow">Approved public summary</p>
            <h1>{item.title}</h1>
            <p>
              <strong>Case code:</strong> {item.caseCode} ·{' '}
              <strong>Recorded status:</strong> {item.status.replaceAll('_', ' ')}
            </p>
            <p>{item.publicSummary}</p>
            <dl className="public-details">
              {item.areaReference && (
                <>
                  <dt>Area reference</dt>
                  <dd>{item.areaReference}</dd>
                </>
              )}
              <dt>Last reviewed</dt>
              <dd>{formatTime(item.lastReviewedAt)}</dd>
              <dt>First recorded</dt>
              <dd>{formatTime(item.createdAt)}</dd>
            </dl>
            <p className="muted">
              This summary was reviewed and approved for publication. It is not an automated finding and
              makes no claim about a source, cause or harm.
            </p>
          </article>
        )}
      </ResourceState>
    </div>
  );
}
