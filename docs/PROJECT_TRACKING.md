# EcoWatch Project Tracking

**Version:** 1.6  
**Date:** 2026-11-18  
**Project:** EcoWatch (Merged Project — canonical baseline in `docs/`, incorporating SignalWeave as the Evidence Correlation and Incident Intelligence subsystem)  
**Repository:** `Fredprime/EcoWatch`  
**Working Branch:** `feat/SandyFrontend` for the current frontend/backend integration task. The owner chose merging `master` into the branch (merge commit `290f386`) rather than rebasing; this task-specific instruction overrides the standing `prime` rule in `docs/OWNER_RULES.md` §3 for this task only. `prime` remains the general working branch and `Tazor` held the Phase 2 pgvector work pending PR into `prime`. Never push directly to `main` or `master`.  
**Status:** Phase 1 backend plus Phase 2 evidence correlation (incl. approved pgvector storage and semantic candidate prefilter) implemented in `camelCase` (Python/JSON) mapped to `lower snake_case` PostgreSQL/PostGIS schema; Phase 3 backend modules are present. Ruff clean; `pytest` 110 passed against live PostgreSQL 16 + PostGIS 3.7 + pgvector (worker stopped), 106 passed / 4 skipped without a live DB. Database image is built locally from the root `Dockerfile`. `frontend/` is integrated with the backend for auth, health, observation intake/list, case list/detail/timeline, correlation suggestions/decisions and read-only Administration; the five Phase 3 workspaces are read-only views wired to the ADR-037 reads (pending backend PR #25) and the offline PWA is absent. Nothing is validated, certified or live.

---

## 1. Working Rules and Git Workflow

- **Branching rule:** Work on branch `prime` (branched from `master`), review changes, and push to `prime`. Never commit or push directly to `main` (sacred release branch) or `master` (integration branch receiving reviewed PRs). Do not delete branches after merging unless explicitly asked by the maintainer. For the current task the owner explicitly directed work on `feat/SandyFrontend`, merging `master` into it (merge `290f386`) rather than rebasing; that dated override applies to this task only and is recorded in `docs/OWNER_RULES.md` §7. This standing rule is unchanged.
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

- Finalized Phase 1 (`Core Platform, Intake, Provenance & Case Foundation`) inside `backend/` with `camelCase` Python/JSON naming mapped to `lower snake_case` PostgreSQL/PostGIS columns, Ponytail audit cleanup, Ruff lint clean, and full `pytest` verification (`17 passed` including live PostgreSQL 16 + PostGIS 3.4 Alembic `upgrade`/`downgrade` and `FOR UPDATE SKIP LOCKED` tests).
- Updated repository and architecture documentation (`README.md`, `backend/README.md`, `docs/08_Data_and_Database_Architecture.md`, `docs/22_Change_History_and_References.md`, `docs/23_Implementation_Backlog_and_Acceptance.md`, `docs/PACKAGE_MANIFEST.json`) and synced `prime` with `origin/master` on PR #5 (3/3 CI checks passing).
- **2026-11-19, `backend/remaining-work` (three commits, pending PR into `master`):** finished the remaining backend work after frontend and Phase 3 landed separately (Phase 3 via PRs #9 and #21 — do not redo). `c7218a7` FR-057 governance export + `obs:hide` tombstone (`ADR-034`); `c8bd4cc` ADR-031 case-side actions with authority clarified by `ADR-035`; `67e9c38` ADR-036 Phase 2 contract hardening (error taxonomy, `Retry-After`, idempotent media upload, migration `0006`, split-phase contract docs). Verification: ruff clean, single head `0006` with valid upgrade/downgrade SQL, `pytest backend -q` → 123 passed / 4 skipped. See `docs/REVIEW_SUMMARY.md` §3 item 6 for owner decision points.

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
- [x] Unit, integration, security, and live PostgreSQL/PostGIS tests passing (`17 passed` with `ECOWATCH_RUN_POSTGIS_TESTS=1` against `ecowatch-db`, plus `CI/backend / lint + test` green on PR #5).

### Step C — Backend Phase 2: Evidence Correlation, Async Worker & Offline Sync Hardening (ECII)
- [x] Bounded database-backed worker (`processing_jobs` with `FOR UPDATE SKIP LOCKED` row claiming, retries, bounded concurrency) — built in Phases 1/2.
- [x] Bounded PostGIS/temporal/category-aware candidate retrieval (excluding previously rejected relationships) — built on `phase2-correlation`.
- [x] Task-specific correlation scoring (semantic, spatial, temporal, context; missing-signal denominator exclusion; deterministic fallback; `evidence_relationships` with component scores & plain-language reason codes) — built, with pgvector path added in PR #19.
- [x] Source-dependency / duplicate-repost tracking — built on `phase2-correlation`.
- [x] Reviewer workflow (accept, reject, mark ambiguous; no naive transitive clustering) — built on `phase2-correlation`.
- [x] Case-side `promote_from_cluster` / `merge` / `split` / `cross_case` with IV/OA/SA authority, org-scoping, self-review guard and audit (`ADR-031` + `ADR-035`, 2026-11-19).
- [x] Split-phase offline sync contract hardening: permanent/transient error category, `Retry-After`, idempotent media re-upload (`ADR-036`, 2026-11-19). WebSocket invalidation and server-side observation sync-state column explicitly deferred — client queueing belongs to the frontend PWA.
- [x] Smoke-test-only evaluation harness wiring (no accuracy claim; real labelled set does not exist).

### Step D — Backend Phase 3: Environmental Intelligence, Prioritisation, Interventions & Verification
Phase 3 was completed by a teammate on separate branches and merged via PR #9 (`c3aafd4`) and PR #21 (`3a13520`); it is **not** part of the `backend/remaining-work` PR and must not be redone.
- [x] Dataset catalogue & versioning (`datasets`, `dataset_versions` with licence, attribution, coverage, limitations).
- [x] Reproducible analysis runs (`analysis_runs`, `analysis_outputs` with CRS, quality masks, seasonality context) and environmental entities/relationships (`environmental_entities`, `environmental_relationships`).
- [x] Transparent prioritisation factor records (`prioritisation_assessments`) with human rationale.
- [x] Case assignment, referral records, interventions (`interventions`, `intervention_milestones`), and baseline definitions.
- [x] Indicator definitions/measurements (`indicator_definitions`, `indicator_measurements`) and `verification_assessments` (separating activity completion, output, outcome, and `"recovery verified"`).
- [x] Governance export/hide (`FR-057`, completed on `backend/remaining-work` under `ADR-034`) and approved public summaries (`FR-058`, already present).

### Step E — Frontend PWA & Release Readiness
- [x] Multi-role `frontend/` shell (React + TypeScript + Vite, router-based workspace navigation) following the light/clean UI rules.
- [x] Core read + intake integration with the backend: auth (`login`, `auth/me`), health, observations (intake + list), cases (list/detail/timeline) and correlation suggestions with human decisions. Hand-written typed DTOs and a single `fetch` wrapper (no React Query/Axios/Zod); memory-only bearer token (reload requires signing in again; 401 clears auth); same-origin Vite dev proxy to `127.0.0.1:8000` with no backend CORS middleware added.
- [x] Removal of fake receipts, queued-local/demo state, hardcoded example observations/cases/suggestions and example monitoring/prioritisation rows; no seeded/sample/demo data remains in product source.
- [ ] Offline-first PWA queue (IndexedDB, client UUIDs, split-phase text-then-media upload, explicit sync states). Not implemented.
- [x] MapLibre GL JS rendering (ADR-038): a shared lazy-loaded map component draws stored WKT geometry from the ADR-037 read APIs on a local blank style — no basemap, tile service, API key or external request. Analysis (entity geometry), Monitoring (dataset coverage) and Interventions (location) get maps; Prioritisation and Verification expose no geometry and show an explicit no-spatial-data notice with their list views intact. Public case detail stays restricted. `npm run lint`/`build` pass and the WKT parser passed a Node self-check over all supported forms plus malformed/out-of-bounds input; no real-device or basemap verification. Tile provider and projected CRS remain owner decisions.
- [ ] End-to-end, offline, performance, usability, backup/restore, and legal/governance release-gate verification before any live pilot. Manual end-to-end checks through the Vite proxy covered the integrated read/intake flows and auth/permission errors; this is not release-gate sign-off.


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
| 1.9 | 2026-11-18 | `prime` (`3713211`–`bbdc5be`) | Implemented full Phase 1 backend (`backend/`) in `camelCase` mapped to `lower snake_case` DB columns, ran Ponytail audit, recorded `ADR-029`, synced `origin/master` into `prime` on PR #5, fixed CI Ruff lint checks (`3/3` CI checks green). |
| 1.10 | 2026-11-18 | `prime` | Verified live PostgreSQL 16 + PostGIS 3.4 container (`ecowatch-db`), Alembic `upgrade`/`downgrade`/`SKIP LOCKED` (`17 passed` total), and updated `README.md`, `backend/README.md`, `docs/08`, `docs/22`, `docs/23`, and `docs/PACKAGE_MANIFEST.json`. |
| 2.0 | 2026-11-18 | `phase2-correlation` | Phase 2 started on its own branch. Correlation scoring engine + evaluation harness built before Phase 1 existed (23 tests), then moved to `ecowatch/modules/correlation/` to match Phase 1's layout. Phase 1 (`3713211`) merged in: `pyproject.toml` and `ecowatch/__init__.py` conceded to Phase 1, change-log rows re-appended rather than overwriting Phase 1's. |
| 2.1 | 2026-11-18 | `phase2-correlation` | Implemented the Phase 2 correlation slice on the real Phase 1 schema: `evidence_relationships` migration `0002` (canonical-pair CHECK + UNIQUE per pair/task), `observations.source_ref` because `FR-027` was unimplementable without it, bounded org-scoped retrieval, `CorrelationService` scan + decide, worker job type `correlation.scan`, three API endpoints, `correlation:read`/`correlation:review` permissions. 49 passed / 2 skipped by default, plus 2 PostGIS-gated tests verified against live PostgreSQL. Fixed `prime`'s failing lint (159 errors) so CI can gate anything. |
| 2.2 | 2026-11-18 | `phase2-correlation` | Merged `origin/prime` (`3f1e6df`): kept prime's docs-alignment rows and re-appended the Phase 2 rows rather than overwriting. CI: the backend job now starts a `postgis/postgis:16-3.4` service and runs the migration tests (`ECOWATCH_RUN_POSTGIS_TESTS=1`), so the Alembic chain executes on every PR instead of skipping — `51 passed` in CI, `49 passed / 2 skipped` without a database. Merging also caught a wrong TOML merge resolution that CI failed in 9 seconds, which is the check doing its job. |
| 2.3 | 2026-11-18 | `phase2-correlation` | Phase 2 capability pass, one piece per commit: per-category retrieval policy with a tighter window when a report has no location (`policy.py`); `ST_DWithin` on geography so distance uses the Phase 1 GiST index (the PostGIS test caught a lat/lon swap that silently filtered out every neighbour); detector differentiation `source_dependency` > `duplicate` > `same_event` with a review threshold, so the queue stops being every pair with any shared signal; `POST /suggestions/{id}/reopen` with a required reason, making a decision reversible by a named action while the row keeps current state and audit keeps history; `correlation_clusters` + members (migration `0003`) with one cluster per report so A~B and B~C never become a cluster of three, plus a persisted `ambiguous` tie flag. 70 passed / 3 skipped, 73 with PostGIS. |
| 2.4 | 2026-11-18 | `phase2-intake-hook` | Observation intake now queues `correlation.scan` in the same transaction as the submission, so new reports are actually scanned without a manual API call. An idempotent replay queues no second job; the worker turns the queued job into a provisional staff-only cluster. One Phase 1 workflow test was updated to assert on the evidence job it cares about rather than the total number of pending jobs. 72 passed / 3 skipped. |
| 2.5 | 2026-11-18 | `prime` | Merged PR #11 (`eab2a23`) and PR #12 (`beae5b7`) into `prime`: one-row-per-pair reclassification and the self-review rule on `reopen`, then automatic `correlation.scan` enqueue on observation intake. Final combined tree: ruff clean, 75 passed / 3 skipped, 78 with PostGIS; CI 3/3 green on both PRs. |
| 2.6 | 2026-11-18 | `prime` | Fixed PR #14's backend CI failure: synced `master` (`c3aafd4`) into `prime`, then added no-op Alembic merge revision `0004_merge_phase2_phase3` to join the sibling `0003_phase2_clusters` and `0003_phase3_schema` heads. One head now; ruff clean, 94 passed with PostGIS, 91 passed / 3 skipped without. |
| 2.7 | 2026-11-18 | `docs/phase2-decisions` | Recorded the owner's four Phase 2 decisions: pgvector approved (`ADR-030`), smoke-test-only evaluation, case-side actions owned by the cases module (`ADR-031`), and re-scan on corrections plus evidence uploads. Updated `PHASE2_TODO.md`, `PHASE2_CORRELATION.md`, `REVIEW_SUMMARY.md` and the ADR register. |
| 2.8 | 2026-11-18 | `feat/correlation-rescan-triggers` | Implemented the approved re-scan triggers: observation corrections and evidence uploads enqueue `correlation.scan` in the same transaction as the change. Added two integration tests. Ruff clean; 96 passed with PostGIS, 93 passed / 3 skipped without. |
| 2.9 | 2026-11-18 | `test/correlation-evaluation-smoke` | Ran the evaluation harness under the owner's smoke-test-only route with temporary synthetic fixtures. Counts assert scoring-to-evaluation wiring only; no accuracy claim. Ruff clean; 97 passed with PostGIS, 94 passed / 3 skipped without. |
| 2.10 | 2026-11-18 | `Tazor` | Implemented ADR-030 pgvector support: migration `0005_phase2_embeddings` (`correlation_embeddings` with `vector(384)`, HNSW cosine index on PostgreSQL, JSON fallback on SQLite, unique per observation/model/input hash, skip-on-unchanged); deterministic hashed-word vectors (`hashed-words-v1`, not a semantic model — ADR-019 open, no accuracy claim); `semantic_similarity` uses vector cosine with `token_similarity` fallback; nearest-vector query narrows the org/time/space candidate set. Combined DB image from new root `Dockerfile` (pgvector base + PostGIS 3.7); compose and both CI DB jobs use it and prove both extensions. Ruff clean; 106 passed with live PostgreSQL, 102 passed / 4 skipped without. |
| 2.11 | 2026-11-18 | `feat/SandyFrontend` (merge `290f386`) | Owner chose merging `master` into the branch rather than rebasing (task-specific override of the standing `prime` rule, recorded in `OWNER_RULES.md` §7). Frontend integrated with the backend for auth, health, observation intake/list, case list/detail/timeline and correlation suggestions/decisions via hand-written typed DTOs, a single `fetch` wrapper, a memory-only bearer token and a same-origin Vite dev proxy (no CORS middleware added). Fake receipts, queued/demo state and example rows removed. Vite 6.2.7 -> 6.4.6 via lockfile only; `npm audit` 0; no new runtime dependencies. Security: DB-backed login rate limiting (5 attempts / 300 s window, 900 s lockout, SHA-256 email+IP bucket key), public DTO no longer exposes `originalLocationWording`, production rejects `debug=true`, worker-startup regression test. Logout/401 clearing client-only; stateless token not server-revocable (deferred). Frontend lint/build clean; backend Ruff clean; pytest 106 passed / 4 skipped without DB, 110 passed with live DB and worker stopped. |
| 2.12 | 2026-11-19 | `master` (PRs #9/#19/#20/#21) | Remote state audit confirmed Phase 3 merged via PR #9 (`c3aafd4`) and PR #21 (`3a13520`), pgvector via #19, frontend via #20, and earlier Phase 2 PRs #10/#11/#12/#17/#18. Frontend work on `Tazor` was merged from `origin/master`, conflicts resolved, slim toggle / centred sign-in button / read-only Administration docs verified; lint and build clean. These streams are complete and must not be redone. |
| 2.13 | 2026-11-19 | `backend/remaining-work` (`c7218a7`, `c8bd4cc`, `67e9c38`) | Remaining backend work. ADR-034/035/036 recorded before code. FR-057 governance export + `obs:hide` tombstone (hide from all views, clear isolated source PII, audit; originals preserved); ADR-031 case-side `promote_from_cluster`/`merge`/`split`/`cross_case` with ADR-035 single-actor IV/OA/SA authority, cross-org 404, self-review guard, same-transaction audit; ADR-036 Phase 2 contract hardening (error category, `Retry-After`, `Idempotency-Key` media replay via migration `0006`, split-phase contract docs). Verified: ruff clean, single head `0006`, upgrade/downgrade SQL valid, 123 passed / 4 skipped. Pending PR into `master`. |
| 2.14 | 2026-11-19 | `feat/phase3-read-apis` (`d01b3d9`, PR #25 merged `eada1d1`) | ADR-037 recorded before code, then 13 org-scoped, cursor-paginated GET/list endpoints added across the five Phase 3 modules, with a shared `phase3Reads` helper, existing response DTOs in `CursorPage`, and each module's WRITE permission as the read gate. System admins see all organisations; other principals only their permitted organisations; cross-org filters 403, out-of-scope child parents 404. No migration, permission or dependency change. Five new integration tests seed temporary records through the POST APIs. Verified: ruff clean, single head `0006`, 128 passed / 4 skipped, `git diff --check` clean. |
| 2.15 | 2026-11-19 | `feat/phase3-shell-wiring` (PR #26, pending) | Wired the five Phase 3 staff shells (Analysis, Monitoring, Prioritisation, Interventions, Verification) to the ADR-037 org-scoped read APIs from backend PR #25 (merged). Typed DTOs for all Phase 3 response shapes plus 13 typed list helpers in `src/api/phase3.ts`; read-only first-page tables via a shared `ReadOnlyListCard`/`RecordPicker` and the existing `useApiResource`/`ResourceState`/`SignInPrompt`/`EmptyState` pattern. Parent selectors load analysis outputs by run, dataset versions by dataset and intervention milestones by intervention. Removed disabled "pending backend" buttons; map area remains a labelled placeholder. No writes, fabricated rows or fake queues; permissions/scope stay server-side. Verified: `npm run lint` clean, `npm run build` passes (86 modules), `git diff --check` clean. Frontend has no test harness. |
