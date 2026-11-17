# 08 — Data and Database Architecture

**Status:** PostgreSQL approved. PostGIS and detailed schema are proposed and require review.

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
| `users` | Account identity and authentication reference |
| `organisations` | Participating organisations |
| `memberships` | User-to-organisation roles |
| `observations` | Core observation records |
| `observation_versions` | Controlled corrections/version history |
| `observation_sources` | Source and contributor metadata with restricted access |
| `evidence_assets` | Original and derivative file metadata |
| `asset_derivatives` | Original-to-preview/analysis derivative links |
| `datasets` | External/imported dataset catalogue |
| `dataset_versions` | Source version, licence, coverage and acquisition details |
| `cases` | Environmental investigation/response cases |
| `case_observations` | Many-to-many observation/case links |
| `evidence_relationships` | Suggested/reviewed evidence links and explanations |
| `environmental_entities` | Optional sites, waterbodies, catchments, habitats or monitored assets |
| `environmental_relationships` | Domain relationships between entities/observations |
| `analysis_runs` | Reproducible analysis metadata |
| `analysis_outputs` | Derived maps, metrics, rasters, tables and reports |
| `prioritisation_assessments` | Factors, method, score/rank and human decision |
| `interventions` | Planned and actual response actions |
| `intervention_milestones` | Activity milestones and supporting evidence |
| `indicator_definitions` | Approved indicator metadata and units |
| `indicator_measurements` | Measurements with method, quality and source |
| `verification_assessments` | Outcome assessment records |
| `audit_events` | Security and workflow audit |
| `processing_jobs` | Durable asynchronous job state |
| `notifications` | Optional user notifications |

This is a conceptual model, not a final migration-ready schema.

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

PostGIS is recommended for points, lines, polygons and spatial indexes, but its inclusion is not yet approved. If adopted, define coordinate reference systems and units explicitly. Store source geometry and any generalised public geometry separately where necessary.

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
