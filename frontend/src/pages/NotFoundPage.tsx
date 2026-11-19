import { Link } from 'react-router-dom';

/**
 * Generic 404 for every unmatched public route. Only neutral copy is rendered:
 * paths, errors, request IDs and other diagnostics stay in administrator logs
 * and are never shown to a visitor.
 */
export function NotFoundPage() {
  return (
    <div className="public-page public-narrow public-not-found">
      <h1>Page not found</h1>
      <p>This page is not available. Check the address or use the links below to continue.</p>
      <p><Link to="/">Return to the public home page</Link></p>
    </div>
  );
}
