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
          Report without an account. Your wording is kept as given, contact details are stored separately,
          and authorised reviewers examine the evidence — a report is never treated as proof.
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
            <p>No account needed. Describe what you saw and how sure you are about when and where.</p>
            <Link to="/report">Open the report form</Link>
          </article>
          <article className="public-card">
            <h3>Track</h3>
            <p>Use your tracking code to confirm the server receipt. No identity or exact location is returned.</p>
            <Link to="/track">Look up a receipt</Link>
          </article>
          <article className="public-card">
            <h3>Read public updates</h3>
            <p>Approved, redacted case summaries — reviewed records, not automated findings.</p>
            <Link to="/updates">See public updates</Link>
          </article>
        </div>
      </section>
    </div>
  );
}
