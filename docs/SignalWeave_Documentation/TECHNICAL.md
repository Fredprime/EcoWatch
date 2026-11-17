# SignalWeave — Technical Design Document

**Version:** 1.0  
**Companion to:** `PRD.md`  
**Recommended backend:** Python + FastAPI  
**Architecture style:** Modular monolith, asynchronous processing, offline-first client

## 1. Technical direction

Build SignalWeave as a modular monolith for the hackathon. One deployable backend contains clear internal modules for report intake, correlation, incident management, persistence and realtime updates.

Use Python because the project’s differentiating work is semantic similarity, numerical scoring, geospatial analysis and optional image processing. Python provides the shortest path to a credible working ML pipeline and matches the team's existing skills. Go is technically capable, but introducing a second language or moving the ML path into a less mature ecosystem adds integration work without proving a meaningful hackathon advantage.

### Recommended stack

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React + TypeScript | Reporter and analyst interfaces |
| Map | MapLibre GL JS | Incident and report map |
| API | Python + FastAPI | REST API, validation, auth boundary |
| Validation | Pydantic | Request and response schemas |
| Database | PostgreSQL + PostGIS | Reports, incidents, geospatial queries |
| ORM/migrations | SQLAlchemy + Alembic | Persistence and schema changes |
| Embeddings | Sentence Transformers | Semantic representations |
| Inference optimisation | ONNX Runtime | CPU inference where practical |
| Numerical work | NumPy / SciPy | Scoring and distance calculations |
| Image handling | Pillow / OpenCV | Resize, compression and basic metadata handling |
| Realtime | FastAPI WebSockets | Dashboard event updates |
| Offline client queue | IndexedDB for web; SQLite for a native/local collector | Durable pending reports |
| Testing | pytest; frontend test tooling | Unit, integration and acceptance tests |
| Packaging | Docker Compose | Repeatable local demo |

Do not add Redis, Kafka, Celery, Kubernetes or microservices to the initial build. PostgreSQL and an in-process bounded background worker are enough for the controlled hackathon workload. If the worker is restarted, pending processing can be recovered by querying unprocessed records in the database.

## 2. High-level architecture

```text
                 REPORTER / FIELD CLIENT
              React PWA + local durable queue
                          |
                    HTTPS REST API
                          |
                 FastAPI application
                          |
          +---------------+----------------+
          |               |                |
     Report module   Incident module   Review/auth module
          |               |                |
          +---------------+----------------+
                          |
                 PostgreSQL + PostGIS
                          |
               Candidate retrieval query
                          |
                 Correlation service
          +---------------+----------------+
          |               |                |
      Embedding       Spatial/time       Context
      similarity       scoring          scoring
          |               |                |
          +---------------+----------------+
                          |
                 Evidence relationships
                          |
                 Incident/cluster update
                          |
                 WebSocket event stream
                          |
               React analyst dashboard
                 Map + list + timeline
```

### Main processing sequence

1. Client creates a UUID for the report and persists it locally.
2. Client sends the report with the UUID as its idempotency key.
3. API validates the payload and attachment metadata.
4. API inserts the report; a unique constraint prevents duplicate submissions.
5. API marks the report as pending correlation.
6. A bounded background worker claims pending reports.
7. Worker retrieves candidate reports/incidents using PostGIS and time indexes.
8. Correlation service calculates semantic and other available scores.
9. Worker stores suggestions and creates or updates a provisional incident.
10. API publishes a small incident/report update event over WebSockets.
11. Dashboard fetches the authoritative incident details through REST.

Do not make the client wait for model inference before receiving a successful report receipt.

## 3. Backend module layout

Suggested repository:

```text
signalweave/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── reports.py
│   │   │   │   ├── incidents.py
│   │   │   │   ├── reviews.py
│   │   │   │   └── health.py
│   │   │   └── websocket.py
│   │   ├── schemas/
│   │   │   ├── report.py
│   │   │   ├── incident.py
│   │   │   └── review.py
│   │   ├── models/
│   │   │   ├── report.py
│   │   │   ├── incident.py
│   │   │   ├── evidence.py
│   │   │   └── audit.py
│   │   ├── services/
│   │   │   ├── report_service.py
│   │   │   ├── incident_service.py
│   │   │   ├── correlation/
│   │   │   │   ├── candidates.py
│   │   │   │   ├── embeddings.py
│   │   │   │   ├── scoring.py
│   │   │   │   └── clustering.py
│   │   │   ├── media_service.py
│   │   │   └── event_service.py
│   │   ├── workers/
│   │   │   └── correlation_worker.py
│   │   └── db/
│   │       ├── session.py
│   │       └── migrations/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── features/
│   │   │   ├── reporting/
│   │   │   ├── incidents/
│   │   │   ├── map/
│   │   │   └── review/
│   │   ├── lib/
│   │   └── offline/
│   └── package.json
├── data/
│   ├── seed/
│   └── sample-media/
├── docs/
│   ├── PRD.md
│   └── TECHNICAL.md
├── compose.yaml
└── README.md
```

Keep modules small and responsibility-focused. Avoid turning every folder into a separate service.

## 4. Data model

Use UUID primary keys. Store event time separately from server receipt time because they represent different facts.

### reports

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key; client-generated idempotency ID |
| description | TEXT | Required, length-limited |
| category | VARCHAR | Nullable controlled category |
| event_time | TIMESTAMPTZ | Nullable observation/event time |
| submitted_at | TIMESTAMPTZ | Server receipt time |
| location | GEOGRAPHY(POINT, 4326) | Nullable PostGIS point |
| reporter_id | UUID | Nullable/private user reference |
| processing_status | VARCHAR | pending, processing, processed, failed |
| media_metadata | JSONB | Optional safe metadata; no raw untrusted paths |
| created_at | TIMESTAMPTZ | Server timestamp |

Indexes:
- Unique primary key on `id`.
- GiST index on `location`.
- B-tree index on `event_time`.
- B-tree index on `processing_status`.
- Optional composite indexes based on observed query patterns.

### incidents

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| title | VARCHAR | Editable short label |
| summary | TEXT | Evidence-grounded summary |
| category | VARCHAR | Nullable |
| status | VARCHAR | provisional, under_review, confirmed_by_analyst, rejected, closed |
| centroid | GEOGRAPHY(POINT, 4326) | Nullable |
| confidence_score | REAL | Correlation score, not probability |
| created_at | TIMESTAMPTZ | Server timestamp |
| updated_at | TIMESTAMPTZ | Server timestamp |

### evidence_relationships

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| report_id | UUID | Foreign key to reports |
| incident_id | UUID | Foreign key to incidents |
| score | REAL | Combined score |
| score_components | JSONB | Semantic, spatial, temporal and context values |
| explanation | JSONB | Human-readable reason codes/values |
| status | VARCHAR | suggested, accepted, rejected |
| reviewed_by | UUID | Nullable analyst ID |
| reviewed_at | TIMESTAMPTZ | Nullable |

Add a uniqueness constraint appropriate to the chosen relationship model, such as one active report-to-incident relationship per report. Preserve rejected suggestions in history rather than deleting them.

### audit_events

Record actor, action, target, timestamp and minimal metadata for review actions, merges and splits.

### Media storage

For the prototype, store files on a controlled local volume or a configured object-storage bucket. Store only generated storage keys and validated metadata in PostgreSQL. Never use a user-supplied filename as a filesystem path.

## 5. Correlation engine

The correlation engine is the core differentiator. Keep it deterministic, testable and explainable.

### 5.1 Candidate generation

Do not compare each incoming report against every historical report. First narrow the candidate set.

When a report has coordinates:
- Use PostGIS `ST_DWithin` to find reports/incidents within a configurable radius.
- Restrict candidates to a configurable event-time window where event time is available.
- Exclude rejected relationships and optionally closed incidents, according to product rules.

When location is absent:
- Use a wider but bounded time window and semantic retrieval over a limited recent candidate set.
- Mark the result as lower-context and avoid overconfident automatic grouping.

Candidate filtering should be category-aware where enough reliable category data exists. A flood may affect a larger area than a blocked road.

### 5.2 Semantic similarity

Use a compact sentence embedding model such as `sentence-transformers/all-MiniLM-L6-v2` as the initial baseline. It is suitable for a prototype because it is relatively small and designed for sentence-level similarity.

Process:
1. Normalise whitespace and reject empty/oversized text.
2. Generate an embedding for each report.
3. L2-normalise embeddings.
4. Calculate cosine similarity between the new report and candidate report text or an incident representation.
5. Cache embeddings so historical reports are not repeatedly encoded.

For CPU deployment, evaluate exporting the model to ONNX and using ONNX Runtime. Validate numerical consistency and latency before relying on the exported model. Cache model files before the demo; do not make the live demonstration depend on downloading a model.

A deterministic keyword or TF-IDF fallback may be provided for test mode if the embedding model cannot load. Clearly label fallback mode; do not present it as equivalent ML inference.

### 5.3 Spatial score

For two valid points, compute geodesic distance or use PostGIS distance in metres. A simple decay:

`spatial_score = exp(-distance_km / distance_scale_km)`

The distance scale is configurable by incident category. If either point is missing, mark spatial evidence unavailable rather than assigning a fabricated score.

### 5.4 Temporal score

Use the absolute difference between event timestamps:

`temporal_score = exp(-abs(delta_minutes) / time_scale_minutes)`

Prefer event time over submission time when available. If event time is missing, submission time can be used only as a weaker proxy and the explanation must disclose that.

### 5.5 Context score

For MVP, context can be category agreement or a small rule-based compatibility score. Do not claim advanced entity extraction unless implemented and tested.

Example:
- Same compatible category: high context score.
- Related categories: moderate score.
- Contradictory categories: low score or a review warning.
- Missing category: unavailable signal.

### 5.6 Weighted score

For available signals:

`combined = sum(weight_i * score_i) / sum(weight_i for available signals)`

Initial weights:
- semantic 0.40
- spatial 0.25
- temporal 0.25
- context 0.10

These weights are tunable prototype parameters. Persist both the final score and component scores. The UI must not describe this value as a calibrated probability.

Suggested prototype bands:
- 0.75 and above: strong candidate
- 0.50–0.74: possible candidate
- below 0.50: do not attach automatically

All machine-generated relationships remain suggestions until reviewed by a human. Test threshold behaviour against labelled positive and negative pairs.

### 5.7 Cluster assignment

For each new report:
1. Generate candidate incidents.
2. Score the report against each candidate incident using representative evidence (for example, the best matching report plus incident-level time/location context).
3. Rank candidates.
4. If the top candidate exceeds the configured suggestion threshold, create a suggested relationship.
5. Otherwise create a new provisional incident and attach the report as its initial evidence.
6. If multiple candidates are close in score, flag ambiguity for analyst review rather than choosing silently.

Avoid naive transitive merging: if A matches B and B matches C, it does not necessarily follow that A and C describe the same incident. Keep pairwise evidence and cluster-level constraints visible.

### 5.8 Explainability payload

Example:

```json
{
  "score": 0.82,
  "components": {
    "semantic": 0.91,
    "spatial": 0.78,
    "temporal": 0.74,
    "context": 0.80
  },
  "reasons": [
    "Descriptions are semantically similar",
    "Reports are geographically close",
    "Observation times are within the configured window",
    "Categories are compatible"
  ],
  "missing_signals": []
}
```

The actual values above are illustrative only.

## 6. Image handling

Image analysis is optional for the MVP. The first version should use images as supporting evidence attached to reports, not as the sole basis for incident correlation.

Required safeguards:
- Enforce file size and allowed image formats.
- Verify file signatures rather than trusting extension or MIME header alone.
- Generate storage names.
- Strip EXIF metadata where appropriate, especially GPS and device identifiers, unless location metadata is an explicit, consented feature.
- Resize/compress client-side where practical and validate again server-side.
- Never execute uploaded files.
- Keep image access private or access-controlled.

A later phase may add lightweight image classification or similarity, but do not let it delay the text/location/time correlation demo.

## 7. API design

Use versioned REST routes under `/api/v1`.

### Submit report

`POST /api/v1/reports`

Example request:

```json
{
  "id": "7d43c3d8-6c44-4c88-9a9d-8c4d42e3a100",
  "description": "Water has covered the junction and cars cannot pass.",
  "category": "flooding",
  "event_time": "2026-11-12T09:20:00Z",
  "location": {
    "latitude": 5.6037,
    "longitude": -0.1870
  }
}
```

Return `202 Accepted` after durable receipt, not after the full correlation job. Repeated submission with the same ID should return the existing report receipt.

### Get report

`GET /api/v1/reports/{report_id}`

### List incidents

`GET /api/v1/incidents?status=under_review&category=flooding&since=...`

Support pagination and bounded filters.

### Get incident detail

`GET /api/v1/incidents/{incident_id}`

Return incident metadata, evidence relationships, reports, score explanations and timeline.

### Review relationship

`POST /api/v1/incidents/{incident_id}/relationships/{relationship_id}/review`

Example:

```json
{
  "decision": "accept",
  "note": "Same junction and observation period."
}
```

Only authorised analysts can use this route.

### Merge incidents

`POST /api/v1/incidents/{incident_id}/merge`

P1. Require an explicit target incident, permission check and audit event.

### Split relationship

`POST /api/v1/relationships/{relationship_id}/reject`

P0 relationship rejection can use this simpler action. Full cluster splitting is P1.

### Health

`GET /health`

Expose application health without leaking secrets or internal configuration.

## 8. Realtime updates

Use WebSockets for small notification events, not as the source of truth.

Example event:

```json
{
  "type": "incident.updated",
  "incident_id": "uuid",
  "report_id": "uuid",
  "occurred_at": "2026-11-12T09:21:00Z"
}
```

The client receives the event and fetches the latest incident detail through REST. This avoids sending large, potentially stale incident payloads over the socket.

For the hackathon, an in-process connection manager is acceptable. If the app later runs multiple backend instances, introduce a shared event broker only when required.

## 9. Offline and low-bandwidth design

### Client behaviour

- Persist each report locally before attempting upload.
- Use a UUID generated at report creation.
- Maintain states: `queued`, `syncing`, `submitted`, `failed`.
- Retry transient failures with exponential backoff and jitter.
- Stop automatic retries for permanent validation errors and show the user what needs correction.
- Upload text and coordinates first.
- Upload image attachments separately after the report is accepted.
- Compress images and enforce a maximum attachment size.
- Avoid repeatedly downloading full incident histories; fetch deltas/details on demand.

For a web PWA, IndexedDB is the practical browser-native durable queue. If the team builds a native field collector or local agent, SQLite is appropriate. Do not try to assume that a browser has a normal writable SQLite filesystem.

### Server behaviour

- Enforce idempotency with the report UUID as a unique key.
- Return a receipt as soon as the report is durably stored.
- Process correlation asynchronously.
- Make worker operations safe to retry.
- Store processing state in PostgreSQL so a restarted worker can resume pending work.

### Bandwidth priority

1. Report text and report ID.
2. Coordinates and event time.
3. Small metadata.
4. Compressed image.
5. Optional additional media.

## 10. Background processing without a task-broker dependency

For the hackathon:
- Use FastAPI lifespan to start a bounded worker loop.
- Worker polls a small batch of pending reports from PostgreSQL.
- Claim jobs safely using a transaction and row locking (for example, `FOR UPDATE SKIP LOCKED`).
- Mark the record processing, execute correlation, then persist results and mark processed.
- On recoverable failure, increment attempts and return it to pending with a retry time.
- On repeated failure, mark failed and expose a safe operational status.

Keep inference concurrency bounded to avoid loading multiple model copies or exhausting laptop memory. Load the model once at startup and warm it before the demo.

This is a prototype worker, not a replacement for a durable distributed task system at production scale.

## 11. Frontend information architecture

### Reporter experience
- Short report form.
- Location picker and optional device location.
- Event time selector.
- Optional image attachment.
- Offline/online and sync status.
- Submission receipt.

### Analyst dashboard
- **Overview:** active/provisional incidents and recent reports.
- **Map:** incident points/areas with selectable markers.
- **Incident detail:** title, status, confidence, summary and evidence list.
- **Timeline:** event times and submission times clearly distinguished.
- **Review panel:** score components, explanation, accept/reject controls.
- **Filters:** status, category and time range.

Use labels and icons alongside colour. Avoid presenting confidence as a definitive danger level.

## 12. Security and privacy implementation

- Use Pydantic validation and strict bounds for all request fields.
- Enforce authentication for analyst/admin routes.
- Apply role checks on the server; hiding a button in the frontend is not authorisation.
- Use parameterised database operations/ORM.
- Validate uploads by content and size; store outside the application code directory.
- Strip unnecessary image metadata.
- Rate-limit public report intake where practical.
- Keep secrets in environment variables; commit only `.env.example`.
- Use HTTPS outside localhost.
- Avoid logging full report text, private user details or image contents by default.
- Restrict exact reporter identity to authorised roles.
- Record analyst review actions.
- Treat all report content as untrusted user data.

For a hackathon demo, authentication can be simple, but analyst review endpoints must not be openly writable in a deployed environment.

## 13. Deployment and local development

Use Docker Compose for a repeatable local environment:
- `backend`
- `frontend`
- `postgres` with PostGIS

Persist PostgreSQL data in a named volume. Mount a local media volume if using filesystem storage. Provide a seed command for the demo dataset.

Keep the backend and database in one deployment environment for the MVP. The model artefact should be cached in the image or mounted model directory so the first live report does not trigger an internet download.

Environment variables should include:
- `DATABASE_URL`
- `MODEL_NAME` or `MODEL_PATH`
- `MODEL_DEVICE=cpu`
- `UPLOAD_DIR`
- `MAX_UPLOAD_BYTES`
- `CORS_ORIGINS`
- `APP_ENV`
- authentication secrets

Do not put real secrets in the repository.

## 14. Testing strategy

### Unit tests
- Text normalisation and embedding similarity.
- Spatial and temporal decay.
- Weighted scoring with missing signals.
- Candidate filtering.
- Threshold and ambiguity handling.
- Idempotency behaviour.
- Upload validation.

### Integration tests
- Report submission and database persistence.
- Duplicate submission with the same UUID.
- Background correlation and relationship persistence.
- Analyst accept/reject flow.
- WebSocket notification followed by REST refresh.
- Worker recovery after simulated failure.

### Offline tests
- Create report while offline.
- Reload client and verify queued report remains.
- Restore network and retry.
- Verify exactly one server-side report exists.
- Simulate image upload failure while text report remains accepted.

### Evaluation dataset
Create a small labelled dataset with:
- Several reports describing the same simulated incident in different words.
- Nearby reports describing different incidents.
- Similar wording in different locations or times.
- Reports with missing coordinates.
- Reports with missing event times.
- Ambiguous examples that should be sent to human review.

Measure precision, recall, false merges and processing latency. Keep the dataset and expected labels in version control.

## 15. Performance targets and measurement

Prototype targets under a documented local test setup:
- API receipt: fast and independent of model inference.
- Warm correlation fast path: approximately 250 ms for a small candidate set, subject to hardware and model.
- Dashboard update: approximately 500 ms from receipt under controlled local conditions.
- No unbounded task creation or unbounded in-memory queues.

Record:
- API receipt latency.
- Queue wait time.
- Candidate count.
- Embedding inference time.
- Scoring time.
- Database write time.
- End-to-end time to dashboard visibility.

Do not claim these targets are achieved until measured on the actual demo machine.

## 16. Implementation sequence

### Phase 1 — Skeleton
- Create repository and Docker Compose.
- Start FastAPI, React and PostgreSQL/PostGIS.
- Add health check and migrations.

### Phase 2 — Report path
- Build report form.
- Add report schema and persistence.
- Add UUID idempotency.
- Add map coordinate handling.

### Phase 3 — Correlation engine
- Add candidate query.
- Add sentence embeddings.
- Add spatial/time/context scoring.
- Persist score components and explanations.
- Add provisional incident assignment.

### Phase 4 — Analyst experience
- Build incident list, map, detail and timeline.
- Add accept/reject controls.
- Add WebSocket update notifications.

### Phase 5 — Offline and reliability
- Add local durable queue.
- Add retry/backoff and sync states.
- Prioritise text/location before images.
- Test duplicate retries and interrupted sync.

### Phase 6 — Demo hardening
- Seed labelled reports.
- Warm model and cache artefacts.
- Test misleading/ambiguous examples.
- Measure latency.
- Rehearse a repeatable end-to-end demonstration.

## 17. Demo script

1. Open the analyst dashboard with no active incident.
2. Submit a report describing flooding at a junction.
3. Submit a differently worded report with a nearby location and close event time.
4. Submit a photograph-backed report describing blocked vehicles at the same location.
5. Show SignalWeave proposing a shared incident, with semantic, spatial and temporal reasons.
6. Open the incident timeline and evidence list.
7. Submit a similar-sounding report from a different area or time.
8. Show that it remains separate or is marked ambiguous.
9. Reject one deliberately incorrect relationship and show the audit/review state.
10. Disable connectivity, create another report, restore connectivity and show safe synchronisation without duplication.

## 18. Known limitations

- Similarity scores are not truth scores or calibrated probabilities.
- Reports can be false, malicious, duplicated or inaccurate.
- A location pin may be approximate or intentionally misleading.
- Sparse evidence can make correct correlation impossible.
- A compact text embedding model may perform unevenly on local language, slang and multilingual reports.
- Image processing does not establish when or where an image was taken.
- Prototype latency and reliability do not imply production readiness.
- Human review remains essential before operational decisions.

## 19. Technical decision record

| Decision | Choice | Reason |
|---|---|---|
| Backend language | Python | Fastest path to semantic/geospatial ML implementation; team familiarity |
| API framework | FastAPI | Typed validation, async API and WebSocket support |
| Architecture | Modular monolith | Simple to build, test and deploy within hackathon time |
| Database | PostgreSQL + PostGIS | Relational integrity and native geospatial candidate filtering |
| Semantic model | Compact sentence transformer | Local semantic similarity without hosted LLM dependency |
| Inference optimisation | ONNX Runtime where validated | Potentially faster/lighter CPU inference |
| Realtime | WebSockets | Timely dashboard notifications |
| Offline web queue | IndexedDB | Durable browser-side storage |
| Background work | Bounded DB-backed worker | Avoids introducing broker infrastructure prematurely |
| Image role | Supporting evidence first | Keeps core correlation reliable and achievable |

**Final technical principle:** make the evidence pipeline correct, explainable and resilient before adding more models or infrastructure.
