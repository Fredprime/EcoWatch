# EcoWatch UI Catalogue

**Standard:** `GLOBAL_AGENT_RULES_MERGED.md` §17.1 (`UI-<AREA>-<NNN>` stable identifiers; never reuse or renumber IDs).  
**Last Updated:** 2026-11-19

## Public No-Login Surface (`PublicLayout`)

- **`UI-PUB-001` — Public Home Page**
  - **Purpose:** Public entry point linking to anonymous reporting, receipt tracking, public case updates, and FAQ.
  - **Source & Route:** `frontend/src/pages/PublicHomePage.tsx` (`/`).
  - **States:** Static navigation cards + theme toggle; no service-health or internal diagnostics exposed.
  - **Accessibility:** Semantic headings, keyboard-focusable links, WCAG AA light/dark tokens.
- **`UI-PUB-002` — Anonymous Observation & Photo Report Form**
  - **Purpose:** Submit environmental observations anonymously with optional client-previewed photos (`image/jpeg`, `image/png`, `image/webp`, 15 MB cap) and offline IndexedDB queue (`offlineQueue.ts`).
  - **Source & Route:** `frontend/src/pages/ReportPage.tsx` (`/report`).
  - **States:** Ready, offline queued/syncing/failed, uploading photo, uploaded, validation/server error, tracking receipt.
  - **Accessibility:** Explicit `<label>` associations, inline error notices, non-colour status text.
- **`UI-PUB-003` — Receipt Lookup Page**
  - **Purpose:** Look up a PII-free submission receipt using the server-issued tracking code.
  - **Source & Route:** `frontend/src/pages/TrackPage.tsx` (`/track`).
  - **States:** Idle, loading, receipt found, 404/429 lockout error.
  - **Accessibility:** Form labels, `role="alert"` error feedback.
- **`UI-PUB-004` — Public Case Updates & Detail**
  - **Purpose:** View approved, redacted public case summaries without contributor identity or exact locations.
  - **Source & Route:** `frontend/src/pages/PublicUpdatesPage.tsx` (`/updates`), `frontend/src/pages/PublicCaseDetailPage.tsx` (`/updates/:caseId`).
  - **States:** Loading, empty, populated list/detail, error.
  - **Accessibility:** Accessible tables/cards, restricted map placeholder notice.
- **`UI-PUB-005` — FAQ & Generic 404**
  - **Purpose:** Process overview, correlation caveats, and generic 404 without leaking internal diagnostics.
  - **Source & Route:** `frontend/src/pages/FaqPage.tsx` (`/faq`), `frontend/src/pages/NotFoundPage.tsx` (`*`).
  - **States:** Static content.
  - **Accessibility:** Semantic landmarks and focusable FAQ shortcut button.

## Authentication & Staff Shell (`StaffLayout`)

- **`UI-AUTH-001` — Sign-In Page**
  - **Purpose:** Authenticate staff/admin users via `POST /api/v1/auth/login` and redirect to the requested workspace.
  - **Source & Route:** `frontend/src/pages/LoginPage.tsx` (`/login`).
  - **States:** Idle, submitting, invalid credentials/429 lockout error, authenticated redirect.
  - **Accessibility:** Centred single-column form, explicit labels, visible focus.
- **`UI-NAV-001` — Staff Overview & Sidebar Navigation**
  - **Purpose:** Role-gated workspace overview, service health read, and sign-out (`POST /api/v1/auth/logout`).
  - **Source & Route:** `frontend/src/pages/OverviewPage.tsx` (`/workspace`), `frontend/src/App.tsx`.
  - **States:** Loading, authenticated overview, permission notices, theme toggle (`UI-NAV-002`).
  - **Accessibility:** Collapsible/responsive nav, `role="switch"` theme toggle (`ThemeToggle.tsx`).

## Investigation & Phase 3 Workspaces

- **`UI-CASE-001` — Cases List & Case Detail / Timeline**
  - **Purpose:** Inspect org-scoped cases, linked observations, and chronological timelines.
  - **Source & Route:** `frontend/src/pages/CasesPage.tsx` (`/cases`), `frontend/src/pages/CaseDetailPage.tsx` (`/cases/:caseId`).
  - **States:** Loading, empty, populated, 403/404 error.
  - **Accessibility:** Scrollable `role="region"` tables with `tabIndex={0}`.
- **`UI-EVID-001` — Evidence & Correlation Review**
  - **Purpose:** Inspect observations, evidence assets, and review correlation suggestions (accept/reject/ambiguous).
  - **Source & Route:** `frontend/src/pages/EvidencePage.tsx` (`/evidence`).
  - **States:** Loading, empty, reviewing, error.
  - **Accessibility:** Accessible action buttons and status badges with text labels.
- **`UI-MON-001` — Environmental Monitoring & Dataset Catalogue**
  - **Purpose:** Browse datasets, immutable versions, WKT coverage geometry via lazy-loaded `LazyWktMap`, and register datasets/versions.
  - **Source & Route:** `frontend/src/pages/MonitoringPage.tsx` (`/monitoring`).
  - **States:** Loading, empty, map/list populated, collapsible create/version forms, error.
  - **Accessibility:** Non-map table alternative alongside `LazyWktMap`.
- **`UI-ANL-001` — Environmental Analysis**
  - **Purpose:** Browse entities (with `LazyWktMap`), relationships, analysis runs/outputs, and create entities, propose relationships, or queue runs.
  - **Source & Route:** `frontend/src/pages/AnalysisPage.tsx` (`/analysis`).
  - **States:** Loading, empty, populated, collapsible write forms, error.
  - **Accessibility:** Labelled `RecordPicker` and `ActionPanel` controls.
- **`UI-PRI-001` — Prioritisation**
  - **Purpose:** View transparent prioritisation factors/decisions, create assessments, and record human decisions.
  - **Source & Route:** `frontend/src/pages/PrioritisationPage.tsx` (`/prioritisation`).
  - **States:** Loading, empty, populated, collapsible write forms, error.
  - **Accessibility:** Explicit decision-support warning notice and labelled inputs.
- **`UI-INT-001` — Interventions**
  - **Purpose:** View interventions (with `LazyWktMap`), milestones, create interventions, add/complete milestones, and transition status.
  - **Source & Route:** `frontend/src/pages/InterventionsPage.tsx` (`/interventions`).
  - **States:** Loading, empty, populated, collapsible write forms, error.
  - **Accessibility:** Non-map table alternative and labelled form controls.
- **`UI-VER-001` — Verification & Publications**
  - **Purpose:** Manage indicators, qualified measurements, outcome assessments, and approved public summaries.
  - **Source & Route:** `frontend/src/pages/VerificationPage.tsx` (`/verification`).
  - **States:** Loading, empty, populated, collapsible write forms, error.
  - **Accessibility:** Explicit verification-boundary notice and labelled form controls.
- **`UI-ADM-001` — Administration**
  - **Purpose:** View organisations, queue summaries, audit events, and create organisations, users, or memberships.
  - **Source & Route:** `frontend/src/pages/AdminPage.tsx` (`/admin`).
  - **States:** Loading, empty, populated, collapsible write forms, error.
  - **Accessibility:** Restricted-workspace notice and keyboard-navigable tables.
