import { useCallback, useRef, useState } from 'react';
import { WorkspacePage } from './WorkspacePage';
import { Notice } from '../components/Notice';
import { EmptyState } from '../components/EmptyState';
import { ResourceState } from '../components/ResourceState';
import { SignInPrompt } from '../components/SignInPrompt';
import { useAuth } from '../auth/authContext';
import { useApiResource } from '../hooks/useApiResource';
import { decideSuggestion, listSuggestions } from '../api/correlation';
import { errorMessage } from '../api/client';
import type { CorrelationDecision, CorrelationSuggestion } from '../api/types';

function SuggestionRow({
  suggestion,
  onDecided,
}: {
  suggestion: CorrelationSuggestion;
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
        </td>
      </tr>
    </>
  );
}

export function EvidencePage() {
  const { status } = useAuth();
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
                        <SuggestionRow key={item.id} suggestion={item} onDecided={handleDecided} />
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            }
          </ResourceState>
        )}
      </div>

      <p className="muted">
        Decisions are recorded and audited by the server. Original observations are never overwritten.
      </p>
    </WorkspacePage>
  );
}
