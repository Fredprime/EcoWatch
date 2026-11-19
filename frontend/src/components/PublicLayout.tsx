import { NavLink, Outlet, useLocation } from 'react-router-dom';
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
 * Anonymous visitors are never offered a staff sign-in link or told where it is.
 */
export function PublicLayout() {
  const { status } = useAuth();
  const location = useLocation();

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
          {status === 'authenticated' && (
            <div className="public-account">
              <NavLink to="/workspace" className="btn btn-secondary">Staff workspace</NavLink>
            </div>
          )}
        </div>
      </header>

      <main id="main-content" className="public-main" tabIndex={-1}>
        <Outlet />
      </main>

      {location.pathname !== '/faq' && (
        <NavLink
          to="/faq"
          className="public-faq-button"
          aria-label="Frequently asked questions"
          title="Frequently asked questions"
        >
          ?
        </NavLink>
      )}

      <footer className="public-footer">
        <div className="public-footer-inner">
          <p className="public-footer-sub">Share only what is safe to share. Sensitive locations are restricted or generalised.</p>
        </div>
      </footer>
    </div>
  );
}
