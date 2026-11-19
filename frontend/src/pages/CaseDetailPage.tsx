import { useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import { WorkspacePage } from './WorkspacePage';
import { ResourceState } from '../components/ResourceState';
import { SignInPrompt } from '../components/SignInPrompt';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import { getCase, getCaseTimeline } from '../api/cases';

function formatTime(value: string | null | undefined): string {
  if (!value) return 'Not provided';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function CaseDetailPage() {
  const { caseId } = useParams();
  const { status } = useAuth();
  const enabled = status === 'authenticated' && Boolean(caseId);
  const loadDetail = useCallback(() => getCase(caseId ?? ''), [caseId]);
  const loadTimeline = useCallback(() => getCaseTimeline(caseId ?? ''), [caseId]);
  const detail = useApiResource(loadDetail, caseId ?? '', enabled);
  const timeline = useApiResource(loadTimeline, `timeline:${caseId ?? ''}`, enabled);

  return (
    <WorkspacePage
      title={`Case detail${caseId ? `: ${caseId}` : ''}`}
      description="Case record within your permitted scope, with linked observations and a timeline that keeps date types separate."
    >
      <div className="card">
        <Link className="btn btn-secondary" to="/cases">Back to cases</Link>
      </div>

      {status !== 'authenticated' ? (
        <SignInPrompt what="Case records require an authenticated account." />
      ) : (
        <>
          <ResourceState state={detail.state}>
            {(record) => (
              <>
                <div className="card">
                  <h2>{record.title}</h2>
                  <p><strong>Case code:</strong> {record.caseCode} · <strong>Server status:</strong> {record.status.replaceAll('_', ' ')}</p>
                  <p className="muted">{record.summary || 'No summary recorded.'}</p>
                  {record.statusRationale && <p><strong>Status rationale:</strong> {record.statusRationale}</p>}
                </div>

                <div className="grid grid-2">
                  <div className="card">
                    <h3>Investigation questions</h3>
                    {record.investigationQuestions.length > 0 ? (
                      <ul>{record.investigationQuestions.map((item) => <li key={item}>{item}</li>)}</ul>
                    ) : <p className="muted">None recorded.</p>}
                    <h3>Competing hypotheses</h3>
                    {record.competingHypotheses.length > 0 ? (
                      <ul>{record.competingHypotheses.map((item) => <li key={item}>{item}</li>)}</ul>
                    ) : <p className="muted">None recorded.</p>}
                  </div>
                  <div className="card">
                    <h3>Evidence gaps / next actions</h3>
                    {record.evidenceGaps.length > 0 ? (
                      <ul>{record.evidenceGaps.map((item) => <li key={item}>{item}</li>)}</ul>
                    ) : <p className="muted">None recorded.</p>}
                    <h3>Geographic context</h3>
                    <div className="placeholder-map" role="note" aria-label="Map not available in this integration">
                      <div>
                        <p><strong>Map view unavailable.</strong></p>
                        <p>Use the case summary and linked records; exact sensitive locations are restricted by the server.</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h2>Linked observations</h2>
                  {record.observations.length === 0 ? (
                    <p className="muted">No observations are linked to this case.</p>
                  ) : (
                    <div className="table-wrap" role="region" aria-label="Linked observations table" tabIndex={0}>
                      <table>
                        <thead>
                          <tr>
                            <th scope="col">Observation</th>
                            <th scope="col">Link rationale</th>
                            <th scope="col">Review status</th>
                            <th scope="col">Contested</th>
                            <th scope="col">Linked at</th>
                          </tr>
                        </thead>
                        <tbody>
                          {record.observations.map((item) => (
                            <tr key={item.id}>
                              <th scope="row">{item.observationId}</th>
                              <td>{item.linkRationale}</td>
                              <td>{item.reviewStatus.replaceAll('_', ' ')}</td>
                              <td>{item.isContested ? 'Yes' : 'No'}</td>
                              <td>{formatTime(item.createdAt)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </>
            )}
          </ResourceState>

          <div className="card">
            <h2>Timeline</h2>
            <p className="muted">Date type, precision and source are shown separately. Device and reported times are not treated as server receipt times.</p>
            <ResourceState state={timeline.state}>
              {(page) =>
                page.items.length === 0 ? (
                  <p className="muted">No timeline entries recorded.</p>
                ) : (
                  <ol className="timeline">
                    {page.items.map((item, index) => (
                      <li key={`${item.entityType}-${item.entityId}-${item.dateType}-${index}`}>
                        <time dateTime={item.timestamp}>{formatTime(item.timestamp)}</time>
                        <strong>{item.dateType.replaceAll('_', ' ')}</strong>
                        <div className="muted">
                          Precision: {item.precision} · Source: {item.source}
                          {item.summary ? ` · ${item.summary}` : ''}
                        </div>
                      </li>
                    ))}
                  </ol>
                )
              }
            </ResourceState>
          </div>
        </>
      )}
    </WorkspacePage>
  );
}
