# EcoWatch Backend Architecture and Three-Phase Implementation Plan

**Version:** 1.1  
**Date:** 2026-11-17  
**Status:** Proposed architecture blueprint (zero application code written yet). Version 1.1 applies a technical review: corrected coverage claims, closed sequencing defects, and listed the decisions that must be approved before Phase 1 code is written.  
**Target Directory:** `backend/` (Python 3.14, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL 16 + PostGIS 3.7 + pgvector)

---

## 1. Purpose and Architectural Principles

This document translates EcoWatch's merged baseline (`docs/00`–`24`, `docs/files/22_Correlation_Engine_and_Offline_Collection.md`, `docs/AGENT_GUIDE.md`) and repository infrastructure (`compose.yaml`, `Makefile`, `.github/workflows/ci.yml`, `CONTRIBUTING.md`) into a concrete, **three-phase backend architecture**.

### Core Architectural Decisions
1. **Modular Monolith First (`ADR-013`, `docs/07`):** One deployable FastAPI service (`backend/`) backed by one PostgreSQL 16 + PostGIS 3.7 + pgvector database (`compose.yaml`). Domain modules communicate via explicit service/interface calls inside one process and share ACID transactions without premature microservices, Redis, Kafka, or Kubernetes.
2. **Database-Backed Asynchronous Processing (`docs/07` §4, `docs/files/22` §13):** Slow or heavy tasks (media scanning/derivatives, ECII semantic embeddings and correlation, dataset imports, spatial/raster analysis) execute asynchronously via a `processing_jobs` table (`FOR UPDATE SKIP LOCKED` row claiming) in a bounded in-app worker loop. API intake returns durable receipt immediately (`NFR-001`).
3. **Provider Interfaces for Open Choices (`docs/18`, `docs/AGENT_GUIDE.md` §7):** Authentication/identity verification and object storage (evidence originals and derivatives) sit behind narrow Python protocols/interfaces so local development (local disk + local token/session auth) swaps cleanly to chosen cloud/object-storage/IdP providers later.
4. **Organisation-scoped data (`docs/05` §2, `docs/16` §3, `ADR-027`):** Every aggregate row carries `organisation_id`, and access is deny-by-default. Without it, the `organisation_admin` role and every "own organisation" restriction in `docs/PERMISSIONS_MATRIX.md` are unimplementable. A missing `organisation_id` is a defect, not a default of "everyone can see it".
5. **Naming and Data Boundary (`docs/AGENT_GUIDE.md` §8):**
   - PostgreSQL tables and columns: `lower snake_case`.
   - API request/response payloads: `camelCase`, mapped at one Pydantic boundary.
   - Python identifiers: `snake_case` (PEP 8), `PascalCase` for classes/types, `UPPER_SNAKE_CASE` for constants. This is the one place where `docs/AGENT_GUIDE.md` §8 and this plan disagreed; v1.1 resolves it toward Python convention so `ruff` code runs instead of being configured off. **Owner confirmation still required** — see §6 item 2.
6. **Non-Negotiable Safety & Scientific Integrity Guardrails (`docs/AGENT_GUIDE.md` §5, `CONTRIBUTING.md` §7):**
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
|    - jobs            (processing_jobs worker, SKIP LOCKED loop)   |
|    - notifications   (clarification_requests, notifications)      |
|                                                                   |
|  Modules (Phase 2 — ECII Correlation):                            |
|    - correlation     (candidate search, scoring, explainability,  |
|                       provisional clusters, review/merge/split)   |
|                       + correlation_embeddings                    |
|                                                                   |
|  Modules (Phase 3 — Intelligence, Prioritisation & Verification): |
|    - catalogue       (datasets, dataset_versions, data rights)    |
|    - intelligence    (environmental_entities, relationships,      |
|                       analysis_runs, analysis_outputs)            |
|    - prioritisation  (prioritisation_assessments, factor views)   |
|    - interventions   (interventions, milestones, baselines)       |
|    - verification    (indicator_definitions, measurements,        |
|                       verification_assessments, public summaries, |
|                       publications)                               |
+-------------------------------------------------------------------+
          |                                      |
PostgreSQL 16 + PostGIS 3.7 + pgvector              Object Storage Interface
(26 tables from `docs/08` + 5 proposed   (Restricted originals vs.
 additions, see §5, Alembic)             derivatives / previews)
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
| **Phase 1** | Roadmap Phase 1 | Durable, idempotent evidence collection, provenance preservation, RBAC, and case foundation | 11 tables (`users`, `organisations`, `memberships`, `observations`, `observation_versions`, `observation_sources`, `evidence_assets`, `asset_derivatives`, `cases`, `case_observations`, `audit_events`) + `processing_jobs`, `notifications`, `clarification_requests`, `methods`, `units` (see §5) | `core`, `identity`, `collection`, `observations`, `evidence`, `cases`, `audit`, `jobs`, `notifications` |
| **Phase 2** | Roadmap Phase 2 | Explainable ECII evidence correlation, human review, and offline sync hardening | +2 tables (`evidence_relationships`, `correlation_embeddings`) + rejected-pair index (see §5) | `correlation` (+ `evidence` async scan, `collection` split-phase sync) |
| **Phase 3** | Roadmap Phases 3, 4, 5 | Permissioned environmental datasets, geospatial/environmental analysis, prioritisation, interventions, and verified recovery | +12 tables (`datasets`, `dataset_versions`, `environmental_entities`, `environmental_relationships`, `analysis_runs`, `analysis_outputs`, `prioritisation_assessments`, `interventions`, `intervention_milestones`, `indicator_definitions`, `indicator_measurements`, `verification_assessments`) + `publications` (see §5) | `catalogue`, `intelligence`, `prioritisation`, `interventions`, `verification` |

### Requirement traceability

Every requirement in `docs/06` is mapped to a phase below, so acceptance tests can be traced in both directions. This table, not a percentage, is the coverage claim.

| FR | Phase | Module | Acceptance anchor |
|---|---|---|---|
| FR-001 | P1 | collection, observations | Intake accepts anonymous + registered; 201/202 receipt |
| FR-002 | P1 | collection | Client UUID / idempotency key, stable across retries |
| FR-003 | P1 | observations | Description, type, source_type, submission metadata columns |
| FR-004 | P1 | observations | Nullable geometry, location_precision, original wording |
| FR-005 | P1 | observations | Four timestamps, server receipt authoritative |
| FR-006 | P1 | observations | time_precision / location_precision enums, no invented values |
| FR-007 | P1 | collection | Pydantic bounds: text, coordinates, timestamps, units, size |
| FR-008 | P1 | collection | Idempotent retry returns original receipt |
| FR-009 | P1 | observations | Structured protocol fields + measurement metadata |
| FR-010 | P1 | observations | observation_versions append; originals never mutated |
| FR-011 | P1 | evidence | Content-signature validation, size/MIME limits |
| FR-012 | P1 | evidence | Original preserved; previews/derivatives as separate rows |
| FR-013 | P1 | evidence | SHA-256, source, acquisition method, processing history |
| FR-014 | P1 | evidence | Server-generated storage keys, no user filenames as paths |
| FR-015 | P1 | evidence | Access class on assets; restricted originals |
| FR-016 | P3 | catalogue | Dataset licence, attribution, coverage, permitted use |
| FR-017 | P1 fields / P2 scan | evidence, jobs | Scan/quarantine status fields now; scanner in P2 |
| FR-018 | P2 | correlation | Bounded candidate retrieval (spatial, temporal, category) |
| FR-019 | P2 | correlation | Semantic similarity as one optional signal |
| FR-020 | P2 | correlation | Spatial + temporal compatibility where data permits |
| FR-021 | P2 | correlation | Missing signals marked unavailable, never invented |
| FR-022 | P2 | correlation | Component scores, method version, reason codes persisted |
| FR-023 | P2 | correlation | Suggestions labelled unverified |
| FR-024 | P2 | correlation | Reviewer accept / reject / ambiguous |
| FR-025 | P1 | cases | case_observations many-to-many, typed link + rationale |
| FR-026 | P2 | correlation | Merge/split with audit and preserved history |
| FR-027 | P2 | correlation | Repost / shared-source dependence detection |
| FR-028 | P1 | cases | Case creates independently of observations |
| FR-029 | P1 | cases | Case summary, status, geography, timeline, linked evidence |
| FR-030 | P1 | cases | Reviewer, status changes, rationale recorded |
| FR-031 | P1 | cases | Assignment + follow-up actions |
| FR-032 | P1 | cases | Competing hypotheses + evidence gap fields |
| FR-033 | P1 | cases | Controlled referral + external reference record |
| FR-034 | P3 | catalogue | Permissioned dataset import with provenance |
| FR-035 | P3 | intelligence | Raw observation vs derived output separation |
| FR-036 | P3 | intelligence | Historical comparison + map overlays |
| FR-037 | P3 | intelligence | Method, parameters, input versions, limitations recorded |
| FR-038 | P3 | intelligence | Typed environmental relationships (upstream/downstream, pathway) |
| FR-039 | P3 | intelligence | Gated prediction hook, blocked without validated model |
| FR-040 | P3 | prioritisation | Factor view + missing inputs, no opaque score |
| FR-041 | P3 | prioritisation | Human priority decision + rationale |
| FR-042 | P3 | interventions | Objective, owner, location, dates, milestones, evidence |
| FR-043 | P3 | verification | activity != output != outcome != recovery enforced |
| FR-044 | P3 | verification | Baseline + follow-up indicators, units, uncertainty |
| FR-045 | P3 | verification | improvement / no_improvement / deterioration / inconclusive |
| FR-046 | P1 API / frontend | collection | Mobile-friendly intake contract |
| FR-047 | P1 | cases, correlation | Reviewer access to evidence + relationship explanations |
| FR-048 | P1 | cases | Map / list / timeline endpoints |
| FR-049 | P2 | notifications | Live update notifications where useful (WS optional) |
| FR-050 | P1 contract | collection | Draft persistence is client-side; server distinguishes local vs received |
| FR-051 | P2 | collection | Sync states + safe retry of transient failures |
| FR-052 | P2 | collection | Split-phase: text/coords first, media after |
| FR-053 | P1 | identity | Server-side RBAC dependencies (rules: ADR-027) |
| FR-054 | P1 | observations, identity | Identity isolated; never in public DTOs |
| FR-055 | P1 | audit | Append-only audit events, same transaction |
| FR-056 | P1 | evidence | Uploads outside public roots; application-mediated retrieval |
| FR-057 | P2 | governance | Correction, export, deletion workflows |
| FR-058 | P3 | verification, publications | Approved public summaries, sensitive data stripped |

**Honest position at v1.1:** all 58 `FR` and 10 `NFR` identifiers are now mapped. Before v1.1 the document claimed "58/58" while 21 `FR` identifiers carried no phase tag and `NFR-007`, `NFR-008`, `NFR-009` appeared nowhere, so nothing could be traced to a test.

---

### Phase 1 — Core Platform, Intake, Provenance & Case Foundation

**Objective:** Establish a reliable, security-hardened API and database foundation where observations and media are captured idempotently with full provenance, contributor identity is isolated, and authorised staff can manage cases.

#### 1.1 Modules & Responsibilities
- **`core`:** Environment config (`.env`), SQLAlchemy async/sync engine with connection pooling, PostGIS geometry/geography helpers (`SRID 4326` storage with explicit CRS metadata), `camelCase` <-> `snake_case` Pydantic base schema, structured non-leaking error responses, bounded pagination, and `StorageProvider` / `AuthProvider` protocols.
- **`identity` (`FR-053`, `FR-054`):**
  - Tables: `users`, `organisations`, `memberships`.
  - Roles: `anonymous_contributor` (unauthenticated public intake boundary), `registered_contributor`, `reviewer`, `investigator`, `environmental_specialist`, `intervention_manager`, `organisation_admin`, `system_admin`.
  - Server-side RBAC dependencies and separation-of-duties helper (e.g., preventing reviewers from reviewing their own staff-submitted observations).
  - **Grant set: `docs/PERMISSIONS_MATRIX.md` (`ADR-027`, Proposed).** Deny-by-default, eight roles, `organisation_id` on every aggregate. `FR-053` cannot be implemented from this plan alone — the rules live in the matrix and must be approved first.
  - **Anonymous access is an intake boundary, not a role with data access.** Anonymous contributors submit and retrieve their own receipt by tracking code only: a high-entropy code (≥128 bits), hashed at rest, served over a throttled endpoint with attempt-limit lockout. Without this, `docs/05` Workflow A's "receives a reference" is not implementable and the acceptance criterion below is untestable.
- **`notifications` + `clarification_requests` (`docs/05` Workflow B):** `docs/05` promises clarification requests and no entity existed for them. Phase 1 adds `clarification_requests` so a request has an addressable record, an inbox for `registered_contributor`, and a delivery channel. Anonymous contributors can only be reached if they left contact details, which is a documented limitation, not a hidden failure.
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
  - **Scan policy must be explicit.** The fields exist in Phase 1; the scanner is a Phase 1 `jobs` task, not Phase 2, so that `FR-017` has an executor in the phase that declares its fields. Policy is fail-closed for public/anonymous uploads (stored but not served until scanned) and fail-open for staff uploads pending review, with both recorded on the asset.
  - **Derivative generation is a Phase 1 `jobs` task** (thumbnails, EXIF-stripped previews). Generating them inside the upload request would make receipt latency depend on image work and violate `NFR-001`.
  - Original assets stored untouched under restricted access; EXIF-stripped previews/thumbnails created as separate `asset_derivatives` records; application-mediated/signed retrieval.
- **`cases` (`FR-025` baseline, `FR-028`–`FR-033`, `FR-048`, `FR-058` baseline):**
  - Tables: `cases`, `case_observations`.
  - Independent case creation, many-to-many observation linking with link rationale, investigator assignment, competing hypotheses/evidence gaps fields, controlled referral metadata, status history, and redacted public summary endpoints.
  - Bounded geo-temporal list, map-feature, and chronological timeline endpoints distinguishing all four date types.
- **`audit` (`FR-055`):**
  - Table: `audit_events` (append-only; transactional logging for role changes, case status changes, sensitive evidence access, and corrections).

#### 1.2 Phase 1 Acceptance Criteria
- `make up` builds/starts PostgreSQL 16 + PostGIS 3.7 + pgvector and Alembic migrations apply cleanly from an empty DB.
- Duplicate retries with the same `idempotencyKey` produce one observation and return the original receipt. **Re-using a key with a different payload must be rejected with a stable error code, not silently return the old receipt** — the behaviour is defined once, in the API contract.
- Original uploaded files retain exact checksums; previews exist separately; unauthorised roles cannot access restricted originals or `observation_sources`.
- Case edits and status changes never overwrite linked observations.
- **Cross-organisation isolation is tested:** an `organisation_admin` in organisation A receives 404 (not 403) for organisation B's observation, case and asset identifiers.
- **Anonymous receipt retrieval is tested:** a tracking code returns the submitter's own receipt, a wrong code is rate-limited and locked out, and no other observation is reachable.
- **Illegal case status transitions are rejected** (e.g. `closed -> recovery_verified`), with the allowed transitions and their required roles taken from `docs/PERMISSIONS_MATRIX.md` §4.
- `make lint` (`ruff`) and `make test` (`pytest`, creating and removing temporary test records only) pass in CI.

---

### Phase 2 — Evidence Correlation, Async Worker & Offline Sync Hardening (ECII)

**Objective:** Implement the SignalWeave-derived **Evidence Correlation and Incident Intelligence** subsystem cleanly inside EcoWatch, decouple heavy processing into a recoverable database worker, and harden offline/low-connectivity sync contracts.

#### 2.1 Modules & Responsibilities
- **`jobs` (`docs/07` §4, `docs/files/22` §13, `NFR-001`):**
  - Table: `processing_jobs` — **introduced in Phase 1** (§1.1), because Phase 1 already needs an executor for `FR-017` scanning and derivative generation. Phase 2 adds job types, not the mechanism.
  - In-process bounded worker started via FastAPI lifespan, claiming jobs safely using `SELECT ... FOR UPDATE SKIP LOCKED`.
  - Tracks `pending`, `processing`, `processed`, `failed` states, attempt counts, exponential backoff + jitter retry scheduling, bounded concurrency, and a `dead` terminal state after the attempt limit so a poison job cannot loop forever.
  - Phase 2 adds: ECII correlation scoring jobs and the embedding backfill job.
- **`correlation` (`FR-018`–`FR-027`, `FR-047`, `NFR-003`, `NFR-010`):**
  - Tables: `evidence_relationships`, plus **`correlation_embeddings`** — the 26-table model in `docs/08` has nowhere to store vectors, so "semantic candidate pre-filter" was previously unimplementable. One row per (observation, model version, input hash) with a fixed-dimension vector column and an index, so re-embedding is skipped when the text and model are unchanged. **The vector type and index must be chosen before Phase 1's first Alembic revision**, because it is a schema decision, not a Phase 2 convenience (`pgvector` is the default candidate; see §5 item 3).
  - **Rejected-pair exclusion needs a designed index.** Excluding prior rejections is a pairwise lookup, not a filter: normalise `(observation_a_id, observation_b_id)` to a canonical order with a unique constraint, so the exclusion is an index probe and cancel/reject is idempotent. Without it, candidate retrieval degrades toward a scan per intake.
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

**Split-phase sync contract — as built (ADR-034/036, 2026-11-19).** The plan above
is the intent; this is the concrete backend contract now enforced on
`backend/remaining-work`:

| Phase | Call | Idempotency | Success | Replay / conflict |
|---|---|---|---|---|
| A — text/coords/timestamps | `POST /api/v1/observations` with a client `idempotencyKey` (UUID body field) | keyed on `idempotencyKey` | `201` with a receipt | same key + same payload returns the original receipt (`idempotentReplay: true`); same key + different payload is `409 IDEMPOTENCY_KEY_CONFLICT` |
| B — media | `POST /api/v1/observations/{id}/evidence` with an `Idempotency-Key` (UUID request header) | keyed on (observation, idempotency key), unique via migration `0006_evidence_upload_idempotency` | `201` with the asset receipt | same key + same bytes returns the original `assetId` (`idempotentReplay: true`); same key + different bytes is `409 IDEMPOTENCY_KEY_CONFLICT` |

Error classification for both phases (`ADR-036`): every error envelope carries
`category: permanent | transient`. `4xx` validation, auth and conflict errors are
**permanent** — an offline queue must stop retrying. Rate-limit (`429`), tracking-
code lockout (`429`), `EVIDENCE_NOT_READY` (`409`, scan still in flight) and all
`5xx` are **transient**; `429`/`5xx` also carry a `Retry-After` header and a
`retryAfterSeconds` body field so clients can back off deterministically. Intake
latency never includes embedding or scan work — both are enqueued as
`processing_jobs` in the same transaction.

**Explicitly out of scope (ADR-036):** a server-side observation `syncState`
column/endpoint and WebSocket invalidation pushes. Durable queueing, explicit
client sync states and reconnect behaviour belong to the frontend PWA; REST
remains authoritative. `/observations/export` (OA own org / SA) and
`POST /observations/{id}/hide` (SA only) complete the `FR-057` governance branch
of this workstream as tombstone + restrict, never deletion of originals
(`ADR-034`).

#### 2.2 Phase 2 Acceptance Criteria
- Observation intake latency does not depend on embedding or correlation execution (`NFR-001`).
- Correlation suggestions expose component scores, method version, missing signals, and plain-language reasons (`NFR-003`), and are labelled unverified.
- Rejected relationships are preserved and excluded from re-suggestion, by index lookup rather than by rescanning.
- Offline split-phase uploads and retries remain idempotent across simulated interruptions.
- **Evaluation harness runs and reports** precision, recall, false links, missed links, ambiguity rate and reviewer override rate per source type and language.

**Correction to the previous acceptance criterion.** Version 1.0 required the suite to *measure* these metrics "across source types and geographies". That criterion could never be met at the start of Phase 2: `DR-018` and `AGENT_GUIDE` §5 forbid seeded or demo data, and `docs/files/22` §19 states that real labels only exist after real staff reviews. A phase cannot be accepted on data that does not yet exist.

Two admissible routes, owner's choice (`docs/files/23` §6.1 already raises the same conflict for demonstrations):

1. **Harness-only acceptance (recommended for a prototype).** The harness, the metric definitions and a scored run on a small consented set are the acceptance. No accuracy claim is published until real reviewed decisions accumulate.
2. **Separate synthetic corpus.** A labelled corpus exists in an isolated environment that never touches the product database, is clearly marked synthetic, and is never presented as evidence of accuracy.

Without one of these, Phase 2 has no pass condition. Correlation stays a clearly labelled suggestion with no accuracy claim either way.

---

### Phase 3 — Environmental Intelligence, Prioritisation, Interventions & Verification

**Objective:** Deliver the domain-specific environmental analysis, transparent decision support, intervention lifecycle, and rigorous outcome verification capabilities that complete EcoWatch's `Collect -> Analyse -> Prioritise -> Intervene -> Verify` loop.

#### 3.1 Modules & Responsibilities
- **`catalogue` (`FR-016`, `FR-034`):**
  - Tables: `datasets`, `dataset_versions`.
  - Records external/permissioned satellite, hydrological, laboratory, and institutional datasets with owner, licence, attribution, geographic/temporal coverage, resolution, method, and limitations.
- **`intelligence` (`FR-035`–`FR-039`, `NFR-003`, `NFR-010`):**
  - Tables: `environmental_entities` (sites, catchments, waterbodies, habitats), `environmental_relationships`, `analysis_runs`, `analysis_outputs`.
  - **`environmental_entities` is not optional here.** `docs/08` marks it optional, but `environmental_relationships` (upstream/downstream, pathway) reference entities; without them the relationship types have no endpoints. Treat it as required and migrate it in this order.
  - Enforces raw observation vs derived analytical output separation (`FR-035`).
  - Reproducible `analysis_runs` (dispatched via `processing_jobs`) recording dataset version IDs, CRS, quality/cloud masks, seasonal context, algorithm parameters, and limitations.
  - **Imagery has no pipeline design yet.** `analysis_outputs` can hold rasters, but nothing specifies the storage format (COG), the catalogue convention (STAC or equivalent), the cloud/shadow masking method, the output layout, or the storage-cost model `docs/18` §6 warns may dominate. Decide before the first raster is stored, because the format choice is expensive to reverse.
  - Typed `environmental_relationships` (e.g., `upstream_downstream`, `source_pathway_receptor`, `habitat_connectivity`) carrying supporting evidence, uncertainty, alternative explanations, and human review status — never auto-claiming causation.
  - Gated predictive analysis interface (`FR-039`, future-ready hook blocked unless representative validated model metadata is registered).
- **`prioritisation` (`FR-040`, `FR-041`, `NFR-007`):**
  - Table: `prioritisation_assessments`.
  - Exposes structured, transparent multi-factor views (magnitude, persistence, ecosystem sensitivity, exposure, evidence quality, downstream connectivity, data gaps) and missing-input indicators alongside authorised human priority decisions and rationale.
  - **The factor set is named but the method is not.** Before this module is written, define: the factor vocabulary and its controlled values, how a missing factor is shown (never imputed), whether any composite rank exists at all, and if it does, its weights, stability test and explicit statement that it is not severity. `docs/13` §3 forbids false precision; a factor view with no missing-data rule quietly becomes one.
- **`interventions` (`FR-042`):**
  - Tables: `interventions`, `intervention_milestones`.
  - Tracks objective, linked case(s), responsible organisation/lead, approvals, geography, planned/actual dates, milestones, resources, and supporting evidence.
- **`verification` (`FR-043`–`FR-045`, `FR-058`):**
  - Tables: `indicator_definitions`, `indicator_measurements`, `verification_assessments`, `publications`, `units`.
  - Enforces explicit separation between `activity_completed`, `output_delivered`, `environmental_outcome`, and `recovery_verified`.
  - Records baseline vs post-intervention measurements with units, methods, quality controls, seasonal/rainfall context, and optional reference sites.
  - **`units` is a dimension table, not a text field.** Free-text units make measurements incomparable and verification unfalsifiable. Measurements also need a detection limit and qualifier (`<`/`>`, not-detected) or a laboratory result cannot be recorded honestly.
  - Restricts `recovery_verified` transitions to authorised environmental reviewers with documented criteria and uncertainty.
  - **The criteria are still missing.** `docs/14` requires "approved criteria" and none have been written anywhere in the repository. Until a document defines minimum detectable change, monitoring duration, comparable methods, reference/comparison locations and seasonality handling, `recovery_verified` cannot be granted by any implementation — the product's central claim rests on an unwritten document. This is decision item 6 in §6.
  - `publications` records who approved a public summary, in what role, when, and the exact published text, so an approved summary can be reproduced or retracted (`docs/05` §9).

#### 3.2 Phase 3 Acceptance Criteria
- Every analytical output links reproducibly to `analysis_runs`, `dataset_versions`, CRS, parameters, and limitations.
- Prioritisation records expose all underlying factors, missing data, and human rationale, and no composite rank exists without a documented method.
- Completing an intervention or milestone never automatically marks a case or outcome as `recovery_verified`.
- **`recovery_verified` is unreachable while the criteria document does not exist.** Either the criteria are approved before this phase is accepted, or the status stays disabled and the product reports observed change with limitations instead (`docs/14` §5).
- Measurements are stored with a resolved unit and a qualifier, so a laboratory result with a detection limit can be recorded without inventing a number.
- Published summaries are reproducible: the approved text and its approvers are stored, and a retraction is an event rather than an edit.
- End-to-end lifecycle tests (`Collect -> Analyse -> Prioritise -> Intervene -> Verify`), backup/restore verification (`NFR-008`), and release-gate security checks pass.

---

## 4. Cross-Cutting Non-Functional & CI Alignment

| Concern | Implementation Approach Across Phases |
|---|---|
| **Local & CI Tooling** | Python 3.14, `ruff` (`make lint`), `pytest` (`make test`), PostgreSQL 16 + PostGIS 3.7 + pgvector (`compose.yaml`, `make up`), integrated into `.github/workflows/ci.yml` (`backend` job activates automatically once `backend/pyproject.toml` exists). |
| **Database Integrity** | UUID PKs, unique `idempotency_key` constraints, FK integrity, enumerated status checks, coordinate/non-negative checks, PostGIS GiST spatial indexes, B-tree status/timestamp indexes, and query pagination/bounds on every list endpoint. |
| **API contract (P1)** | Every Phase 1 endpoint is specified before code: method, path, request/response schema, required role, idempotency behaviour, error codes, and pagination style. A **stable error-code catalogue** (`code`, `message`, `field`, no internals) is part of the contract, not an afterthought; union of 4xx cases is finite and testable. Pagination is cursor-based for observations, cases and timeline; offset is not used for anything that changes while paged. |
| **Security & Privacy** | Server-side RBAC per `docs/PERMISSIONS_MATRIX.md` (`ADR-027`), deny-by-default, organisation scoping on every aggregate. **Rate limiting is specified, not merely named:** per-IP and per-tracking-code limits on public intake and receipt lookup, attempt-limit lockout, bounded request body size, and the counters stored where a restart does not reset them. Strict Pydantic validation, untrusted-data handling (prompt injection safe), content-verified uploads outside public web roots, zero personal data in application logs. |
| **Observability (P1)** | Structured logs with a request id and no personal data, health and readiness endpoints, worker and queue depth metrics, and failure counters per job type. "Zero personal data in logs" is implemented by an allowlist of logged fields, not by reviewer diligence. |
| **Migrations** | Alembic, one revision per phase increment, forward-only in the prototype with a documented rollback note per revision. Any revision that adds a required column to a populated table is split into add-nullable → backfill → set-not-null so a failed deploy is recoverable. |
| **Performance / `NFR-007`** | Design targets only, measured and never claimed: receipt independent of model inference, warm correlation path and dashboard visibility targets from `docs/files/22` §18. Numbers become acceptance criteria after pilot hardware and expected volume are known; until then a benchmark harness records receipt latency, queue wait, candidate count, inference time and scoring time. |
| **Portability / `NFR-008`** | Database dumps, media references, dataset metadata and analysis records must be exportable without the hosting provider. Restore is tested, not assumed (`docs/17` §2), including media, not database alone. |
| **Accessibility / `NFR-009`** | Target WCAG 2.2 AA for the reporting flow and the case workspace: keyboard operation, contrast, labelled controls, plain language. Tested with a real assistive-technology pass at Phase E, not claimed from developer review (`docs/17` §2). |
| **Testing Discipline** | Temporary test-created records cleaned up per test run (`DR-018` / Agent Guide §5); separate unit, integration, security, offline-contract, and correlation-evaluation test suites. Phase 1 acceptance items in §1.2 are the test list — including cross-organisation isolation and anonymous receipt lockout, which are the two that fail silently if untested. |

---

## 5. Schema Additions Required (Proposed)

`docs/08` defines 26 logical tables. This plan maps all 26, but **five additions and one scoping column are needed before the model can support the requirements already written**. They are proposed as `ADR-028`, and `docs/08` should be amended to match once approved — this plan does not silently change the canonical data document.

| Addition | Needed by | Why the current model cannot do without it |
|---|---|---|
| `organisation_id` on `observations`, `cases`, `evidence_assets`, `evidence_relationships`, `interventions`, `prioritisation_assessments`, `verification_assessments` | `FR-053`, `docs/05` §2, `docs/PERMISSIONS_MATRIX.md` | Organisation-scoped roles are unimplementable; cross-org leakage is the default |
| `methods` (id, name, version, protocol text, instrument class) | `docs/08` §4 references `method_id` | The field has no referent; reproducibility claims have nothing to point at |
| `units` (id, symbol, dimension, UCUM code where applicable) | `FR-044`, `docs/14` §5 | Free-text units make verification unfalsifiable |
| `clarification_requests` | `docs/05` Workflow B | A promised workflow with no entity, no inbox, no delivery record |
| `publications` | `FR-058`, `docs/05` §9 | "Approved public summary" with no approver, no timestamp, no stored text |
| `correlation_embeddings` (Phase 2) | `FR-019`, `docs/files/22` §7 | Semantic candidate retrieval has no storage and no index |

Deliberately **not** added at this stage: consent/terms-acceptance records, disputes/right-of-reply, sensor device and calibration tables, chain-of-custody records. All four are real gaps identified in review; none is required to start Phase 1, and inventing them now would be speculative. They are recorded in `docs/21_Risks_Assumptions_and_Open_Questions.md` terms and must be decided before the flows that need them (public reporting, multi-source evidence, laboratory results).

## 6. Decisions Required Before Phase 1 Code

| # | Decision | Owner action | Blocks |
|---|---|---|---|
| 1 | Approve `ADR-027` permission matrix (or amend it) | Approve or correct `docs/PERMISSIONS_MATRIX.md` | `FR-053`, every role check |
| 2 | Naming: DB `snake_case` + JSON `camelCase` + Python `snake_case` | Confirm, per §1.5 | `ruff` configuration, every module |
| 3 | Vector store: `correlation_embeddings` + `pgvector` (or alternative) | Approve | Phase 1's first Alembic revision |
| 4 | Approve `ADR-028` schema additions and amend `docs/08` | Approve | Phase 1 schema |
| 5 | Phase 2 evaluation route: harness-only or separate synthetic corpus | Choose | Phase 2 acceptance has no pass condition otherwise |
| 6 | Verification criteria document (minimum detectable change, duration, reference sites, seasonality) | Commission or write | `recovery_verified`, the product's central claim |
| 7 | Auth mechanism for Phase 1 (local session vs token vs OIDC) | Choose or defer behind `AuthProvider` with a working default | login, tracking-code binding |
| 8 | Python 3.14 vs 3.12 for the image, given Phase 2 needs `sentence-transformers` and Phase 3 may need `rasterio`/`geopandas` | Verify wheel availability, then pin | CI image, `pyproject.toml` requires-python |

## 7. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-17 | Initial three-phase backend blueprint. |
| 1.1 | 2026-11-17 | Technical review applied: corrected the coverage claim and added a full FR traceability table; moved `processing_jobs` into Phase 1 so `FR-017` has an executor in the phase that declares its fields; added organisation scoping, anonymous tracking-code retrieval, scan policy, units/methods/publications/clarification tables; added `correlation_embeddings` and the rejected-pair index; rewrote the Phase 2 evaluation acceptance into two achievable routes; named the missing verification criteria, raster pipeline and prioritisation method; expanded cross-cutting concerns (API contract, error catalogue, pagination, observability, migrations, NFR-007/008/009); listed the eight decisions required before Phase 1. Zero application code. |
