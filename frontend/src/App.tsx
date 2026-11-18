import { useMemo, useState } from 'react';
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom';
import './App.css';
import { WORKSPACES } from './types';
import { OverviewPage } from './pages/OverviewPage';
import { ReportPage } from './pages/ReportPage';
import { CasesPage } from './pages/CasesPage';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { EvidencePage } from './pages/EvidencePage';
import { SimpleWorkspace } from './pages/SimpleWorkspace';

type RoleView = 'all' | 'contributor' | 'reviewer' | 'investigator' | 'specialist' | 'manager' | 'admin';

const ROLE_OPTIONS: { id: RoleView; label: string }[] = [
  { id: 'all', label: 'Demo: all workspaces' },
  { id: 'contributor', label: 'Community / field contributor' },
  { id: 'reviewer', label: 'Reviewer' },
  { id: 'investigator', label: 'Investigator' },
  { id: 'specialist', label: 'Environmental specialist' },
  { id: 'manager', label: 'Intervention manager' },
  { id: 'admin', label: 'Administrator' },
];

function NotFoundPage() {
  return (
    <section>
      <header className="page-header">
        <h1>Page not found</h1>
        <p>The page you requested does not exist in this scaffold. Use the workspace navigation to continue.</p>
      </header>
      <div className="card notice notice-info" role="note">
        In the full product, access to workspaces and records is role-scoped and enforced server-side.
      </div>
    </section>
  );
}

function Layout() {
  const [roleView, setRoleView] = useState<RoleView>('all');

  const visibleWorkspaces = useMemo(() => {
    if (roleView === 'all') return WORKSPACES;
    return WORKSPACES.filter((ws) => ws.roles.includes('all') || ws.roles.includes(roleView));
  }, [roleView]);

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
            {visibleWorkspaces.map((ws) => (
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
        <p className="sidebar-note">
          Navigation is role-scoped in production. This selector is a UI demo only; permissions must be enforced server-side.
        </p>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <strong>Prototype frontend scaffold</strong>
            <div className="topbar-meta">Design baseline — no backend integration, no live data.</div>
          </div>
          <div className="field" style={{ margin: 0, minWidth: '260px' }}>
            <label htmlFor="role-view">Role view (UI demo)</label>
            <select id="role-view" value={roleView} onChange={(e) => setRoleView(e.target.value as RoleView)}>
              {ROLE_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>{opt.label}</option>
              ))}
            </select>
          </div>
        </header>
        <main id="main-content" className="content" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/cases/:caseId" element={<CaseDetailPage />} />
            <Route path="/analysis" element={<SimpleWorkspace title="Analysis" description="Datasets, methods, outputs and interpretation. Derived artefacts are linked to source data and versions; interpretations are separate reviewed records." />} />
            <Route path="/prioritisation" element={<SimpleWorkspace title="Prioritisation" description="Transparent factors and human review decisions. The system supports prioritisation; it does not independently decide enforcement or public-safety action." />} />
            <Route path="/interventions" element={<SimpleWorkspace title="Interventions" description="Approved actions, owners, milestones and records. Activity completion is distinct from environmental outcome." />} />
            <Route path="/verification" element={<SimpleWorkspace title="Verification" description="Baselines, follow-up measurements and outcome assessments. Recovery claims require suitable evidence, comparison, and qualified review." />} />
            <Route path="/admin" element={<SimpleWorkspace title="Administration" description="Users, organisations, vocabularies, imports, audit and configuration. Access is restricted and audited in production." />} />
            <Route path="*" element={<NotFoundPage />} />
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
