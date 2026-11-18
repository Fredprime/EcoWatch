import { useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ResourceState } from '../components/ResourceState';
import { useApiResource } from '../hooks/useApiResource';
import { getHealth } from '../api/health';

export function PublicHomePage() {
  const loadHealth = useCallback(() => getHealth(), []);
  const health = useApiResource(loadHealth, 'public-health');

  return (
    <div className="public-page">
      <section className="public-hero">
        <p className="public-eyebrow">Environmental observations, handled with care</p>
        <h1>Report what you saw. Follow what happens next.</h1>
        <p className="public-lede">
          EcoWatch keeps an observation with its reported time and location precision, stores contributor
          identity separately, and helps authorised reviewers examine evidence — without treating a report
          as proof.
        </p>
        <div className="public-hero-actions">
          <Link to="/report" className="btn">Submit an observation</Link>
          <Link to="/track" className="btn btn-secondary">Track a report</Link>
        </div>
        <div className="public-status">
          <ResourceState state={health.state}>
            {(data) => (
              <p className="muted">
                Service {data.status} · Database {data.database}
                {data.postgisVersion ? ' · Spatial store available' : ''}
              </p>
            )}
          </ResourceState>
        </div>
      </section>

      <section className="public-section" aria-labelledby="public-actions-title">
        <h2 id="public-actions-title">What you can do here</h2>
        <div className="public-cards">
          <article className="public-card">
            <h3>Report</h3>
            <p>
              Send an observation without an account. Describe what you observed and how certain you are
              about the time and place.
            </p>
            <Link to="/report">Open the report form</Link>
          </article>
          <article className="public-card">
            <h3>Track</h3>
            <p>
              If you were given a tracking code, check the server receipt for your report. No identity or
              exact location is returned.
            </p>
            <Link to="/track">Look up a receipt</Link>
          </article>
          <article className="public-card">
            <h3>Read public updates</h3>
            <p>
              Approved, redacted case summaries show recorded status and public context. They are reviewed
              records, not automated findings.
            </p>
            <Link to="/updates">See public updates</Link>
          </article>
        </div>
      </section>

      <section className="public-section" aria-labelledby="public-process-title">
        <h2 id="public-process-title">How the process works</h2>
        <ol className="public-steps">
          <li><strong>Collect</strong> — observations are preserved with their provenance.</li>
          <li><strong>Analyse</strong> — explainable suggestions help reviewers find related records.</li>
          <li><strong>Prioritise</strong> — transparent factors and human decisions guide review.</li>
          <li><strong>Intervene</strong> — approved actions are recorded separately from outcomes.</li>
          <li><strong>Verify</strong> — outcomes are assessed later with suitable evidence.</li>
        </ol>
        <p className="muted">
          A correlation score is a ranking signal only. No step in this process declares a source, cause or
          harm on its own.
        </p>
      </section>
    </div>
  );
}
