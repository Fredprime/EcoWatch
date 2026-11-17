# EcoWatch Project Tracking

**Version:** 1.1  
**Date:** 2026-11-17  
**Project:** EcoWatch (Merged Project — canonical baseline in `docs/`, incorporating SignalWeave as the Evidence Correlation and Incident Intelligence subsystem)  
**Repository:** `Fredprime/EcoWatch`  
**Working Branch:** `prime` (branched from `master`; never push directly to `main` or `master`)  
**Status:** Documentation baseline consolidated on branch `prime`; infrastructure baseline present; zero application code written yet.

---

## 1. Working Rules and Git Workflow

- **Branching rule:** Work on branch `prime` (branched from `master`), review changes, and push to `prime`. Never commit or push directly to `main` (sacred release branch) or `master` (integration branch receiving reviewed PRs). Do not delete branches after merging unless explicitly asked by the maintainer.
- **Commit style:** Conventional commits `type(scope): summary` (imperative, <= 72 chars), per `CONTRIBUTING.md`.
- **Documentation precedence:**
  1. Explicit owner instructions for the current task.
  2. Canonical merged docs at `docs/00`–`docs/24` (`docs/START_HERE.md`, `docs/PACKAGE_MANIFEST.json`) and ADRs in `docs/20_Technical_Decision_Records.md`.
  3. `docs/EcoWatch Agent Guide.md`, `CONTRIBUTING.md`, and user global rules (minimal, YAGNI, native capabilities first).
  4. `docs/files/22_Correlation_Engine_and_Offline_Collection.md` (secondary source; merged baseline wins on conflicts).
  5. `docs/EcoWatch_Full_Project_Documentation_v0.1/` and `docs/SignalWeave_Documentation/` (historical context only).
- **Subagent dispatch:** Delegate bounded research, implementation, verification, and documentation tasks to subagents where parallel or isolated context is beneficial.
- **Safety boundaries (always enforced):**
  - No seeded, sample, or demo data in the product; tests create and clean up temporary records.
  - Automated correlation/AI is decision support only; human review is required for cases, `"field verified"`, and `"recovery verified"`.
  - Original observations and evidence files remain immutable/untouched; identity is stored separately from public views; four timestamps (`event_start_at`, `observed_at`, `submitted_at`, `received_at`) remain distinct.
  - Record architectural decisions in `docs/20_Technical_Decision_Records.md` before landing code.

---

## 2. What Has Been Done

1. **Full documentation audit across all documentation packages (no code written):**
   - Read `docs/EcoWatch Agent Guide.md` (v1.0) and `docs/RULES_COMPARISON_AND_MERGE_REPORT.md`.
   - Read all 26 canonical merged baseline files (`START_HERE.md`, `PACKAGE_MANIFEST.json`, `00`–`24`).
   - Read `docs/files/START_HERE.md`, `docs/files/22_Correlation_Engine_and_Offline_Collection.md` (v0.8), and `docs/files/23_SignalWeave_Merge_Record.md`.
   - Dispatched research subagents to read and summarize `docs/SignalWeave_Documentation/` (`PRD.md`, `TECHNICAL.md`) and `docs/EcoWatch_Full_Project_Documentation_v0.1/EcoWatch_Documentation/` (`START_HERE.md`, `00`–`19`).
2. **Repository & branch setup (`Fredprime/EcoWatch`):**
   - Cloned `Fredprime/EcoWatch` (baseline commit `88ca75d` on `master`, which already includes `compose.yaml` with PostGIS 16-3.4, `Makefile`, `scripts/compose.sh`, `.env.example`, `.github/workflows/ci.yml`, `CONTRIBUTING.md`, `LICENSE`, `NOTICE`, and the 26 canonical merged `docs/` files).
   - Created working branch `prime` from `master`.
   - Added `docs/EcoWatch Agent Guide.md`, `docs/RULES_COMPARISON_AND_MERGE_REPORT.md`, `docs/PROJECT_TRACKING.md`, `docs/files/` (excluding `.zip`), `docs/SignalWeave_Documentation/`, and `docs/EcoWatch_Full_Project_Documentation_v0.1/` (without duplicating `docs/` or copying any `.zip` archives).

---

## 3. What We Are Doing Now

- Reviewing and pushing the consolidated documentation baseline on branch `prime`.
- Holding before writing `backend/` or `frontend/` application code until review is complete and pre-build confirmations are settled.

---

## 4. What Is Left To Be Done

### Step A — Review & Pre-Build Confirmations (Before Writing Code)
- [ ] Review documentation baseline on branch `prime`.
- [ ] Record ADRs in `docs/20_Technical_Decision_Records.md` for confirmed stack decisions already reflected in repo infra (`Python 3.14 + FastAPI`, `PostgreSQL 16 + PostGIS 3.4`, `React + TypeScript`, local dev containers via Podman/Docker Compose).
- [ ] Confirm naming convention boundary (`lower snake_case` DB tables/columns mapped to `camelCase` API/code fields; `UPPER_SNAKE_CASE` constants).
- [ ] Confirm Phase 1 auth/role scope (anonymous + registered contributors vs. staff/admin roles) and local dev interfaces for object storage and auth.
- [ ] Confirm client vs. server image handling rule (uploading untouched originals vs. optional client compression marked as derivative).

### Step B — Phase 1: Unified Evidence Foundation (`backend/` Modular Monolith)
- [ ] Initialize `backend/` (`pyproject.toml`, FastAPI app skeleton, settings, Ruff/Pytest config matching `.github/workflows/ci.yml` and `Makefile`).
- [ ] PostgreSQL + PostGIS schema and Alembic migrations (`users`, `organisations`, `memberships`, `observations`, `observation_versions`, `observation_sources`, `evidence_assets`, `asset_derivatives`, `cases`, `case_observations`, `audit_events`, `processing_jobs`).
- [ ] Identity, RBAC, separation of duties, and anonymous submission boundary.
- [ ] Idempotent Observation intake API (`event_start_at`, `observed_at`, `submitted_at`, `received_at`, precision fields, coordinate/unit validation).
- [ ] Evidence upload pipeline (content-type validation, size limits, server-generated storage keys, checksums, restricted original storage, separate derivative generation).
- [ ] Case management & many-to-many case-observation links (preserving original observations).
- [ ] Immutable/append-only audit logging for consequential actions.
- [ ] Unit, integration, security, and idempotency tests (temporary test records cleaned up after runs; `make lint` and `make test` green).

### Step C — Phase 2: Evidence Correlation & Offline Hardening (ECII)
- [ ] Bounded database-backed worker (`processing_jobs` with `FOR UPDATE SKIP LOCKED` row claiming, retries, bounded concurrency).
- [ ] Bounded PostGIS/temporal/category-aware candidate retrieval (excluding previously rejected relationships).
- [ ] Task-specific correlation scoring (semantic, spatial, temporal, context; missing-signal denominator exclusion; deterministic fallback; `evidence_relationships` with component scores & plain-language reason codes).
- [ ] Source-dependency / duplicate-repost tracking.
- [ ] Reviewer workflow (accept, reject, mark ambiguous; merge/split with audit; no naive transitive clustering).
- [ ] Labelled evaluation harness measuring precision, recall, false links, missed links, and ambiguity.
- [ ] Offline-first PWA queue & sync support (when `frontend/` begins: IndexedDB, client UUIDs, split-phase text-then-media upload, explicit sync states).

### Step D — Phase 3: Environmental Intelligence
- [ ] Dataset catalogue & versioning (`datasets`, `dataset_versions` with licence, attribution, coverage, limitations).
- [ ] Reproducible analysis runs (`analysis_runs`, `analysis_outputs` with CRS, quality masks, seasonality context).
- [ ] Environmental entities and typed `environmental_relationships` (upstream/downstream, source-pathway-receptor hypotheses with uncertainty).

### Step E — Phase 4: Prioritisation & Intervention Management
- [ ] Transparent prioritisation factor records (`prioritisation_assessments`) with human rationale.
- [ ] Case assignment, referral records, interventions (`interventions`, `intervention_milestones`), and baseline definitions.

### Step F — Phase 5: Verification, UI & Release Readiness
- [ ] Indicator definitions/measurements and `verification_assessments` (separating activity completion, output, outcome, and `"recovery verified"`).
- [ ] Multi-role `frontend/` (React + TypeScript + MapLibre GL JS; Overview, Report/Collect, Evidence Intelligence, Cases, Monitoring/Analysis, Prioritisation, Interventions, Verification, Admin) following light/clean UI rules.
- [ ] End-to-end, offline, performance, usability, backup/restore, and legal/governance release-gate verification before any live pilot.
