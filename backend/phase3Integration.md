# EcoWatch Phase 3 Integration Contract

**Owner:** Randy
**Date:** 2026-11-18
**Branch:** `feat/Randy_Branch` (merged with latest `origin/master`)
**Scope:** Phase 3 of `BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md` — environmental intelligence, prioritisation, interventions and verification. Documentation `docs/00`–`24` remains the source of truth for behaviour.

## 1. What exists

Application files under `backend/src/ecowatch/modules/`, using the Phase 1 core models, RBAC, audit and database layer:

| Module | Files | Tables |
|---|---|---|
| `catalogue` | `rules.py`, `models.py`, `service.py` | `datasets`, `dataset_versions` |
| `intelligence` | `enums.py`, `rules.py`, `models.py`, `service.py` | `environmental_entities`, `environmental_relationships`, `analysis_runs`, `analysis_outputs` |
| `prioritisation` | `enums.py`, `rules.py`, `models.py`, `service.py` | `prioritisation_assessments` |
| `interventions` | `enums.py`, `rules.py`, `models.py`, `service.py` | `interventions`, `intervention_milestones` |
| `verification` | `enums.py`, `rules.py`, `models.py`, `service.py` | `indicator_definitions`, `indicator_measurements`, `verification_assessments`, `publications` |
| shared | `phase3Contracts.py` | none |
| tests | `backend/tests/unit/phase3/test_phase3Rules.py` | none |
| migration | `backend/alembic/versions/0003_phase3_schema.py` | all 13 tables |
| wiring | `backend/alembic/env.py` imports all Phase 3 models | none |

Not built here (owned by later work): FastAPI routers for Phase 3 endpoints, frontend integration, and any Phase 2 correlation code.

## 2. Naming and type conventions (aligned to Phase 1)

Phase 3 now follows the merged Phase 1 codebase on `origin/prime`:

- Python classes are PascalCase; functions and methods are snake_case; attributes and parameters are camelCase.
- PostgreSQL table and column names are snake_case, declared explicitly on each `mapped_column`.
- Enum classes are PascalCase and enum values are snake_case strings (for example `recovery_verified`, `pending_review`, `no_action`, `less_than`).
- Portable SQLAlchemy types only: `Uuid(as_uuid=True)`, `JSON`, `Numeric`, and `ecowatch.core.spatial.GeographyType` (PostGIS `GEOGRAPHY` on PostgreSQL, `TEXT` WKT on SQLite). No `geoalchemy2`, `JSONB` or PostgreSQL-only UUID type.
- Models inherit `ecowatch.core.models.Base`, `UUIDPrimaryKeyMixin` and, where Phase 1 does, `TimestampMixin` (`created_at`/`updated_at`).

This supersedes the earlier camelCase-only proposal; the integration target is the merged Phase 1 convention.

## 3. Core contract used

Phase 3 imports only these Phase 1 facilities:

1. `ecowatch.core.models.Base`, `UUIDPrimaryKeyMixin`, `TimestampMixin`, `utc_now`.
2. `ecowatch.core.spatial.GeographyType`.
3. Synchronous SQLAlchemy `Session` passed into each service constructor (`ServiceClass(session)`).
4. Existing tables referenced by foreign key: `organisations.id`, `users.id`, `cases.id`, `observations.id`, `units.id`.
5. RBAC: `ecowatch.modules.identity.permissions.Principal`, `Permission`, `Role`, and deny-by-default `ROLE_PERMISSIONS`.
6. Audit: `ecowatch.modules.audit.service.AuditService.record_event(...)`, wrapped by `phase3Contracts.record_event(...)` so Phase 3 events append in the caller's transaction.
7. Errors: `ecowatch.core.errors.DomainError` and `ErrorCode`.

`phase3Contracts.py` provides `require_authenticated_user`, `require_permission`, `require_text`, `require_identifier` and `record_event`.

## 4. Permissions and error codes added to Phase 1

New `Permission` members:

- `CATALOGUE_WRITE`
- `INTELLIGENCE_WRITE`, `INTELLIGENCE_REVIEW`
- `PRIORITISATION_WRITE`
- `INTERVENTION_WRITE`
- `VERIFICATION_WRITE`, `VERIFICATION_APPROVE`
- `PUBLICATION_WRITE`

Granted to the relevant Phase 1 roles (`REVIEWER`, `INVESTIGATOR`, `ENVIRONMENTAL_SPECIALIST`, `INTERVENTION_MANAGER`, `ORGANISATION_ADMIN`, `SYSTEM_ADMIN`); see `identity/permissions.py` for the exact matrix.

New `ErrorCode` members: `PREDICTION_BLOCKED`, `RECOVERY_NOT_VERIFIABLE`.

Permission guard semantics:

- System administrators bypass organisation membership but must still hold the permission.
- A principal with no role in the target organisation receives `404 NOT_FOUND` (`organisationId`) to avoid leaking tenancy.
- A principal with a role but without the permission receives `403 FORBIDDEN`.

## 5. Behaviour enforced in code

- **Catalogue:** a dataset version needs licence, attribution, permitted use, acquisition date, resolution, CRS and method, and coverage start cannot follow coverage end (`FR-016`, `FR-034`). Licence, attribution and permitted use are snapshotted per version.
- **Intelligence:** a relationship needs exactly one source endpoint, exactly one target endpoint, an evidence summary, an uncertainty level and note, alternative explanations and a method/version. An analysis run needs a question, method, version, at least one input dataset version, CRS, parameters and limitations. Outputs must link to a run, are always marked derived, and start `pending_review`. Prediction is blocked unless a model, version, validation report, representative-data reference and target are registered (`FR-035`–`FR-039`).
- **Prioritisation:** factors are a fixed vocabulary; unknown factors are rejected; missing factors are reported, never filled in; a composite rank is refused unless a method reference exists and `rank_is_not_severity` is explicitly true; a human decision needs a user and a rationale (`FR-040`, `FR-041`).
- **Interventions:** status moves through an explicit transition table. Milestone completion can only derive activity status, never an environmental outcome. `recovery_verified` cannot be reached without a verification assessment reference (`FR-042`, `FR-043`).
- **Verification:** every measurement needs a resolved unit, method, version and time. `<`, `>` and `not_detected` require a detection limit; `not_detected` forbids a numeric value. Activity, output, environmental outcome and recovery are ordered and cannot be conflated. Recovery verification refuses to run without an approved criteria version, an environmental-specialist reviewer, baseline and follow-up measurements, comparison method, uncertainty, confounders and seasonal context. Observed-change calculation can return improvement, no improvement, deterioration or inconclusive, never recovery (`FR-043`–`FR-045`, `FR-058`).

## 6. Migration

`backend/alembic/versions/0003_phase3_schema.py`:

- `revision = "0003_phase3_schema"`, `down_revision = "0002_phase2_correlation"`.
- Creates the 13 Phase 3 tables in dependency order with the same foreign keys, unique constraints and indexes as the ORM metadata.
- Adds PostGIS GiST indexes on `datasets.coverage_geometry`, `environmental_entities.geometry` and `interventions.location` only when the active dialect is PostgreSQL.
- `downgrade()` drops Phase 3 tables in reverse order and leaves Phase 1 untouched.

## 7. Decisions still required (do not treat as approved)

1. **`docs/PERMISSIONS_MATRIX.md` (ADR-027) does not exist in this repository.** Phase 3 guards use the eight roles in `docs/05`; endpoint and object-level rules cannot be finalised until that matrix is approved.
2. **Recovery criteria document does not exist.** The code gates `recovery_verified` behind `criteriaApproved=True`; nothing in the product may pass `True` until a criteria document is approved. This keeps the product's central claim honest.
3. **Prioritisation factor vocabulary is proposed, not agreed.** It follows `docs/13` §2. Domain experts must confirm it, and decide whether a composite rank is ever allowed.
4. **Imagery pipeline is undecided.** `analysis_outputs` stores summary plus an optional `storage_key`; no COG/STAC layout, cloud masking method or storage-cost model is committed (`BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md` §3.1).
5. **Phase 3 API surface is not built.** Services are ready, but routers, request/response schemas and endpoint tests are pending.

## 8. Requirement coverage

Implemented as domain rules/services: `FR-016`, `FR-034`–`FR-045`, `FR-058`.
Referenced but not implemented: Phase 3 HTTP endpoints, `FR-055` audit query surface, `FR-053` endpoint RBAC wiring, `FR-057` export/deletion workflows.

## 9. Verification performed

Run from `backend` with a Python 3.13 temp venv and dependencies installed directly (project metadata requires Python >=3.14):

- `ruff check` over all Phase 3 modules, `phase3Contracts.py`, the Phase 3 tests and migration — passed.
- `python -m compileall` over `src`, `alembic` and `tests` — passed.
- `pytest backend/tests/unit/phase3 -q` — 16 passed (rule tests plus SQLite metadata and catalogue-service integration smoke tests).
- `pytest backend/tests -q -m "not postgis"` — 65 passed, 2 deselected (Phase 1 + Phase 2 + Phase 3).
- `alembic history` — confirms `base -> 0001_phase1_initial_schema -> 0002_phase2_correlation -> 0003_phase3_schema (head)`.
- `alembic upgrade head` then `alembic downgrade base` on a temporary SQLite database — both passed, creating and dropping all Phase 1, Phase 2 and Phase 3 tables.
- `alembic check` on the upgraded SQLite database detected no Phase 2 or Phase 3 drift; its only report is the pre-existing Phase 1 index `ix_audit_events_target`, which is unrelated to this branch.

## 10. Next steps

1. Approve or amend §7, especially the permissions matrix and recovery criteria.
2. Add Phase 3 FastAPI routers and endpoint tests once the Phase 3 API surface is agreed.
3. Run the PostgreSQL/PostGIS migration integration test (`-m postgis`) against a live database before merge.
4. Move the temporary `PYTHONPATH=src` test procedure to the project's supported Python version once available.
