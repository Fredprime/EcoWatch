import { useCallback, useRef, useState } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';
import { ResourceState } from '../components/ResourceState';
import { SignInPrompt } from '../components/SignInPrompt';
import { useAuth } from '../auth/authContext';
import { CORRELATION_REVIEW_ROLES, hasAnyRole } from '../auth/roles';
import { useApiResource } from '../hooks/useApiResource';
import { decideSuggestion, listSuggestions } from '../api/correlation';
import { listObservationEvidence } from '../api/evidence';
import { listObservations } from '../api/observations';
import { errorMessage } from '../api/client';
import type { CorrelationDecision, CorrelationSuggestion } from '../api/types';

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function SuggestionRow({
  suggestion,
  canReview,
  onDecided,
}: {
  suggestion: CorrelationSuggestion;
  canReview: boolean;
  onDecided: (suggestionId: string) => void;
}) {
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function decide(decision: CorrelationDecision) {
    setBusy(true);
    setError(null);
    try {
      await decideSuggestion(suggestion.id, decision, reason.trim() || undefined);
      setReason('');
      onDecided(suggestion.id);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <tr>
        <th scope="row">{suggestion.id}</th>
        <td>
          <div>{suggestion.observationAId}</div>
          <div className="muted">↔ {suggestion.observationBId}</div>
        </td>
        <td>
          <div><strong>{suggestion.task.replaceAll('_', ' ')}</strong></div>
          <div className="muted">Ranking signal: {suggestion.score.toFixed(2)}</div>
          <div className="muted">Method: {suggestion.methodVersion}</div>
        </td>
        <td>
          <ul className="compact-list">
            {suggestion.reasons.map((item) => <li key={item}>{item}</li>)}
          </ul>
          {suggestion.missingSignals.length > 0 && (
            <p className="muted">Missing signals: {suggestion.missingSignals.join(', ')}</p>
          )}
          <p className="muted">Not a probability, severity, source or causation claim.</p>
        </td>
        <td>{suggestion.status.replaceAll('_', ' ')}</td>
        <td>
          {canReview ? (
            <>
              <label className="sr-only" htmlFor={`reason-${suggestion.id}`}>Reason for decision on {suggestion.id}</label>
              <input
                id={`reason-${suggestion.id}`}
                type="text"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Optional rationale"
                maxLength={2000}
              />
              <div className="row-actions">
                <button type="button" className="btn btn-secondary" disabled={busy} aria-busy={busy} onClick={() => void decide('accepted')}>Accept</button>
                <button type="button" className="btn btn-secondary" disabled={busy} aria-busy={busy} onClick={() => void decide('rejected')}>Reject</button>
                <button type="button" className="btn btn-secondary" disabled={busy} aria-busy={busy} onClick={() => void decide('ambiguous')}>Ambiguous</button>
              </div>
              {error && <p className="field-error" role="alert">{error}</p>}
            </>
          ) : (
            <p className="muted">Your role cannot record review decisions. The server enforces this.</p>
          )}
        </td>
      </tr>
    </>
  );
}

/** Read-only view of stored uploads; no bytes are fetched or shown here. */
function EvidenceReadback() {
  const { status } = useAuth();
  const [selectedId, setSelectedId] = useState('');
  const loadObservations = useCallback(() => listObservations(), []);
  const observations = useApiResource(
    loadObservations,
    'evidence-observations',
    status === 'authenticated',
  );
  const loadAssets = useCallback(() => listObservationEvidence(selectedId), [selectedId]);
  const assets = useApiResource(
    loadAssets,
    `evidence-assets:${selectedId}`,
    status === 'authenticated' && selectedId !== '',
  );

  return (
    <div className="card">
      <h2>Evidence read-back</h2>
      <p className="muted">
        Confirm that an uploaded photo is stored and how far its processing has got. Scan status is a
        processing state, not a finding.
      </p>
      {status !== 'authenticated' ? (
        <SignInPrompt what="Evidence records require an authenticated staff account." />
      ) : (
        <ResourceState state={observations.state}>
          {(page) => page.items.length === 0 ? (
            <EmptyState
              title="No observations in your permitted scope."
              detail="Uploaded evidence will appear against its observation."
            />
          ) : (
            <>
              <label className="sr-only" htmlFor="evidence-observation">Observation</label>
              <select
                id="evidence-observation"
                value={selectedId}
                onChange={(event) => setSelectedId(event.target.value)}
              >
                <option value="">Choose an observation</option>
                {page.items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.observationType.replaceAll('_', ' ')} · {item.id.slice(0, 8)}
                  </option>
                ))}
              </select>
              {selectedId !== '' && (
                <ResourceState state={assets.state}>
                  {(items) => items.length === 0 ? (
                    <EmptyState
                      title="No evidence assets for this observation."
                      detail="An upload receipt appears here once the server stores a file."
                    />
                  ) : (
                    <div className="table-wrap" role="region" aria-label="Evidence assets table" tabIndex={0}>
                      <table>
                        <thead>
                          <tr>
                            <th scope="col">Asset</th>
                            <th scope="col">Received</th>
                            <th scope="col">Scan</th>
                            <th scope="col">Metadata</th>
                            <th scope="col">Derivatives</th>
                          </tr>
                        </thead>
                        <tbody>
                          {items.map((asset) => (
                            <tr key={asset.id}>
                              <th scope="row">
                                <div>{asset.originalFilename}</div>
                                <div className="muted">{asset.id.slice(0, 8)} · {formatBytes(asset.sizeBytes)}</div>
                              </th>
                              <td>{formatTime(asset.receivedAt)}</td>
                              <td>
                                {asset.scanStatus.replaceAll('_', ' ')}
                                {asset.idempotentReplay && (
                                  <div className="muted">Retry of an existing upload</div>
                                )}
                              </td>
                              <td>{asset.metadataExtractionStatus.replaceAll('_', ' ')}</td>
                              <td>
                                {asset.derivatives.length === 0 ? (
                                  <span className="muted">None yet</span>
                                ) : (
                                  <ul className="compact-list">
                                    {asset.derivatives.map((derivative) => (
                                      <li key={derivative.id}>
                                        {derivative.derivativeType.replaceAll('_', ' ')} ·{' '}
                                        {derivative.mimeType} ·{' '}
                                        {derivative.exifStripped ? 'EXIF stripped' : 'EXIF retained'}
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </ResourceState>
              )}
            </>
          )}
        </ResourceState>
      )}
    </div>
  );
}

export function EvidencePage() {
  const { status, me } = useAuth();
  const canReview = hasAnyRole(me, CORRELATION_REVIEW_ROLES);
  const [announcement, setAnnouncement] = useState('');
  const queueHeadingRef = useRef<HTMLHeadingElement>(null);
  const loadSuggestions = useCallback(() => listSuggestions(), []);
  const suggestions = useApiResource(loadSuggestions, 'suggestions', status === 'authenticated');
  const { reload: reloadSuggestions } = suggestions;

  const handleDecided = useCallback(
    (suggestionId: string) => {
      setAnnouncement(`Decision recorded for suggestion ${suggestionId}. The queue has been refreshed.`);
      reloadSuggestions();
      window.requestAnimationFrame(() => queueHeadingRef.current?.focus());
    },
    [reloadSuggestions],
  );

  return (
    <WorkspacePage
      title="Evidence Intelligence"
      description="Candidate relationships awaiting review by authorised staff. Suggestions are explainable and reversible; correlation is a ranking signal, not proof."
    >
      <Notice variant="info" role="note" title="Review principle:">
        Machine suggestions do not declare sources, causation, illegality or harm. Similar reports are not independent corroboration without source checks.
      </Notice>

      <div className="card">
        <h2 ref={queueHeadingRef} tabIndex={-1}>Relationship review queue</h2>
        <p className="sr-only" role="status">{announcement}</p>
        {status !== 'authenticated' ? (
          <SignInPrompt what="Candidate relationships require an authenticated reviewer account." />
        ) : (
          <ResourceState state={suggestions.state}>
            {(items) =>
              items.length === 0 ? (
                <EmptyState
                  title="No candidate relationships to review."
                  detail="Explainable suggestions appear here when correlation jobs produce them."
                />
              ) : (
                <div className="table-wrap" role="region" aria-label="Candidate relationships table" tabIndex={0}>
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Suggestion</th>
                        <th scope="col">Observation pair</th>
                        <th scope="col">Ranking signal</th>
                        <th scope="col">Explanation</th>
                        <th scope="col">State</th>
                        <th scope="col">Decision</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((item) => (
                        <SuggestionRow
                          key={item.id}
                          suggestion={item}
                          canReview={canReview}
                          onDecided={handleDecided}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            }
          </ResourceState>
        )}
      </div>

      <EvidenceReadback />

      <p className="muted">
        Decisions are recorded and audited by the server. Original observations are never overwritten.
        Scan status and derivative metadata are processing records, not conclusions about the environment.
      </p>
    </WorkspacePage>
  );
}
