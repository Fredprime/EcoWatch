import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  BrowserRouter,
  NavLink,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from 'react-router-dom';
import './App.css';
import { WORKSPACES } from './types';
import { useAuth } from './auth/authContext';
import { AuthProvider } from './auth/AuthProvider';
import { PublicLayout } from './components/PublicLayout';
import { PublicHomePage } from './pages/PublicHomePage';
import { PublicUpdatesPage } from './pages/PublicUpdatesPage';
import { PublicCaseDetailPage } from './pages/PublicCaseDetailPage';
import { TrackPage } from './pages/TrackPage';
import { LoginPage } from './pages/LoginPage';
import { ReportPage } from './pages/ReportPage';
import { OverviewPage } from './pages/OverviewPage';
import { CasesPage } from './pages/CasesPage';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { EvidencePage } from './pages/EvidencePage';
import { AnalysisPage } from './pages/AnalysisPage';
import { PrioritisationPage } from './pages/PrioritisationPage';
import { InterventionsPage } from './pages/InterventionsPage';
import { VerificationPage } from './pages/VerificationPage';
import { AdminPage } from './pages/AdminPage';

function NotFoundPage() {
  return (
    <div className="public-page public-narrow">
      <h1>Page not found</h1>
      <p>The page you requested does not exist. Use the navigation above to continue.</p>
      <p><a href="/">Return to the public home page</a></p>
    </div>
  );
}

/** Staff-only guard. The backend still enforces every permission independently. */
function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status !== 'authenticated') {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return <>{children}</>;
}

function StaffLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [authAnnouncement, setAuthAnnouncement] = useState('');
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { status, me, logout } = useAuth();
  const previousStatus = useRef(status);

  useEffect(() => {
    const id = window.requestAnimationFrame(() => setMenuOpen(false));
    return () => window.cancelAnimationFrame(id);
  }, [location.pathname]);

  useEffect(() => {
    if (previousStatus.current !== status) {
      setAuthAnnouncement(
        status === 'authenticated'
          ? `Signed in${me ? ` as ${me.displayName}` : ''}.`
          : 'Signed out.',
      );
      previousStatus.current = status;
    }
  }, [status, me]);

  useEffect(() => {
    if (!menuOpen) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [menuOpen]);

  function focusMain() {
    window.requestAnimationFrame(() => document.getElementById('main-content')?.focus());
  }

  function openMenu() {
    setMenuOpen(true);
    window.requestAnimationFrame(() => {
      navRef.current?.querySelector<HTMLAnchorElement>('.nav-link')?.focus();
    });
  }

  function closeMenu() {
    setMenuOpen(false);
    menuButtonRef.current?.focus();
  }

  function navigateFromMenu() {
    setMenuOpen(false);
    focusMain();
  }

  function signOut() {
    logout();
    setAuthAnnouncement('Signed out.');
    navigate('/login');
    focusMain();
  }

  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <p className="sr-only" role="status">{authAnnouncement}</p>
      {menuOpen && <button type="button" className="sidebar-backdrop" aria-label="Close menu" onClick={closeMenu} />}
      <aside className={`sidebar${menuOpen ? ' open' : ''}`} aria-label="Workspace navigation">
        <div className="sidebar-header">
          <div className="brand">
            <p className="brand-title">EcoWatch</p>
            <p className="brand-subtitle">Evidence-led environmental intelligence</p>
          </div>
          <button type="button" className="btn btn-secondary menu-close" onClick={closeMenu}>
            Close
          </button>
        </div>
        <nav id="primary-nav" ref={navRef} aria-label="Primary">
          <ul className="nav-list">
            {WORKSPACES.map((ws) => (
              <li key={ws.id}>
                <NavLink
                  to={ws.path}
                  end={ws.path === '/workspace'}
                  className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
                  onClick={navigateFromMenu}
                >
                  {ws.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <p className="sidebar-note">
          Navigation lists the documented workspaces. Record access and reviewer actions are enforced server-side.
        </p>
        <button type="button" className="btn btn-secondary public-return" onClick={() => navigate('/')}>
          Public site
        </button>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              ref={menuButtonRef}
              className="btn btn-secondary menu-button icon-button"
              aria-expanded={menuOpen}
              aria-controls="primary-nav"
              aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              title={menuOpen ? 'Close menu' : 'Open menu'}
              onClick={() => (menuOpen ? closeMenu() : openMenu())}
            >
              <span aria-hidden="true" className="menu-dots">
                <span></span><span></span><span></span>
              </span>
            </button>
            <div>
              <strong>EcoWatch staff workspace</strong>
              <div className="topbar-meta">Evidence-led environmental intelligence</div>
            </div>
          </div>
          <div className="topbar-account">
            {me ? (
              <>
                <div>
                  <span className="topbar-name">{me.displayName}</span>
                  <div className="topbar-meta">Signed in</div>
                </div>
                <button type="button" className="btn btn-secondary" onClick={signOut}>Sign out</button>
              </>
            ) : (
              <NavLink to="/login" className="btn btn-secondary">Sign in</NavLink>
            )}
          </div>
        </header>
        <main id="main-content" className="content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route path="/" element={<PublicHomePage />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="/track" element={<TrackPage />} />
            <Route path="/updates" element={<PublicUpdatesPage />} />
            <Route path="/updates/:caseId" element={<PublicCaseDetailPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>

          <Route element={<RequireAuth><StaffLayout /></RequireAuth>}>
            <Route path="/workspace" element={<OverviewPage />} />
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/cases/:caseId" element={<CaseDetailPage />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/prioritisation" element={<PrioritisationPage />} />
            <Route path="/interventions" element={<InterventionsPage />} />
            <Route path="/verification" element={<VerificationPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
