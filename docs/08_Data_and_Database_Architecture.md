# 08 — Data and Database Architecture

**Status:** PostgreSQL approved (`ADR-005`). Phase 1 schema (17 PostgreSQL + PostGIS tables in `backend/alembic/versions/0001_phase1_initial_schema.py`) implemented per `ADR-028` and `ADR-029`; Phases 2–3 logical tables remain proposed until their respective phases.

## 1. Design principles

- Preserve original observations.
- Separate observations, evidence assets, cases, relationships, analysis outputs, interventions and verification assessments.
- Keep contributor identity separate from public-facing content.
- Preserve temporal precision and source.
- Record units, coordinate reference systems and method versions.
- Avoid storing large binary media directly in relational tables unless a specific reason exists.
- Make important changes auditable.

## 2. Core entities

### Observation
A reported, measured, sensed, interpreted-from-source or imported record. It includes source type, observation type, content, location/time precision and provenance.

### Evidence asset
An original file or structured data object. It has a checksum, storage key, media type, size, access class and derivative relationships.

### Case
A managed environmental investigation/response record. It has a scope, status, geography, summary, owner and lifecycle.

### Evidence relationship
A typed link between an observation/asset and another observation or case. It records method, score components, explanation, direction, review status and reviewer decision.

### Environmental relationship
A domain-specific relationship between environmental entities or observations, such as upstream/downstream, possible pathway, habitat connectivity or temporal association. It must carry evidence and uncertainty.

### Analysis run
A reproducible record of inputs, method/version, parameters, outputs, execution time and quality limitations.

### Intervention
A planned or actual response activity connected to one or more cases.

### Verification assessment
A structured evaluation of outcome indicators against a baseline or comparison, with method, reviewer and conclusion.

### Audit event
An immutable or append-only record of sensitive actions and status changes.

## 3. Proposed logical tables

| Table | Purpose |
|---|---|
| `users` | Account identity and authentication reference (Phase 1) |
| `organisations` | Participating organisations (Phase 1) |
| `memberships` | User-to-organisation roles (Phase 1) |
| `methods` | Controlled field/lab measurement protocols (`ADR-028`, Phase 1) |
| `units` | Controlled measurement units (`ADR-028`, Phase 1) |
| `observations` | Core org-scoped observation records (Phase 1) |
| `observation_versions` | Controlled corrections/version history (Phase 1) |
| `observation_sources` | Source and contributor metadata with restricted access (Phase 1) |
| `evidence_assets` | Original and derivative file metadata (Phase 1) |
| `asset_derivatives` | Original-to-preview/analysis derivative links (Phase 1) |
| `clarification_requests` | Reviewer/investigator clarification prompts (`ADR-028`, Phase 1) |
| `datasets` | External/imported dataset catalogue (Phase 3) |
| `dataset_versions` | Source version, licence, coverage and acquisition details (Phase 3) |
| `cases` | Org-scoped environmental investigation/response cases (Phase 1) |
| `case_observations` | Many-to-many observation/case links (Phase 1) |
| `evidence_relationships` | Suggested/reviewed evidence links and explanations (Phase 2) |
| `correlation_embeddings` | Semantic vector representations for correlation retrieval (`ADR-028`, Phase 2) |
| `environmental_entities` | Optional sites, waterbodies, catchments, habitats or monitored assets (Phase 3) |
| `environmental_relationships` | Domain relationships between entities/observations (Phase 3) |
| `analysis_runs` | Reproducible analysis metadata (Phase 3) |
| `analysis_outputs` | Derived maps, metrics, rasters, tables and reports (Phase 3) |
| `prioritisation_assessments` | Factors, method, score/rank and human decision (Phase 3) |
| `interventions` | Planned and actual response actions (Phase 3) |
| `intervention_milestones` | Activity milestones and supporting evidence (Phase 3) |
| `indicator_definitions` | Approved indicator metadata and units (Phase 3) |
| `indicator_measurements` | Measurements with method, quality and source (Phase 3) |
| `verification_assessments` | Outcome assessment records (Phase 3) |
| `publications` | Versioned public release snapshots (`ADR-028`, Phase 3) |
| `audit_events` | Security and workflow audit (Phase 1) |
| `processing_jobs` | Durable asynchronous job state (`FOR UPDATE SKIP LOCKED`, Phase 1) |
| `notifications` | User notifications and clarification delivery (Phase 1) |
| `rate_limit_buckets` | DB-backed intake/tracking-lookup rate limiting and lockouts (Phase 1) |

Phase 1 tables are migration-backed in `backend/alembic/versions/0001_phase1_initial_schema.py` using `lower snake_case` SQL names mapped to `camelCase` Python/JSON DTO attributes (`ADR-029`). Phases 2–3 tables remain logical specifications until built.

## 4. Observation fields

Candidate fields:
- `id` UUID.
- `observation_type`.
- `description` or structured value.
- `source_type`.
- `observed_at` and/or temporal interval.
- `submitted_at`.
- `received_at`.
- `event_start_at` if known.
- `time_precision` and original time wording.
- `location` or geometry.
- `location_precision` and original location wording.
- `method_id` or protocol reference.
- `quality_flags`.
- `visibility/access_class`.
- `created_at`, `updated_at`.

Do not put all content into one unstructured JSON field. Use typed columns for stable query dimensions and JSON only for bounded, versioned extension data.

## 5. Time semantics

Preserve:
- Event start: when a condition is believed to have begun.
- Observed time: when a person or instrument observed it.
- Submitted time: when a contributor submitted it.
- Received time: when the server durably received it.
- Processing time: when a system task ran.

A reported or estimated time must carry precision and source. Do not infer exactness from a date-only value.

## 6. Spatial model

Phase 1 uses PostGIS `GEOGRAPHY(POINT, 4326)` and `GEOGRAPHY(GEOMETRY, 4326)` columns with `GiST` spatial indexes (`ADR-029`) and stores source geometry separately from generalised `public_location` / `public_geometry` columns. Coordinate reference systems and units remain explicit.

Environmental relationships may require network or catchment data. A straight-line distance query is not a substitute for flow direction, river connectivity or ecological connectivity.

## 7. Many-to-many case relationships

One observation may be relevant to multiple cases. A case may contain many observations. A relationship record must capture why the observation is linked, who or what proposed the link, whether it is reviewed and whether the link is contested.

Do not enforce a simplistic rule that every observation belongs to exactly one incident.

## 8. Integrity and indexing

Candidate constraints:
- Unique UUIDs and idempotency keys.
- Foreign keys for all managed relationships.
- Valid enumerated statuses.
- Check constraints for coordinate ranges and non-negative quantities.
- Indexes on observation/case status and timestamps.
- Spatial indexes if PostGIS is approved.
- Indexes on source and dataset version identifiers.
- Transactional audit events for consequential changes.

Index design must be measured against actual pilot queries.

## 9. Data lifecycle

Raw input → validated observation → protected original evidence → derived assets/analysis → reviewed relationships → case record → intervention → verification.

Corrections should create versioned changes, not silently rewrite history. Retention and deletion policies remain subject to legal review and stakeholder approval.
