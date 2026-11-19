# 18 — Deployment and Infrastructure

**Status:** Design principles defined; providers and hosting region open.

## 1. Deployment approach

Keep the first environment simple and reproducible. Separate development, testing/staging and production. Use production only after the release gates in the testing and governance documents are satisfied.

## 2. Candidate components

- Web/PWA hosting.
- API application hosting.
- PostgreSQL database.
- PostGIS extension if approved.
- Object storage for original evidence and derivatives.
- Background workers for correlation, imports and environmental analysis.
- Authentication/identity provider.
- Domain and TLS.
- Monitoring and error reporting.
- Backup and recovery.
- Notification delivery if required.

No provider is selected.

## 3. Environment separation

Development uses synthetic or appropriately protected test data. Staging validates releases with representative non-sensitive data. Production contains real records and must have restricted access, monitoring, backups and an operational owner.

## 4. Data location and provider assessment

Evaluate data residency, latency, cost, contract terms, backup location, export, access control and applicable Ghanaian obligations. Do not assume the default provider region is suitable.

## 5. Reliability and recovery

Define recovery point objective (acceptable data loss) and recovery time objective (acceptable restoration time). Specify backup frequency, retention, restore authority and tested procedures. Back up database metadata and original media; a database-only backup is insufficient.

## 6. Cost control

Estimate compute, database, storage, bandwidth, backups, map services, imagery processing, model execution, email and monitoring. Media and raster processing may dominate costs. Set usage limits and alerts.

## 7. Candidate local development

SignalWeave proposed React, FastAPI, PostgreSQL/PostGIS and Docker Compose. These remain candidates for the merged project, with PostgreSQL itself approved. Avoid adding Redis, Kafka, Kubernetes or microservices before measured need.

## 8. Platform evaluation

Supabase, Firebase and other providers remain unselected. Evaluate them separately against relational/geospatial requirements, authentication, storage, background processing, export, data location, cost and operational burden. Firebase may introduce a second data model if PostgreSQL remains the system of record; quantify that cost rather than assuming it is simpler.

## 9. Implemented Backend Hardening, Operations & Global Rules Applicability

- **Private database networking:** `compose.yaml` binds PostgreSQL to `127.0.0.1` only for local development; `compose.prod.yaml` places `db` on an internal-only `backend_private` bridge network with zero exposed host ports.
- **Least-privilege DB account:** `scripts/init_least_privilege_db.sql` creates a non-superuser `ecowatch_app` runtime role (`NOSUPERUSER NOCREATEDB NOCREATEROLE`) separate from the migration/owner role.
- **Backup & restore:** `scripts/backup_db.sh` and `scripts/restore_db.sh` provide repeatable `pg_dump`/`pg_restore` custom-format procedures.
- **Health & metrics:** `GET /health` verifies PostgreSQL/PostGIS and storage readiness; `GET /metrics` exposes PII-free Prometheus counters and latency sums with `Cache-Control: no-store, private`.
- **Runtime limits & caching:** `RequestLimitsAndHeadersMiddleware` enforces JSON/multipart body limits, bounded concurrency, request timeouts, `X-Content-Type-Options: nosniff`, and strict `Cache-Control` isolation alongside `GZipMiddleware`.
- **Global Rules Applicability (per `GLOBAL_AGENT_RULES_MERGED.md` §17.6):**
  - **§§4, 5, 17.2, 17.3 (Hardware, Arduino C++, Wi-Fi provisioning/AP, SIM/SMS, buzzer):** `N/A` — EcoWatch is a Python/FastAPI + PostgreSQL/PostGIS + React/Vite web platform with no embedded firmware or hardware device targets.
  - **§17.4 Cookie Consent Banner:** `N/A` for non-essential tracking cookies — EcoWatch does not use third-party advertising/analytics cookies or trackers; authentication uses bearer tokens.
