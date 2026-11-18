# 06 — Database and Data Architecture

**Status:** PostgreSQL approved; detailed schema and spatial extension require design review.

## 1. Purpose

EcoWatch needs a reliable structured record of observations, cases, sources, timestamps, evidence, relationships, interventions and verification outcomes. The database must preserve the distinction between what was reported, what was measured, what was inferred and what has been verified.

## 2. Approved database technology

**PostgreSQL is approved as EcoWatch's relational database technology.**

### Why PostgreSQL is suitable
- It is a mature relational database with transactions and constraints.
- It supports structured relationships between observations, cases, contributors, datasets and actions.
- It supports indexing and querying for operational workflows.
- It can store JSON fields when flexible metadata is needed, while retaining relational structure for core records.
- It has a broad ecosystem and can be operated independently of a single application vendor.

Approval of PostgreSQL does not approve a hosting provider, managed platform, authentication provider or frontend/backend framework.

## 3. Spatial capability

PostGIS is a PostgreSQL extension that provides geospatial data types and operations. It is a strong candidate because EcoWatch may need to relate observations to rivers, watersheds, administrative boundaries, sites and downstream locations.

**Status: proposed, not yet approved.** The team should confirm the pilot's spatial queries, deployment options, operational skills and data requirements before locking it in.

## 4. Conceptual entities

### Observation
An original report, measurement, image-derived observation or imported record. It should retain its original source and provenance.

Suggested fields:
- `observation_id`
- `source_type`
- `source_reference`
- `category`
- `description`
- `observed_at` or date range
- `submitted_at`
- `received_at`
- `event_start_at` when supplied or estimated, with provenance
- `date_accuracy`
- `location` and `location_accuracy`
- `evidence_type`
- `verification_status`
- `created_by` or anonymous submission reference
- `created_at`, `updated_at`

### Evidence asset
A file or external evidence item associated with an observation.

Suggested fields:
- `asset_id`
- `observation_id`
- `storage_reference`
- `original_filename`
- `media_type`
- `file_size`
- `checksum`
- `uploaded_at`
- `metadata_extraction_status`
- `security_scan_status`
- `access_classification`

### Incident/case
An evolving investigation hypothesis that may be linked to one or more observations.

Suggested fields:
- `case_id`
- `title`
- `summary`
- `case_category`
- `status`
- `priority`
- `area_reference`
- `opened_at`
- `closed_at`
- `assigned_to`
- `created_by`
- `last_reviewed_at`

### Observation-case relationship
A separate record linking an observation to a case, including relationship type, reviewer, date and rationale. This avoids forcing an observation into one case or overwriting its original meaning.

### Dataset
A named data collection with owner/source, licence, coverage, time range, measurement method, version and quality notes.

### Analysis result
A reproducible record of an analytical run, including method/model version, input identifiers, parameters, output, uncertainty and reviewer status.

### Intervention
A planned or completed response action with objective, location, responsible party, schedule, status and supporting evidence.

### Indicator measurement
A measurement or assessment with indicator name, value, unit, method, sample location, sample time, quality-control information and source.

### Verification assessment
An assessment of whether a defined outcome is supported by post-intervention evidence, including comparison period, method, limitations and reviewer.

### Audit event
A record of important changes, actor, time, affected record and reason.

## 5. Data modelling principles

1. Keep observations immutable in meaning. Corrections should be recorded as amendments or superseding records with history.
2. Separate cases from observations.
3. Separate evidence files from structured metadata.
4. Keep contributor identity separate from public case content.
5. Store dates with timezone-aware semantics; use UTC for server records and retain source timezone where relevant.
6. Store units explicitly for environmental measurements.
7. Record coordinate reference systems and location precision.
8. Preserve source identifiers and licences for imported datasets.
9. Do not store an AI confidence score without documenting what it represents.
10. Use controlled vocabularies for statuses and categories, with versioned changes.

## 6. Data classification

- **Public:** information approved for public display.
- **Internal:** operational information for authorised EcoWatch users.
- **Restricted:** personal data, sensitive locations, protected species locations or sensitive investigation material.
- **High sensitivity:** credentials, security secrets and any specially protected records; these should not be stored in ordinary application tables as plain text.

## 7. Data integrity and backups

Use database constraints, foreign keys and transactions to protect relationships. Establish automated backups, restore testing, access control and change migration procedures before production use. A backup that has never been restored in a test is not a proven recovery plan.

## 8. Storage separation

PostgreSQL should store structured records and references to media. Large photographs, videos and documents should generally be stored in controlled object/file storage, with access mediated by the application. The specific storage provider is not selected.

## 9. Supabase and Firebase

These are not part of the approved pilot database decision:
- Supabase uses PostgreSQL as its database foundation and offers additional managed backend services.
- Firebase is a separate platform with its own database and application services.

Their costs, capabilities, security model, data location, vendor dependency and integration with the approved PostgreSQL approach will be evaluated in a separate document. No pilot dependency on either is assumed.

## 10. Open design questions

- Is PostGIS required in the first pilot release?
- Which fields are mandatory for each observation type?
- Which measurement units and vocabularies will be standardised?
- What retention periods apply to anonymous reports and uploaded media?
- What data must be exportable for researchers or public agencies?
- How will dataset versioning and correction be represented?
