# 23 — Implementation Backlog and Acceptance

**Status:** Phase 1 backend code implemented (`backend/`); a Phase 2 correlation slice and Phase 3 backend modules are present. `frontend/` has core backend read/intake integration; the remaining workspaces, offline PWA and release readiness remain planned/unimplemented.

**Frontend slice (2026-11-18):** auth (`login`, `auth/me`), health, observation intake and list, case list/detail/timeline, and correlation suggestions with human decisions use hand-written typed DTOs, one `fetch` wrapper and a memory-only bearer token (reload requires signing in again; 401 clears auth) through a same-origin Vite dev proxy to `127.0.0.1:8000` (no backend CORS middleware). Analysis, Monitoring, Prioritisation, Interventions, Verification and Administration remain shells without API integration; no fake receipts, queued/demo state or example rows remain in product source. Logout and 401 clearing are client-only: the stateless HMAC token is not server-side revocable and stays valid until expiry (default 12h), although deactivated users are rejected on every request; immediate revocation is deferred. A correlation score is a ranking signal only; `token_similarity` is the labelled fallback, not a validated semantic model.

## 1. Before coding: pilot definition

Deliverables:
- Pilot geography and boundary.
- One primary environmental use case.
- Initial users and stakeholder map.
- Selected indicators and methods.
- Data source and permission register.
- Review and referral pathway.
- Safety, privacy and retention decisions.
- Pilot success measures.

Acceptance: environmental specialist and project owner review the problem, indicators, source suitability and limits. The pilot is bounded and operationally credible.

## 2. Phase 1 — Unified evidence foundation (`backend/` implemented; verification recorded in `docs/REVIEW_SUMMARY.md`)

Backlog:
- [x] Repository and development environment (`backend/pyproject.toml`, `compose.yaml`, `Makefile`).
- [x] PostgreSQL + PostGIS schema and Alembic migrations (`0001_phase1_initial_schema.py`, 17 Phase 1 tables).
- [x] Identity/roles (`PERMISSIONS_MATRIX.md`) and anonymous submission boundary.
- [x] Observation intake API, idempotency keys, `observation_sources` isolation, `methods`/`units`, and immutable `observation_versions`.
- [x] Evidence upload pipeline, untouched original storage, scan/quarantine, and EXIF-stripped derivatives (`processing_jobs` worker).
- [x] Provenance and four separated timestamps (`event_start_at`, `observed_at`, `submitted_at`, `received_at`) + location/time precision.
- [x] Case creation, many-to-many case-observation links, lifecycle transitions, two-key `field_verified` approval, timelines, and approved public summaries.
- [x] Append-only `audit_events` and temporary-record test isolation (zero seeded demo data).

Acceptance:
- Valid observations can be submitted and retrieved.
- Duplicate retries create one record.
- Original evidence is preserved and access-controlled.
- Time/location precision is represented accurately.
- Case links do not overwrite observations.
- Role checks are enforced server-side.

## 3. Phase 2 — Evidence correlation

**Status (2026-11-18):** implemented on `phase2-correlation` — category-aware bounded retrieval with `ST_DWithin` on PostgreSQL, scoring with missing-signal handling, `evidence_relationships` with canonical-pair constraints and a persisted tie flag, detector differentiation (`source_dependency`, `duplicate`, `same_event`), reviewer accept/reject/ambiguous/reopen with audit, provisional clusters, and background scanning. Not built: a validated semantic model (pgvector hashed-word vectors only narrow the candidate set and `token_similarity` remains the labelled fallback), `cross_case`, promote/merge/split, and the scored evaluation run. Per-item status: `docs/PHASE2_TODO.md`; what exists and its limits: `docs/PHASE2_CORRELATION.md`.

Backlog:
- Candidate retrieval. — *built, distance filtered in Python rather than `ST_DWithin` (upgrade tracked as T4b)*
- Semantic baseline model or deterministic fallback. — *deterministic `token_similarity` fallback built; pgvector hashed-word vectors narrow the candidate set (ADR-030); no validated semantic model*
- Spatial and temporal compatibility signals. — *built*
- Source-dependency checks. — *built for explicitly recorded `source_ref`; no inference of shared origin*
- Relationship types and explanations. — *`same_event` only; duplicate / repost / cross-case not differentiated yet*
- Reviewer accept/reject/ambiguous workflow. — *built, audited; reversal is a separate `reopen` action with a required reason*
- Merge/split audit behaviour. — *not built; the cluster container they need exists*
- Offline queue and sync states. — *not built (intake side, Phase 1 module)*

Acceptance:
- Labelled evaluation set exists. — *not yet; harness and metrics exist, the run is gated on the evaluation-route decision*
- False links and missed links are measured. — *metrics implemented, no result claimed*
- Missing data is not fabricated. — *enforced: a missing signal leaves the score, it is not imputed*
- Suggestions are explainable and reversible. — *explainable (components, missing signals, reasons, task wording); reversible by `reopen` with a reason, audited*
- Reviewer actions are audited. — *enforced in the same transaction as the decision*
- Offline retries are idempotent. — *not applicable yet, intake is Phase 1*

## 4. Phase 3 — Environmental intelligence

Backlog:
- Dataset catalogue and versioning.
- One selected environmental analysis.
- Reproducible input/method/parameter record.
- Spatial and temporal quality checks.
- Historical comparison and map output.
- Expert interpretation and limitation record.

Acceptance:
- Analysis can be reproduced.
- Source data and method are traceable.
- Seasonal and quality limitations are visible.
- Output is not presented as proof of cause.

## 5. Phase 4 — Prioritisation and intervention

Backlog:
- Prioritisation factors.
- Human decision and rationale.
- Case assignment/referral.
- Intervention records and milestones.
- Baseline and intended outcome fields.

Acceptance:
- Priority rationale is transparent.
- Authority and owner are recorded.
- Activity completion is separate from environmental outcome.

## 6. Phase 5 — Verification and advanced intelligence

Backlog:
- Follow-up indicator collection.
- Outcome comparison.
- Reference/comparison site support where appropriate.
- Recovery status and review.
- Predictive modelling feasibility assessment.

Acceptance:
- Baseline and follow-up methods are comparable.
- Uncertainty and confounding factors are documented.
- “Recovery verified” requires approved criteria and qualified review.
- Predictive features are not released without representative data and validation.

## 7. Release readiness

Before a live pilot: privacy and legal review, source permissions, role matrix, upload security, tested backups, monitoring, support ownership, user guidance, incident response and acceptance sign-off.
