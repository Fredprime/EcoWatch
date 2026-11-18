import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom';
import './App.css';
import { WORKSPACES } from './types';
import { OverviewPage } from './pages/OverviewPage';
import { ReportPage } from './pages/ReportPage';
import { CasesPage } from './pages/CasesPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { SimpleWorkspace } from './pages/SimpleWorkspace';

function Layout() {
  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <aside className="sidebar" aria-label="Workspace navigation">
        <div className="brand">
          <p className="brand-title">EcoWatch</p>
          <p className="brand-subtitle">Evidence-led environmental intelligence</p>
        </div>
        <nav aria-label="Primary">
          <ul className="nav-list">
            {WORKSPACES.map((ws) => (
              <li key={ws.id}>
                <NavLink
                  to={ws.path}
                  end={ws.path === '/'}
                  className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
                >
                  {ws.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <p className="sidebar-note">Workspaces are role-scoped in production. Navigation shown here reflects the documented product baseline.</p>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <strong>Prototype frontend scaffold</strong>
            <div className="topbar-meta">Design baseline — no backend integration, no live data.</div>
          </div>
          <div className="topbar-meta" aria-label="Role context placeholder">Role view: demo (all workspaces visible)</div>
        </header>
        <main id="main-content" className="content" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="/evidence" element={<SimpleWorkspace title="Evidence Intelligence" description="Candidate relationships, duplicate review and evidence context. Suggestions must be explainable, reversible, and reviewed by authorised humans." />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/analysis" element={<SimpleWorkspace title="Analysis" description="Datasets, methods, outputs and interpretation. Derived artefacts are linked to source data and versions; interpretations are separate reviewed records." />} />
            <Route path="/prioritisation" element={<SimpleWorkspace title="Prioritisation" description="Transparent factors and human review decisions. The system supports prioritisation; it does not independently decide enforcement or public-safety action." />} />
            <Route path="/interventions" element={<SimpleWorkspace title="Interventions" description="Approved actions, owners, milestones and records. Activity completion is distinct from environmental outcome." />} />
            <Route path="/verification" element={<SimpleWorkspace title="Verification" description="Baselines, follow-up measurements and outcome assessments. Recovery claims require suitable evidence, comparison, and qualified review." />} />
            <Route path="/admin" element={<SimpleWorkspace title="Administration" description="Users, organisations, vocabularies, imports, audit and configuration. Access is restricted and audited in production." />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
