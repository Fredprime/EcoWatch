# EcoWatch Backend Architecture and Three-Phase Implementation Plan

**Version:** 1.0  
**Date:** 2026-11-17  
**Status:** Proposed architecture blueprint (zero application code written yet)  
**Target Directory:** `backend/` (Python 3.14, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL 16 + PostGIS 3.4)

---

## 1. Purpose and Architectural Principles

This document translates EcoWatch's merged baseline (`docs/00`–`24`, `docs/files/22_Correlation_Engine_and_Offline_Collection.md`, `docs/EcoWatch Agent Guide.md`) and repository infrastructure (`compose.yaml`, `Makefile`, `.github/workflows/ci.yml`, `CONTRIBUTING.md`) into a concrete, **three-phase backend architecture**.

### Core Architectural Decisions
1. **Modular Monolith First (`ADR-013`, `docs/07`):** One deployable FastAPI service (`backend/`) backed by one PostgreSQL 16 + PostGIS 3.4 database (`compose.yaml`). Domain modules communicate via explicit service/interface calls inside one process and share ACID transactions without premature microservices, Redis, Kafka, or Kubernetes.
2. **Database-Backed Asynchronous Processing (`docs/07` §4, `docs/files/22` §13):** Slow or heavy tasks (media scanning/derivatives, ECII semantic embeddings and correlation, dataset imports, spatial/raster analysis) execute asynchronously via a `processing_jobs` table (`FOR UPDATE SKIP LOCKED` row claiming) in a bounded in-app worker loop. API intake returns durable receipt immediately (`NFR-001`).
3. **Provider Interfaces for Open Choices (`docs/18`, `docs/EcoWatch Agent Guide.md` §7):** Authentication/identity verification and object storage (evidence originals and derivatives) sit behind narrow Python protocols/interfaces so local development (local disk + local token/session auth) swaps cleanly to chosen cloud/object-storage/IdP providers later.
4. **Naming and Data Boundary (`docs/EcoWatch Agent Guide.md` §8):**
   - PostgreSQL tables and columns: `lower snake_case`.
   - Python variables/attributes, configuration keys, and JSON API request/response payloads: `camelCase` (mapped cleanly at the Pydantic schema boundary).
   - Python classes/types: `PascalCase`; constants: `UPPER_SNAKE_CASE`.
5. **Non-Negotiable Safety & Scientific Integrity Guardrails (`docs/EcoWatch Agent Guide.md` §5, `CONTRIBUTING.md` §7):**
   - Observations, evidence assets, and cases remain separate records; one observation can link to multiple cases (`case_observations`).
   - Four timestamps (`event_start_at`, `observed_at`, `submitted_at`, `received_at`) are stored separately with explicit precision; missing values are never fabricated.
   - Original uploaded evidence files are preserved untouched under restricted access; EXIF-stripped previews and analysis outputs are stored separately (`asset_derivatives`).
   - Contributor identity/contact (`observation_sources`) is isolated from observation records and public views.
   - Automated correlation scores are ranking signals only (never probabilities, severity, or causation); `"field verified"` and `"recovery verified"` are set only by authorised humans; `activity completed != environmental outcome != recovery verified`.
   - Zero seeded, sample, or demo data in the codebase; tests create temporary records and clean them up.

---

## 2. Logical Architecture and Module Layout

All 11 modules from `docs/07_System_Architecture.md` §3 live under `backend/src/ecowatch/` with strict dependency direction (`api -> modules -> core/db`, never bypassing module service boundaries to mutate another module's private tables directly).

```text
Clients (Public / Field PWA / Staff & Specialist Web UI)
                         |
              REST API (/api/v1) + Optional WS Notifications
                         |
+-------------------------------------------------------------------+
|               FastAPI Modular Monolith (backend/)                 |
|                                                                   |
|  core/        config, db/PostGIS session, errors, storage port,   |
|               auth port, pagination, camelCase boundary schemas   |
|                                                                   |
|  Modules (Phase 1):                                               |
|    - identity        (users, organisations, memberships, RBAC)    |
|    - collection      (intake validation, idempotency, rate limit) |
|    - observations    (observations, versions, isolated sources)   |
|    - evidence        (assets, checksums, originals, derivatives)  |
|    - cases           (cases, case_observations, referrals)        |
|    - audit           (append-only audit_events)                   |
|                                                                   |
|  Modules (Phase 2 — ECII & Async Engine):                         |
|    - jobs            (processing_jobs worker, SKIP LOCKED loop)   |
|    - correlation     (candidate search, scoring, explainability,  |
|                       provisional clusters, review/merge/split)   |
|    - notifications   (notifications table, thin WS broadcaster)   |
|                                                                   |
|  Modules (Phase 3 — Intelligence, Prioritisation & Verification): |
|    - catalogue       (datasets, dataset_versions, data rights)    |
|    - intelligence    (environmental_entities, relationships,      |
|                       analysis_runs, analysis_outputs)            |
|    - prioritisation  (prioritisation_assessments, factor views)   |
|    - interventions   (interventions, milestones, baselines)       |
|    - verification    (indicator_definitions, measurements,        |
|                       verification_assessments, public summaries) |
+-------------------------------------------------------------------+
          |                                      |
PostgreSQL 16 + PostGIS 3.4              Object Storage Interface
(26 logical tables, Alembic)             (Restricted originals vs.
                                          derivatives / previews)
```

### Target Directory Structure (`backend/`)

Aligned with `Makefile` (`ruff check backend`, `pytest backend`) and `.github/workflows/ci.yml` (`pip install -e "backend[dev]"`):

```text
backend/
  pyproject.toml                 # Python >=3.14, deps, ruff & pytest config
  alembic.ini
  alembic/
    env.py
    versions/
  src/
    ecowatch/
      main.py                    # FastAPI app factory, lifespan, router mount
      core/                      # Config, DB engine/pooling, security, storage, audit helpers
      modules/
        identity/                # Auth boundary, roles, organisations, memberships
        collection/              # Public/field intake endpoints, idempotency, payload validation
        observations/            # Observation domain, versions, isolated observation_sources
        evidence/                # Evidence assets, derivatives, checksums, restricted downloads
        cases/                   # Case lifecycle, many-to-many links, investigation records
        audit/                   # Immutable audit_events service
        jobs/                    # Phase 2: DB-backed worker & retry scheduler
        correlation/             # Phase 2: ECII engine, clusters, review workflow, evaluation
        notifications/           # Phase 2: Staff notifications + thin WebSocket invalidation
        catalogue/               # Phase 3: Datasets, versions, licences, provenance
        intelligence/            # Phase 3: Geospatial/environmental analysis & pathways
        prioritisation/          # Phase 3: Multi-factor decision support records
        interventions/           # Phase 3: Interventions & milestones
        verification/            # Phase 3: Indicators, measurements, recovery verification
  tests/
    unit/
    integration/
    security/
    evaluation/                  # Phase 2: Correlation precision/recall/ambiguity harness
```

---

## 3. Three-Phase Backend Breakdown

### Summary Matrix

| Backend Phase | Roadmap Alignment | Core Goal | Logical Tables (`docs/08`) | Primary Modules |
|---|---|---|---|---|
| **Phase 1** | Roadmap Phase 1 | Durable, idempotent evidence collection, provenance preservation, RBAC, and case foundation | 11 tables (`users`, `organisations`, `memberships`, `observations`, `observation_versions`, `observation_sources`, `evidence_assets`, `asset_derivatives`, `cases`, `case_observations`, `audit_events`) | `core`, `identity`, `collection`, `observations`, `evidence`, `cases`, `audit` |
| **Phase 2** | Roadmap Phase 2 | Explainable ECII evidence correlation, bounded async worker, human review, and offline sync hardening | +3 tables (`evidence_relationships`, `processing_jobs`, `notifications`) | `jobs`, `correlation`, `notifications` (+ `evidence` async scan, `collection` split-phase sync) |
| **Phase 3** | Roadmap Phases 3, 4, 5 | Permissioned environmental datasets, geospatial/environmental analysis, prioritisation, interventions, and verified recovery | +12 tables (`datasets`, `dataset_versions`, `environmental_entities`, `environmental_relationships`, `analysis_runs`, `analysis_outputs`, `prioritisation_assessments`, `interventions`, `intervention_milestones`, `indicator_definitions`, `indicator_measurements`, `verification_assessments`) | `catalogue`, `intelligence`, `prioritisation`, `interventions`, `verification` |

*Total across all three phases: 26/26 logical tables (`docs/08`), 58/58 functional requirements (`FR-001`–`FR-058`), 10/10 non-functional requirements (`NFR-001`–`NFR-010`), and 11/11 logical modules (`docs/07`).*

---

### Phase 1 — Core Platform, Intake, Provenance & Case Foundation

**Objective:** Establish a reliable, security-hardened API and database foundation where observations and media are captured idempotently with full provenance, contributor identity is isolated, and authorised staff can manage cases.

#### 1.1 Modules & Responsibilities
- **`core`:** Environment config (`.env`), SQLAlchemy async/sync engine with connection pooling, PostGIS geometry/geography helpers (`SRID 4326` storage with explicit CRS metadata), `camelCase` <-> `snake_case` Pydantic base schema, structured non-leaking error responses, bounded pagination, and `StorageProvider` / `AuthProvider` protocols.
- **`identity` (`FR-053`, `FR-054`):**
  - Tables: `users`, `organisations`, `memberships`.
  - Roles: `anonymous_contributor` (unauthenticated public intake boundary), `registered_contributor`, `reviewer`, `investigator`, `environmental_specialist`, `intervention_manager`, `organisation_admin`, `system_admin`.
  - Server-side RBAC dependencies and separation-of-duties helper (e.g., preventing reviewers from reviewing their own staff-submitted observations).
- **`collection` & `observations` (`FR-001`–`FR-010`, `FR-046`, `FR-048`, `FR-050`, `NFR-001`, `NFR-002`, `NFR-004`):**
  - Tables: `observations`, `observation_versions`, `observation_sources`.
  - Idempotent `POST /api/v1/observations` keyed on client-generated UUID / `idempotencyKey` (safe retry returns original receipt).
  - Four distinct timestamps (`event_start_at`, `observed_at`, `submitted_at`, authoritative server `received_at`) plus explicit `time_precision` (`exact`, `approximate`, `range`, `unknown`) and `location_precision`.
  - Structured field protocol fields (method, instrument, units, measurement value, quality flags) stored in typed columns with bounded versioned extension payload.
  - Controlled corrections append new `observation_versions` rows without mutating original observation content.
  - Contributor identity/contact stored solely in restricted `observation_sources` (excluded from public and general DTOs).
- **`evidence` (`FR-011`–`FR-015`, `FR-056`, `NFR-005`, `NFR-006`):**
  - Tables: `evidence_assets`, `asset_derivatives`.
  - Content-signature verification (magic bytes, not extension alone), configurable size/MIME limits, SHA-256 checksums, server-generated storage keys (path-traversal safe), and quarantine/scan status fields.
  - Original assets stored untouched under restricted access; EXIF-stripped previews/thumbnails created as separate `asset_derivatives` records; application-mediated/signed retrieval.
- **`cases` (`FR-025` baseline, `FR-028`–`FR-033`, `FR-048`, `FR-058` baseline):**
  - Tables: `cases`, `case_observations`.
  - Independent case creation, many-to-many observation linking with link rationale, investigator assignment, competing hypotheses/evidence gaps fields, controlled referral metadata, status history, and redacted public summary endpoints.
  - Bounded geo-temporal list, map-feature, and chronological timeline endpoints distinguishing all four date types.
- **`audit` (`FR-055`):**
  - Table: `audit_events` (append-only; transactional logging for role changes, case status changes, sensitive evidence access, and corrections).

#### 1.2 Phase 1 Acceptance Criteria
- `make up` starts Postgres 16 + PostGIS 3.4 and Alembic migrations apply cleanly from empty DB.
- Duplicate retries with the same `idempotencyKey` / client UUID produce one observation and return the original receipt.
- Original uploaded files retain exact checksums; previews exist separately; unauthorised roles cannot access restricted originals or `observation_sources`.
- Case edits and status changes never overwrite linked observations.
- `make lint` (`ruff`) and `make test` (`pytest`, creating and removing temporary test records only) pass in CI.

---

### Phase 2 — Evidence Correlation, Async Worker & Offline Sync Hardening (ECII)

**Objective:** Implement the SignalWeave-derived **Evidence Correlation and Incident Intelligence** subsystem cleanly inside EcoWatch, decouple heavy processing into a recoverable database worker, and harden offline/low-connectivity sync contracts.

#### 2.1 Modules & Responsibilities
- **`jobs` (`docs/07` §4, `docs/files/22` §13, `NFR-001`):**
  - Table: `processing_jobs`.
  - In-process bounded worker started via FastAPI lifespan, claiming jobs safely using `SELECT ... FOR UPDATE SKIP LOCKED`.
  - Tracks `pending`, `processing`, `processed`, `failed` states, attempt counts, exponential backoff + jitter retry scheduling, and bounded concurrency.
  - Runs async tasks: evidence security scan / EXIF extraction (`FR-017`) and ECII correlation scoring.
- **`correlation` (`FR-018`–`FR-027`, `FR-047`, `NFR-003`, `NFR-010`):**
  - Table: `evidence_relationships`.
  - **Bounded Candidate Retrieval:** Spatial (`PostGIS ST_DWithin`, catchment/waterbody/site context where available) + configurable per-category temporal windows + semantic candidate pre-filter. Explicitly excludes previously `rejected` pairs and enforces lower-context bounds when location is absent.
  - **Task-Specific Models (no single universal score):**
    - Duplicate / near-identical submission detection.
    - Same-event grouping (semantic, spatial decay, temporal decay, context rules).
    - Source-dependency / repost detection (`FR-027`) so copied claims do not inflate corroboration.
    - Cross-case relevance suggestions.
  - **Missing-Signal-Safe Scoring & Explainability:**
    - Semantic embeddings via local candidate model (`ADR-019`, loaded once at worker start with bounded concurrency) plus clearly labelled deterministic keyword fallback.
    - Score normalises strictly over available signals (missing signals omitted from denominator, never invented).
    - Persists component scores, weights/scales/model version, plain-language reason codes, missing signals list, and `unverified` suggestion status.
  - **Provisional Cluster & Human Review Boundary:**
    - Provisional clusters stay staff-only and never count as confirmed cases (`docs/files/22` §9).
    - Flags close-scoring ties as ambiguous; prohibits naive transitive merging (`A~B` and `B~C` never auto-merges `A` and `C`).
    - Reviewer APIs: `accept`, `reject` (retained in history), `mark_ambiguous`, `promote_to_case`, `merge`, `split` — all audited, reversible via new actions, and blocked if reviewer equals submitter.
- **`collection` & `notifications` Offline/Realtime Hardening (`FR-049`, `FR-051`, `FR-052`, `FR-057`, `NFR-002`, `NFR-004`):**
  - Split-phase intake contract: lightweight text/coordinates/timestamps land via fast `POST /api/v1/observations` (`202 Accepted` / `201`), followed by separate `POST /api/v1/observations/{id}/evidence` media uploads.
  - Deterministic client-error vs transient-error status codes so offline queues halt retries on permanent validation errors.
  - `notifications` table + optional lightweight WebSocket invalidation events to Staff dashboards (REST remains authoritative; zero push to unauthenticated public).
  - Governance workflows for data export, correction, and policy-compliant deletion (`FR-057`).

#### 2.2 Phase 2 Acceptance Criteria
- Observation intake latency does not depend on embedding or correlation execution (`NFR-001`).
- Correlation suggestions expose component scores, method version, missing signals, and plain-language reasons (`NFR-003`), and are labelled unverified.
- Rejected relationships are preserved and excluded from re-suggestion.
- Offline split-phase uploads and retries remain idempotent across simulated interruptions.
- Labelled evaluation suite (`tests/evaluation/`) measures precision, recall, false links, missed links, and ambiguity rate across source types and geographies using temporary/consented evaluation sets.

---

### Phase 3 — Environmental Intelligence, Prioritisation, Interventions & Verification

**Objective:** Deliver the domain-specific environmental analysis, transparent decision support, intervention lifecycle, and rigorous outcome verification capabilities that complete EcoWatch's `Collect -> Analyse -> Prioritise -> Intervene -> Verify` loop.

#### 3.1 Modules & Responsibilities
- **`catalogue` (`FR-016`, `FR-034`):**
  - Tables: `datasets`, `dataset_versions`.
  - Records external/permissioned satellite, hydrological, laboratory, and institutional datasets with owner, licence, attribution, geographic/temporal coverage, resolution, method, and limitations.
- **`intelligence` (`FR-035`–`FR-039`, `NFR-003`, `NFR-010`):**
  - Tables: `environmental_entities` (sites, catchments, waterbodies, habitats), `environmental_relationships`, `analysis_runs`, `analysis_outputs`.
  - Enforces raw observation vs derived analytical output separation (`FR-035`).
  - Reproducible `analysis_runs` (dispatched via `processing_jobs`) recording dataset version IDs, CRS, quality/cloud masks, seasonal context, algorithm parameters, and limitations.
  - Typed `environmental_relationships` (e.g., `upstream_downstream`, `source_pathway_receptor`, `habitat_connectivity`) carrying supporting evidence, uncertainty, alternative explanations, and human review status — never auto-claiming causation.
  - Gated predictive analysis interface (`FR-039`, future-ready hook blocked unless representative validated model metadata is registered).
- **`prioritisation` (`FR-040`, `FR-041`):**
  - Table: `prioritisation_assessments`.
  - Exposes structured, transparent multi-factor views (magnitude, persistence, ecosystem sensitivity, exposure, evidence quality, downstream connectivity, data gaps) and missing-input indicators alongside authorised human priority decisions and rationale.
- **`interventions` (`FR-042`):**
  - Tables: `interventions`, `intervention_milestones`.
  - Tracks objective, linked case(s), responsible organisation/lead, approvals, geography, planned/actual dates, milestones, resources, and supporting evidence.
- **`verification` (`FR-043`–`FR-045`, `FR-058`):**
  - Tables: `indicator_definitions`, `indicator_measurements`, `verification_assessments`.
  - Enforces explicit separation between `activity_completed`, `output_delivered`, `environmental_outcome`, and `recovery_verified`.
  - Records baseline vs post-intervention measurements with units, methods, quality controls, seasonal/rainfall context, and optional reference sites.
  - Restricts `recovery_verified` transitions to authorised environmental reviewers with documented criteria and uncertainty.
  - Approved public-summary publication views stripping contributor identities, sensitive coordinates, and unverified allegations (`FR-058`).

#### 3.2 Phase 3 Acceptance Criteria
- Every analytical output links reproducibly to `analysis_runs`, `dataset_versions`, CRS, parameters, and limitations.
- Prioritisation records expose all underlying factors, missing data, and human rationale.
- Completing an intervention or milestone never automatically marks a case or outcome as `recovery_verified`.
- End-to-end lifecycle tests (`Collect -> Analyse -> Prioritise -> Intervene -> Verify`), backup/restore verification, and release-gate security checks pass.

---

## 4. Cross-Cutting Non-Functional & CI Alignment

| Concern | Implementation Approach Across Phases |
|---|---|
| **Local & CI Tooling** | Python 3.14, `ruff` (`make lint`), `pytest` (`make test`), PostgreSQL 16 + PostGIS 3.4 (`compose.yaml`, `make up`), integrated into `.github/workflows/ci.yml` (`backend` job activates automatically once `backend/pyproject.toml` exists). |
| **Database Integrity** | UUID PKs, unique `idempotency_key` constraints, FK integrity, enumerated status checks, coordinate/non-negative checks, PostGIS GiST spatial indexes, B-tree status/timestamp indexes, and query pagination/bounds on every list endpoint. |
| **Security & Privacy** | Server-side RBAC, rate limiting/throttling on public intake, strict Pydantic validation, untrusted-data handling (prompt injection safe), content-verified file uploads outside public web roots, zero personal data in application logs. |
| **Testing Discipline** | Temporary test-created records cleaned up per test run (`DR-018` / Agent Guide §5); separate unit, integration, security, offline-contract, and correlation-evaluation test suites. |
