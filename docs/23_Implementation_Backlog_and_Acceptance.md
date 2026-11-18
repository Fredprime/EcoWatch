# 23 — Implementation Backlog and Acceptance

**Status:** Phase 1 backend code implemented (`backend/`); Phases 2–5 and release readiness remain planned/unimplemented.

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

## 2. Phase 1 — Unified evidence foundation (`backend/` implemented; live DB/lint checks in progress)

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

Backlog:
- Candidate retrieval.
- Semantic baseline model or deterministic fallback.
- Spatial and temporal compatibility signals.
- Source-dependency checks.
- Relationship types and explanations.
- Reviewer accept/reject/ambiguous workflow.
- Merge/split audit behaviour.
- Offline queue and sync states.

Acceptance:
- Labelled evaluation set exists.
- False links and missed links are measured.
- Missing data is not fabricated.
- Suggestions are explainable and reversible.
- Reviewer actions are audited.
- Offline retries are idempotent.

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
