# 07 — System Architecture

**Status:** Modular monolith is the recommended starting point; framework and provider choices remain subject to approval.

## 1. Architecture goals

- One coherent EcoWatch product.
- Clear separation between evidence correlation and environmental analysis.
- Strong relational integrity and geospatial capability.
- Durable collection independent of slow analytics.
- Explainable, reviewable automated suggestions.
- Low operational complexity for a small team.
- Ability to scale selected workloads later without redesigning every domain boundary.

## 2. Proposed logical architecture

```text
Community / Field / Research / Institutional / Sensor / Remote-sensing sources
                                  |
                           Web / PWA clients
                                  |
                            API boundary
                                  |
             +--------------------+---------------------+
             |                    |                     |
       Collection             Identity &            Notifications
       and intake             permissions            (optional)
             |
       Observation service
             |
       Evidence/provenance service ---- Object storage
             |
       PostgreSQL relational store (+ PostGIS proposed)
             |
       Durable processing queue / database job records
             |
      +------+-------------------------------+
      |                                      |
Evidence Correlation &                 Environmental Intelligence
Incident Intelligence                  and Geospatial Analysis
      |                                      |
      +-------------------+------------------+
                          |
                    Case management
                          |
            Prioritisation / Intervention
                          |
                   Verification
                          |
                 Analyst/research UI
```

## 3. Recommended application structure

Start with a modular monolith: one application deployment with domain modules, explicit service boundaries and shared transactional database. Avoid microservices until operational evidence demonstrates a need.

Suggested modules:
1. Identity and access.
2. Collection and ingestion.
3. Observation management.
4. Evidence and provenance.
5. Correlation and incident intelligence.
6. Environmental data catalogue.
7. Geospatial/environmental analysis.
8. Case and investigation management.
9. Prioritisation.
10. Intervention and verification.
11. Notifications and audit.

## 4. Processing boundaries

Report/observation receipt should be fast and durable. Semantic embeddings, raster processing, large imports and imagery analysis should run asynchronously. Persist job state in a recoverable store. Use bounded concurrency and retries.

A database-backed worker is acceptable for an initial controlled prototype. A dedicated queue/task system may be evaluated later if workload, retries, scheduling or multiple worker processes require it.

## 5. Candidate technical stack

| Layer | Candidate | Status |
|---|---|---|
| Frontend | React + TypeScript | Proposed; consistent with SignalWeave design |
| Map | MapLibre GL JS | Proposed |
| Backend | Python + FastAPI | Proposed; strong fit for data/ML workflows |
| Validation | Pydantic | Proposed with FastAPI |
| Database | PostgreSQL | Approved |
| Geospatial database extension | PostGIS | Proposed; likely important for spatial queries |
| ORM/migrations | SQLAlchemy + Alembic | Proposed |
| Semantic embeddings | Sentence Transformers | Candidate; task validation required |
| Numerical/geospatial processing | NumPy, SciPy, GeoPandas, Rasterio | Candidate; use only where needed |
| Offline web queue | IndexedDB | Proposed |
| Realtime | WebSockets | Optional; only where useful |
| Packaging | Docker Compose | Proposed for repeatable development |

Do not treat this table as final stack approval. Provider, hosting and authentication choices remain open.

## 6. Why not microservices initially?

A small team would incur service discovery, deployment, observability, versioning, network failure and data consistency costs before proving the product's workflows. Modular boundaries provide most early design benefits without that operational burden.

## 7. Future extraction criteria

Consider extracting a module into a separate worker/service only when one or more are demonstrated:
- Independent scaling requirements.
- Heavy raster/model workloads interfere with API availability.
- Different deployment/security boundary is required.
- Worker failures need isolation.
- Multiple teams own separate release cycles.
- A queue or workload cannot be safely managed by the initial worker design.

## 8. API principles

- Version external APIs.
- Validate every input.
- Use idempotency for submissions and retries.
- Return durable receipt before asynchronous analysis completes.
- Paginate lists and bound filters.
- Enforce permissions in backend services.
- Use stable error codes and avoid leaking internals.
- WebSocket events are notifications; REST/API retrieval remains authoritative.

## 9. Offline-first principles

For a browser PWA, IndexedDB is the proposed durable local queue. Use stable client IDs, explicit sync states and safe retries. Local device time is not authoritative server receipt time. Local drafts and queued submissions must be distinguishable from successfully received records.
