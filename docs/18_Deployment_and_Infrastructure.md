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
