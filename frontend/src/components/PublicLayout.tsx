import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../auth/authContext';
import '../public.css';

const PUBLIC_NAV = [
  { to: '/', label: 'Home', end: true },
  { to: '/report', label: 'Report', end: false },
  { to: '/track', label: 'Track a report', end: false },
  { to: '/updates', label: 'Public updates', end: false },
];

/**
 * Lightweight shell for pages that need no account. Deliberately unlike the
 * staff workspace: no sidebar, no role controls, no record-management actions.
 */
export function PublicLayout() {
  const { status } = useAuth();

  return (
    <div className="public-shell">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <header className="public-header">
        <div className="public-header-inner">
          <NavLink to="/" className="public-brand" aria-label="EcoWatch home">
            <span className="public-brand-title">EcoWatch</span>
            <span className="public-brand-subtitle">Evidence-led environmental intelligence</span>
          </NavLink>
          <nav className="public-nav" aria-label="Public navigation">
            <ul>
              {PUBLIC_NAV.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) => `public-nav-link${isActive ? ' active' : ''}`}
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="public-account">
            {status === 'authenticated' ? (
              <NavLink to="/workspace" className="btn btn-secondary">Staff workspace</NavLink>
            ) : (
              <NavLink to="/login" className="btn btn-secondary">Staff sign in</NavLink>
            )}
          </div>
        </div>
      </header>

      <main id="main-content" className="public-main" tabIndex={-1}>
        <Outlet />
      </main>

      <footer className="public-footer">
        <div className="public-footer-inner">
          <p>
            Automated output is decision support only. It does not establish sources, causation or harm.
            Published summaries are redacted and reviewed by authorised staff.
          </p>
          <p className="public-footer-sub">Share only what is safe to share. Sensitive locations are restricted or generalised.</p>
        </div>
      </footer>
    </div>
  );
}
