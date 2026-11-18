# EcoWatch Project Tracking

**Version:** 1.4  
**Date:** 2026-11-18  
**Project:** EcoWatch (Merged Project — canonical baseline in `docs/`, incorporating SignalWeave as the Evidence Correlation and Incident Intelligence subsystem)  
**Repository:** `Fredprime/EcoWatch`  
**Working Branch:** `prime` (branched from `master`; never push directly to `main` or `master`)  
**Status:** Phase 1 backend (`EcoWatch/backend/`) implemented in `camelCase` (Python/JSON) mapped to `lower snake_case` PostgreSQL/PostGIS schema, Ponytail-audited, and verified with `pytest` (`16 passed, 1 skipped`) + `compileall`; pending `ruff` lint, `python-multipart` install, and live PostGIS migration verification.

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

- Finalized Phase 1 (`Core Platform, Intake, Provenance & Case Foundation`) inside `backend/` with `camelCase` Python/JSON naming mapped to `lower snake_case` PostgreSQL/PostGIS columns, Ponytail audit cleanup, and unit/integration/security tests (`16 passed, 1 skipped`).
- Next for owner review & environment setup: install `backend[dev]` (`ruff`, `python-multipart`) and run `make up`, `alembic upgrade head`, `ECOWATCH_RUN_POSTGIS_TESTS=1 pytest -m postgis`, and `make lint`.

---

## 4. What Is Left To Be Done

### Step A — Review & Pre-Build Confirmations
- [x] Document baseline architecture, permissions matrix, and schema additions on branch `prime` (`ADR-026`, `ADR-027`, `ADR-028`).
- [x] Record `ADR-029` approving Phase 1 backend build with `camelCase` Python/JSON <-> `lower snake_case` SQL boundary and native stdlib/SQLAlchemy stack.
- [ ] Complete formal team sign-off of `ADR-014`–`ADR-016` and `ADR-026`–`ADR-028` statuses in `docs/20_Technical_Decision_Records.md` / `docs/08` during PR review.

### Step B — Backend Phase 1: Core Platform, Intake, Provenance & Case Foundation (`backend/` Modular Monolith)
- [x] Initialize `backend/` (`pyproject.toml`, FastAPI app skeleton with 34 API routes, stdlib/env settings, Ruff/Pytest config matching `.github/workflows/ci.yml` and `Makefile`).
- [x] PostgreSQL + PostGIS schema and Alembic initial migration (`0001_phase1_initial_schema.py` covering all 17 Phase 1 tables with GiST spatial indexes and Variant SQLite support for unit/integration tests).
- [x] Identity, 8-role deny-by-default RBAC (`PERMISSIONS_MATRIX.md`), separation of duties, cross-organisation `404` isolation, and anonymous tracking-code lockout.
- [x] Idempotent Observation intake API (`event_start_at`, `observed_at`, `submitted_at`, `received_at`, precision fields, coordinate/unit/method validation, immutable versions & `observation_sources` isolation).
- [x] Evidence upload pipeline, background job worker (`processing_jobs` with `FOR UPDATE SKIP LOCKED` on PostgreSQL), content/magic-byte validation, size limits, server-generated storage keys, SHA-256 checksums, restricted original storage, and EXIF-stripped derivatives.
- [x] Case management, many-to-many case-observation links, two-key `field_verified` approval (`ES` + `OA`), unified timeline, and governed public case summaries.
- [x] Immutable/append-only `audit_events` logging for consequential actions and reads.
- [x] Unit, integration, and security test suite implemented and passing in-memory (`16 passed`, `1` PostGIS test skipped pending DB container).
- [ ] Owner/CI environment verification: install `python-multipart` + `ruff`, start PostgreSQL/PostGIS (`make up`), run `alembic upgrade head`, run `ECOWATCH_RUN_POSTGIS_TESTS=1 pytest -m postgis`, and verify `make lint`.

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
| 1.7 | 2026-11-18 | `prime` (`cd1c74b`) | Added `docs/GLOBAL_AGENT_RULES_MERGED.md` and pushed only that file to `origin/prime`. |
| 1.8 | 2026-11-18 | `prime` (`068070f`) | Removed `RULES_COMPARISON_AND_MERGE_REPORT.md` from repo and local `docs/`, updated `PACKAGE_MANIFEST.json`, `REVIEW_SUMMARY.md`, and `PROJECT_TRACKING.md`. |
| 1.9 | 2026-11-18 | `prime` | Implemented full Phase 1 backend (`backend/`) in `camelCase` mapped to `lower snake_case` DB columns, ran Ponytail audit (dropped `pydantic-settings`/`geoalchemy2`/`shapely` in favor of native stdlib/SQLAlchemy, extracted shared `paginate_descending`), recorded `ADR-029`, and verified `pytest` (`16 passed, 1 skipped`) + `compileall`. |
| 2.0 | 2026-11-18 | `phase2-correlation` | Phase 2 started on its own branch. Correlation scoring engine + evaluation harness built before Phase 1 existed (23 tests), then moved to `ecowatch/modules/correlation/` to match Phase 1's layout. Phase 1 (`3713211`) merged in: `pyproject.toml` and `ecowatch/__init__.py` conceded to Phase 1, change-log rows re-appended rather than overwriting Phase 1's. |
| 2.1 | 2026-11-18 | `phase2-correlation` | Implemented the Phase 2 correlation slice on the real Phase 1 schema: `evidence_relationships` migration `0002` (canonical-pair CHECK + UNIQUE per pair/task), `observations.source_ref` because `FR-027` was unimplementable without it, bounded org-scoped retrieval, `CorrelationService` scan + decide, worker job type `correlation.scan`, three API endpoints, `correlation:read`/`correlation:review` permissions. 49 passed / 2 skipped by default, plus 2 PostGIS-gated tests verified against live PostgreSQL. Fixed `prime`'s failing lint (159 errors) so CI can gate anything. |
