# EcoWatch Review Summary

**Version:** 1.0  
**Last Updated:** 2026-11-17  
**Repository:** `Fredprime/EcoWatch`  
**Active Branch:** `prime`  
**Code Written:** None (pre-build documentation and repository setup stage)

This is the single review document for checking progress, recent changes, and decisions needed before writing application code.

---

## 1. Current State at a Glance

- **Canonical product:** Merged **EcoWatch** (`docs/00`–`24`), incorporating SignalWeave as the **Evidence Correlation and Incident Intelligence (ECII)** subsystem.
- **Repository & branches:**
  - `main`: Protected release branch (`infra / compose + postgis` required, 1 code-owner approval, `enforce_admins: true`, linear history).
  - `master`: Protected integration branch (`infra / compose + postgis` required, 1 approval).
  - `prime`: Active working branch created from `master`; all current documentation updates live here.
- **Existing infrastructure baseline (from `master` commit `88ca75d`):**
  - `compose.yaml`: PostgreSQL 16 + PostGIS 3.4 (`ecowatch-db`, port `5433`, named volume `db-data`).
  - `Makefile` & `scripts/compose.sh`: `venv`, `up`, `down`, `reset`, `psql`, `logs`, `lint` (`ruff check backend`), `test` (`pytest backend`).
  - `.github/workflows/ci.yml`: `infra / compose + postgis` (active), `backend / lint + test` (Python 3.14, activates once `backend/pyproject.toml` exists), `frontend / build` (Node 22, activates once `frontend/package.json` exists).
  - `CONTRIBUTING.md`, `.env.example`, `LICENSE` (Apache-2.0), `NOTICE`, `scripts/protect-branches.sh`.
- **Application folders:** `backend/` and `frontend/` do not exist yet; we will build them from scratch once reviewed.

---

## 2. Changes Made So Far

| Date | Commit / Action | Summary of Changes | Files Affected |
|---|---|---|---|
| 2026-11-17 | Doc audit | Read all docs across `EcoWatch_Merged_Documentation_v1`, `EcoWatch Agent Guide.md`, `RULES_COMPARISON_AND_MERGE_REPORT.md`, `docs/files/`, `SignalWeave_Documentation/` (via research subagent), and `EcoWatch_Full_Project_Documentation_v0.1/` (via research subagent; confirmed identical to `docs/EcoWatch/`). | — |
| 2026-11-17 | `e5d5dd6` (`prime`) | Cloned `Fredprime/EcoWatch`, created branch `prime` off `master`, added non-zip docs (`EcoWatch Agent Guide.md`, `RULES_COMPARISON_AND_MERGE_REPORT.md`, `PROJECT_TRACKING.md`, `files/`, `SignalWeave_Documentation/`, `EcoWatch_Full_Project_Documentation_v0.1/`), verified zero `.zip` files, and pushed to `origin/prime`. | 29 files in `docs/` |
| 2026-11-17 | GitHub API (`main`) | Switched to `main`, ran `scripts/protect-branches.sh` to enforce merge settings and branch protections on `main` and `master`, and switched back to `prime`. | Remote GitHub repo settings |
| 2026-11-17 | Docs update (`prime`) | Created single review doc (`docs/REVIEW_SUMMARY.md`), separate owner rules doc (`docs/OWNER_RULES.md`), and updated `docs/PROJECT_TRACKING.md` with full change history. | `docs/REVIEW_SUMMARY.md`, `docs/OWNER_RULES.md`, `docs/PROJECT_TRACKING.md` |

---

## 3. Items For Your Review Before Building `backend/`

Please confirm or adjust any of the following before we start Phase 1 (`backend/`):

1. **ADR alignment with repo infra (`docs/20_Technical_Decision_Records.md`):**
   - `compose.yaml`, `Makefile`, `CONTRIBUTING.md`, and `.github/workflows/ci.yml` already assume **Python 3.14 + FastAPI**, **PostgreSQL 16 + PostGIS 3.4**, **React + TypeScript**, and **Podman/Docker Compose**, while `ADR-014`–`ADR-016` still say `Proposed`.
   - **Action proposed:** Record updated ADRs marking `Python 3.14 + FastAPI`, `SQLAlchemy + Alembic`, `PostGIS 3.4`, and `React + TypeScript` as `Approved` before writing `backend/`.
2. **Naming boundary (`docs/EcoWatch Agent Guide.md` §8):**
   - **Action proposed:** Confirm `lower snake_case` for PostgreSQL tables/columns, `camelCase` for Python variables/JSON API payloads, `PascalCase` for classes/types, and `UPPER_SNAKE_CASE` for constants.
3. **Phase 1 auth, roles, and storage interfaces:**
   - **Action proposed:** Support both **anonymous** and **registered** contributors alongside staff/admin roles (per canonical `docs/05` and `FR-001`), using a local filesystem/S3-compatible storage interface and JWT/session auth interface so providers stay swappable.
4. **Original image preservation vs. client compression:**
   - **Action proposed:** Preserve uploaded originals untouched under restricted storage (`docs/09`); if client-side compression is used later on low-bandwidth connections, store and label it explicitly as a derivative rather than substituting it for an untouched original.

---

## 4. Reference Map

- **Progress & Backlog:** [PROJECT_TRACKING.md](PROJECT_TRACKING.md)
- **Owner Rules:** [OWNER_RULES.md](OWNER_RULES.md)
- **Agent Guide:** [EcoWatch Agent Guide.md](EcoWatch%20Agent%20Guide.md)
- **Canonical Baseline:** [START_HERE.md](START_HERE.md) (`00`–`24`)
- **Contributing & Branch Policy:** [../CONTRIBUTING.md](../CONTRIBUTING.md)
