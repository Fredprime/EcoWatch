# EcoWatch Project Tracking

**Version:** 1.3  
**Date:** 2026-11-17  
**Project:** EcoWatch (Merged Project — canonical baseline in `docs/`, incorporating SignalWeave as the Evidence Correlation and Incident Intelligence subsystem)  
**Repository:** `Fredprime/EcoWatch`  
**Working Branch:** `prime` (branched from `master`; never push directly to `main` or `master`)  
**Status:** Three-phase backend architecture documented (`docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md`); zero code written yet; merging docs through `prime -> master -> main`.

---

## 1. Working Rules and Git Workflow

- **Branching rule:** Work on branch `prime` (branched from `master`), review changes, and push to `prime`. Never commit or push directly to `main` (sacred release branch) or `master` (integration branch receiving reviewed PRs). Do not delete branches after merging unless explicitly asked by the maintainer.
- **Commit style:** Conventional commits `type(scope): summary` (imperative, <= 72 chars), per `CONTRIBUTING.md`.
- **Documentation precedence:**
  1. Explicit owner instructions for the current task.
  2. Canonical merged docs at `docs/00`–`docs/24` (`docs/START_HERE.md`, `docs/PACKAGE_MANIFEST.json`) and ADRs in `docs/20_Technical_Decision_Records.md`.
  3. `docs/AGENT_GUIDE.md`, `CONTRIBUTING.md`, and user global rules (minimal, YAGNI, native capabilities first).
  4. `docs/files/22_Correlation_Engine_and_Offline_Collection.md` (secondary source; merged baseline wins on conflicts).
  5. `docs/archive/` (historical context only; never cited as authority).
- **Subagent dispatch:** Delegate bounded research, implementation, verification, and documentation tasks to subagents where parallel or isolated context is beneficial.
- **Safety boundaries (always enforced):**
  - No seeded, sample, or demo data in the product; tests create and clean up temporary records.
  - Automated correlation/AI is decision support only; human review is required for cases, `"field verified"`, and `"recovery verified"`.
  - Original observations and evidence files remain immutable/untouched; identity is stored separately from public views; four timestamps (`event_start_at`, `observed_at`, `submitted_at`, `received_at`) remain distinct.
  - Record architectural decisions in `docs/20_Technical_Decision_Records.md` before landing code.

---

## 2. What Has Been Done

1. **Full documentation audit across all documentation packages (no code written):**
   - Read `docs/AGENT_GUIDE.md` (v1.0) and `docs/RULES_COMPARISON_AND_MERGE_REPORT.md`.
   - Read all 26 canonical merged baseline files (`START_HERE.md`, `PACKAGE_MANIFEST.json`, `00`–`24`).
   - Read `docs/files/START_HERE.md`, `docs/files/22_Correlation_Engine_and_Offline_Collection.md` (v0.8), and `docs/files/23_SignalWeave_Merge_Record.md`.
   - Dispatched research subagents to read and summarize `docs/SignalWeave_Documentation/` (`PRD.md`, `TECHNICAL.md`) and `docs/EcoWatch_Full_Project_Documentation_v0.1/EcoWatch_Documentation/` (`START_HERE.md`, `00`–`19`).
2. **Repository & branch setup (`Fredprime/EcoWatch`):**
   - Cloned `Fredprime/EcoWatch` (baseline commit `88ca75d` on `master`, which already includes `compose.yaml` with PostGIS 16-3.4, `Makefile`, `scripts/compose.sh`, `.env.example`, `.github/workflows/ci.yml`, `CONTRIBUTING.md`, `LICENSE`, `NOTICE`, and the 26 canonical merged `docs/` files).
   - Created working branch `prime` from `master`.
   - Added `docs/AGENT_GUIDE.md` (then named `docs/EcoWatch Agent Guide.md`), `docs/RULES_COMPARISON_AND_MERGE_REPORT.md`, `docs/PROJECT_TRACKING.md`, `docs/files/` (excluding `.zip`), `docs/SignalWeave_Documentation/` and `docs/EcoWatch_Full_Project_Documentation_v0.1/` (later moved to `docs/archive/`), without duplicating `docs/` or copying any `.zip` archives, committed as `e5d5dd6`, and pushed to `origin/prime`.
3. **Branch protection & governance docs:**
   - Switched to `main`, ran `scripts/protect-branches.sh` to enforce squash-only merges, `delete_branch_on_merge=false`, and branch protections on `main` and `master`, then switched back to `prime`.
   - Created `docs/REVIEW_SUMMARY.md` (single review summary) and `docs/OWNER_RULES.md` (separate living record of owner rules), committed as `ccea786`, and pushed to `origin/prime`.
4. **Three-phase backend architecture blueprint (docs only, zero code):**
   - Dispatched research subagent to audit coverage across all 26 logical tables (`docs/08`), 58 functional requirements + 10 non-functional requirements (`docs/06`), and 11 logical modules (`docs/07`).
   - Created `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md` mapping the entire backend into 3 concrete phases (`Phase 1: Core/Intake/Cases`, `Phase 2: ECII Correlation/Worker/Offline Sync`, `Phase 3: Environmental Intelligence/Prioritisation/Interventions/Verification`).
   - Added `ADR-026` to `docs/20_Technical_Decision_Records.md` and updated `docs/OWNER_RULES.md`, `docs/REVIEW_SUMMARY.md`, and `docs/PROJECT_TRACKING.md`.
5. **Documentation hygiene (`Tazor` branch, on top of `prime`), docs only:**
   - Renamed `docs/EcoWatch Agent Guide.md` to `docs/AGENT_GUIDE.md` (no spaces in filenames) and updated every reference.
   - Added root `AGENTS.md` as the shared agent entry point, per `AGENT_GUIDE` §18, which previously described this but had nothing configured.
   - Removed the false claim in `AGENT_GUIDE` §4 that PostgreSQL/PostGIS/backend build prompts exist; `ADR-025` excludes them and none were present.
   - Moved `EcoWatch_Full_Project_Documentation_v0.1/` and `SignalWeave_Documentation/` to `docs/archive/` with `docs/archive/SUPERSEDED.md` explaining why they are not canonical.
   - Added `docs/files/DECISION_ID_CROSSWALK.md`: three competing decision-ID schemes exist (`DR-*` unresolved, canonical `ADR-001`–`027`, archived `ADR-001`–`017` with collisions) plus two surfaced contradictions (public accounts, FR renumbering).
   - Added `docs/PERMISSIONS_MATRIX.md` (Proposed, `ADR-027`): eight roles, deny-by-default grants, separation of duties, case/intervention status authority, and the four data-model additions Phase 1 needs.
   - Regenerated `docs/PACKAGE_MANIFEST.json` (v1.1) with canonical / governance / supplementary / archive sections and entry points.

---

## 3. What We Are Doing Now

- Pushing the completed docs-only update on `prime` and merging the docs cleanly through `master` and `main` (without deleting any branch).
- Holding before writing `backend/` or `frontend/` application code until review/confirmations are settled.

---

## 4. What Is Left To Be Done

### Step A — Review & Pre-Build Confirmations (Before Writing Code)
- [ ] Review documentation baseline on branch `prime`.
- [ ] Record ADRs in `docs/20_Technical_Decision_Records.md` for confirmed stack decisions already reflected in repo infra (`Python 3.14 + FastAPI`, `PostgreSQL 16 + PostGIS 3.4`, `React + TypeScript`, local dev containers via Podman/Docker Compose).
- [ ] Confirm naming convention boundary (`lower snake_case` DB tables/columns mapped to `camelCase` API/code fields; `UPPER_SNAKE_CASE` constants).
- [ ] Confirm Phase 1 auth/role scope (anonymous + registered contributors vs. staff/admin roles) and local dev interfaces for object storage and auth.
- [ ] Confirm client vs. server image handling rule (uploading untouched originals vs. optional client compression marked as derivative).

### Step B — Backend Phase 1: Core Platform, Intake, Provenance & Case Foundation (`backend/` Modular Monolith)
- [ ] Initialize `backend/` (`pyproject.toml`, FastAPI app skeleton, settings, Ruff/Pytest config matching `.github/workflows/ci.yml` and `Makefile`).
- [ ] PostgreSQL + PostGIS schema and Alembic migrations (11 tables: `users`, `organisations`, `memberships`, `observations`, `observation_versions`, `observation_sources`, `evidence_assets`, `asset_derivatives`, `cases`, `case_observations`, `audit_events`).
- [ ] Identity, RBAC, separation of duties, and anonymous submission boundary.
- [ ] Idempotent Observation intake API (`event_start_at`, `observed_at`, `submitted_at`, `received_at`, precision fields, coordinate/unit validation).
- [ ] Evidence upload pipeline (content-type validation, size limits, server-generated storage keys, checksums, restricted original storage, separate derivative generation).
- [ ] Case management & many-to-many case-observation links (preserving original observations).
- [ ] Immutable/append-only audit logging for consequential actions.
- [ ] Unit, integration, security, and idempotency tests (temporary test records cleaned up after runs; `make lint` and `make test` green).

### Step C — Backend Phase 2: Evidence Correlation, Async Worker & Offline Sync Hardening (ECII)
- [ ] Bounded database-backed worker (`processing_jobs` with `FOR UPDATE SKIP LOCKED` row claiming, retries, bounded concurrency).
- [ ] Bounded PostGIS/temporal/category-aware candidate retrieval (excluding previously rejected relationships).
- [ ] Task-specific correlation scoring (semantic, spatial, temporal, context; missing-signal denominator exclusion; deterministic fallback; `evidence_relationships` with component scores & plain-language reason codes).
- [ ] Source-dependency / duplicate-repost tracking.
- [ ] Reviewer workflow (accept, reject, mark ambiguous; merge/split with audit; no naive transitive clustering).
- [ ] Split-phase offline sync contract hardening (text/coords first, media second) and optional thin `notifications` / WebSocket invalidation.
- [ ] Labelled evaluation harness measuring precision, recall, false links, missed links, and ambiguity.

### Step D — Backend Phase 3: Environmental Intelligence, Prioritisation, Interventions & Verification
- [ ] Dataset catalogue & versioning (`datasets`, `dataset_versions` with licence, attribution, coverage, limitations).
- [ ] Reproducible analysis runs (`analysis_runs`, `analysis_outputs` with CRS, quality masks, seasonality context) and environmental entities/relationships (`environmental_entities`, `environmental_relationships`).
- [ ] Transparent prioritisation factor records (`prioritisation_assessments`) with human rationale.
- [ ] Case assignment, referral records, interventions (`interventions`, `intervention_milestones`), and baseline definitions.
- [ ] Indicator definitions/measurements (`indicator_definitions`, `indicator_measurements`) and `verification_assessments` (separating activity completion, output, outcome, and `"recovery verified"`).
- [ ] Governance export/correction/deletion endpoints (`FR-057`) and approved public summaries (`FR-058`).

### Step E — Frontend PWA & Release Readiness
- [ ] Offline-first PWA queue (IndexedDB, client UUIDs, split-phase text-then-media upload, explicit sync states) and multi-role `frontend/` (React + TypeScript + MapLibre GL JS) following light/clean UI rules.
- [ ] End-to-end, offline, performance, usability, backup/restore, and legal/governance release-gate verification before any live pilot.


---

## 5. Change Log

| Version | Date | Branch / Commit | Summary |
|---|---|---|---|
| 1.0 | 2026-11-17 | pre-repo (`docs/PROJECT_TRACKING.md`) | Initial tracking doc created after reading all documentation folders. |
| 1.1 | 2026-11-17 | `prime` (`e5d5dd6`) | Cloned `Fredprime/EcoWatch`, created `prime` branch, added non-zip docs and tracking doc, pushed to `origin/prime`. |
| 1.2 | 2026-11-17 | `prime` (`ccea786`) | Applied `scripts/protect-branches.sh` on `main`/`master`; added `docs/REVIEW_SUMMARY.md`, `docs/OWNER_RULES.md`, and change log. |
| 1.3 | 2026-11-17 | `prime` (`aa973a9`) | Documented 3-phase backend architecture (`docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md`), added `ADR-026`, updated rules/review/tracking docs (zero code written). |
| 1.4 | 2026-11-17 | `Tazor` | Docs hygiene: agent guide renamed to `docs/AGENT_GUIDE.md`, root `AGENTS.md` added, superseded packages archived, decision-ID crosswalk added, permission matrix proposed (`ADR-027`), package manifest regenerated (v1.1). Zero application code. |
| 1.5 | 2026-11-17 | `Tazor` | Backend plan v1.1: FR/NFR traceability table, `jobs` moved to Phase 1, organisation scoping + five schema additions (`ADR-028`), Phase 2 evaluation acceptance made achievable, missing verification criteria / raster pipeline / prioritisation method named, eight pre-Phase-1 decisions listed. Zero application code. |
| 1.6 | 2026-11-17 | `Tazor` (`e537b8b`) | Opened PR #4 (`prime` -> `master`). Squash-merging PR #2 left `prime` conflicting, so `master` was merged back in: five doc conflicts resolved in favour of `prime` (master's copies were byte-identical to `aa973a9`, so `prime` was a strict superset), then the three duplicate paths the merge resurrected (`EcoWatch Agent Guide.md`, `SignalWeave_Documentation/`, `EcoWatch_Full_Project_Documentation_v0.1/`) were removed. PR is `MERGEABLE`, `mergeStateStatus: BLOCKED` pending owner review, all three CI checks pass. Nothing merged, zero application code. |
| 1.7 | 2026-11-18 | `phase2-correlation` | Phase 2 ownership assigned by the owner (team takes Phases 1 and 3). Built the Phase 2 correlation engine on its own branch: `features.py`, `scoring.py`, `evaluate.py`, 23 tests, `backend/pyproject.toml`. Storage, retrieval SQL, worker job types and review API deliberately not built — they need Phase 1 tables. Documented in `docs/PHASE2_CORRELATION.md`. Zero Phase 1 or Phase 3 code. |
