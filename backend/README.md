# EcoWatch Backend (Phase 1)

Phase 1 modular monolith for EcoWatch (`Core Platform, Intake, Provenance & Case Foundation`).

## Architecture & Conventions

- **Stack:** Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL 16 + PostGIS 3.4, Pillow.
- **Naming boundary (`ADR-029`, `docs/AGENT_GUIDE.md` §8):**
  - SQL tables and columns use `lower snake_case`.
  - Python variables, function parameters, ORM/config attributes, and JSON API payloads use `camelCase`.
  - Classes use `PascalCase`; constants use `UPPER_SNAKE_CASE`.
- **Modules (`src/ecowatch/modules/`):**
  - `identity`: Users, organisations, memberships, 8-role deny-by-default RBAC (`docs/PERMISSIONS_MATRIX.md`).
  - `audit`: Append-only `audit_events` persistence and org-scoped read API.
  - `notifications`: Clarification requests and user inbox read tracking.
  - `observations`: Immutable observations, controlled versions, redacted vs. restricted views, isolated `observation_sources`, `methods`, and `units`.
  - `collection`: Idempotent anonymous & authenticated intake, tracking-code hashing + lockout.
  - `evidence`: Magic-byte validation, SHA-256 checksums, untouched originals, scan quarantine, EXIF-stripped derivatives.
  - `jobs`: Durable `processing_jobs` queue (`FOR UPDATE SKIP LOCKED` on PostgreSQL) and worker loop.
  - `cases`: Many-to-many case-observation links, lifecycle transitions, two-key `field_verified` approval (`ES` + `OA`), timelines, and approved public summaries.

## Local Setup & Verification

From the repository root (`EcoWatch/`):

```bash
cp .env.example .env
make venv
.venv/bin/pip install -e "backend[dev]"
make up
cd backend && ../.venv/bin/alembic upgrade head && cd ..
```

Run the API and optional background worker:

```bash
.venv/bin/uvicorn ecowatch.main:app --app-dir backend/src --reload
```

Run lint and tests:

```bash
make lint
make test
ECOWATCH_RUN_POSTGIS_TESTS=1 .venv/bin/pytest backend -v
```
