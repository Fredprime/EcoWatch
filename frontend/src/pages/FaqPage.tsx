import { Link } from 'react-router-dom';

/**
 * Public FAQ. Holds the process and score caveats that used to sit on the home
 * page and in the footer. Wording stays within the product boundaries: a score
 * ranks candidates for human review and never states a source, cause or harm.
 */
export function FaqPage() {
  return (
    <div className="public-page public-narrow">
      <header className="public-page-header">
        <h1>Frequently asked questions</h1>
        <p>How observations are handled, what a correlation score means, and how automated output is used.</p>
      </header>

      <section className="public-section" aria-labelledby="faq-process-title">
        <h2 id="faq-process-title">How does the process work?</h2>
        <ol className="public-steps">
          <li><strong>Collect</strong> — observations are preserved with their provenance.</li>
          <li><strong>Analyse</strong> — explainable suggestions help reviewers find related records.</li>
          <li><strong>Prioritise</strong> — transparent factors and human decisions guide review.</li>
          <li><strong>Intervene</strong> — approved actions are recorded separately from outcomes.</li>
          <li><strong>Verify</strong> — outcomes are assessed later with suitable evidence.</li>
        </ol>
        <p className="muted">
          No step in this process declares a source, cause or harm on its own.
        </p>
      </section>

      <section className="public-section" aria-labelledby="faq-score-title">
        <h2 id="faq-score-title">What does a correlation score mean?</h2>
        <p>
          A correlation score is a ranking signal only. It helps reviewers order related records for
          inspection. It is not a probability, a severity rating or a danger level, and it does not
          establish a source, causation or harm.
        </p>
        <p>
          Suggestions are explainable: reviewers can see why records were compared and can accept, reject
          or mark them ambiguous. Comparisons use the available wording, timing and location precision.
          When a validated semantic model is not available, a labelled <code>token_similarity</code> fallback
          is used — it is a fallback, not a validated semantic model.
        </p>
      </section>

      <section className="public-section" aria-labelledby="faq-output-title">
        <h2 id="faq-output-title">How is automated output used?</h2>
        <p>
          Automated output is decision support only. It does not establish sources, causation or harm.
          Published summaries are redacted and reviewed by authorised staff.
        </p>
      </section>

      <p className="public-after-form"><Link to="/">Return to the public home page</Link></p>
    </div>
  );
}
