# EcoWatch Review Summary

**Version:** 1.1  
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
| 2026-11-17 | `ccea786` (`prime`) | Created single review doc (`docs/REVIEW_SUMMARY.md`), separate owner rules doc (`docs/OWNER_RULES.md`), and updated `docs/PROJECT_TRACKING.md` with full change history. | `docs/REVIEW_SUMMARY.md`, `docs/OWNER_RULES.md`, `docs/PROJECT_TRACKING.md` |
| 2026-11-17 | Docs update (`prime`) | Added three-phase backend architecture blueprint (`docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md`) covering all 26 tables, 58 FRs, 10 NFRs, and 11 modules; added `ADR-026`; updated `OWNER_RULES.md`, `PROJECT_TRACKING.md`, and `REVIEW_SUMMARY.md` (zero code written). | `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md`, `docs/20_Technical_Decision_Records.md`, `docs/OWNER_RULES.md`, `docs/PROJECT_TRACKING.md`, `docs/REVIEW_SUMMARY.md` |
| 2026-11-17 | Docs hygiene (`Tazor`) | Renamed agent guide to `docs/AGENT_GUIDE.md`; added root `AGENTS.md`; archived superseded v0.1 and SignalWeave packages with `SUPERSEDED.md`; added `DECISION_ID_CROSSWALK.md`; proposed `PERMISSIONS_MATRIX.md` with `ADR-027`; regenerated `PACKAGE_MANIFEST.json` v1.1. | `AGENTS.md`, `docs/AGENT_GUIDE.md`, `docs/archive/`, `docs/files/DECISION_ID_CROSSWALK.md`, `docs/PERMISSIONS_MATRIX.md`, `docs/PACKAGE_MANIFEST.json` |
| 2026-11-17 | Backend plan v1.1 (`Tazor`) | Review applied to `BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md`: full FR/NFR traceability table (previously 37/58 FR and 7/10 NFR by ID while claiming 58/58 and 10/10); `processing_jobs` moved to Phase 1; organisation scoping, anonymous tracking-code retrieval, scan policy, `methods`/`units`/`clarification_requests`/`publications`/`correlation_embeddings`; rejected-pair index; Phase 2 evaluation acceptance split into two achievable routes; verification criteria, raster pipeline and prioritisation method named as missing; cross-cutting concerns expanded; eight pre-Phase-1 decisions listed. `ADR-028` added. Zero code. | `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md`, `docs/20_Technical_Decision_Records.md` |
| 2026-11-17 | PR #4 sync (`Tazor`) | `prime` conflicted after PR #2 was squash-merged. Merged `master` into `prime`, resolved 5 doc conflicts toward `prime` (master held no unique content other than the duplicates, verified by diffing against `aa973a9`), and deleted the three duplicate paths the merge resurrected. Verified the resulting tree is byte-identical to the pre-merge `prime` tree, so nothing was lost or silently reverted. | `docs/20_Technical_Decision_Records.md`, `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md`, `docs/OWNER_RULES.md`, `docs/PROJECT_TRACKING.md`, `docs/REVIEW_SUMMARY.md`, 3 duplicate trees |
| 2026-11-18 | Phase 2 start (`phase2-correlation`) | Built the correlation engine only, because it is the one part of Phase 2 that does not depend on Phase 1 existing: pairwise scoring over four optional signals, missing-signal handling, repost/source-dependence flagging, ranking with an explicit ambiguity flag, and a precision/recall harness. 23 tests, `ruff` clean. Phase 2's own tables, retrieval SQL, worker types and review API are listed as blocked on Phase 1 rather than stubbed. | `backend/pyproject.toml`, `backend/src/ecowatch/correlation/`, `backend/tests/`, `docs/PHASE2_CORRELATION.md` |

---

## 3. Items For Your Review Before Building `backend/`

Please confirm or adjust any of the following before we start Phase 1 (`backend/`):

1. **ADR alignment with repo infra (`docs/20_Technical_Decision_Records.md`):**
   - `compose.yaml`, `Makefile`, `CONTRIBUTING.md`, and `.github/workflows/ci.yml` already assume **Python 3.14 + FastAPI**, **PostgreSQL 16 + PostGIS 3.4**, **React + TypeScript**, and **Podman/Docker Compose**, while `ADR-014`–`ADR-016` still say `Proposed`.
   - **Action proposed:** Record updated ADRs marking `Python 3.14 + FastAPI`, `SQLAlchemy + Alembic`, `PostGIS 3.4`, and `React + TypeScript` as `Approved` before writing `backend/`.
2. **Naming boundary (`docs/AGENT_GUIDE.md` §8):**
   - **Action proposed:** Confirm `lower snake_case` for PostgreSQL tables/columns, `camelCase` for Python variables/JSON API payloads, `PascalCase` for classes/types, and `UPPER_SNAKE_CASE` for constants.
3. **Phase 1 auth, roles, and storage interfaces:**
   - **Action proposed:** Support both **anonymous** and **registered** contributors alongside staff/admin roles (per canonical `docs/05` and `FR-001`), using a local filesystem/S3-compatible storage interface and JWT/session auth interface so providers stay swappable.
4. **Original image preservation vs. client compression:**
   - **Action proposed:** Preserve uploaded originals untouched under restricted storage (`docs/09`); if client-side compression is used later on low-bandwidth connections, store and label it explicitly as a derivative rather than substituting it for an untouched original.

---

## 4. Reference Map

- **Three-Phase Backend Blueprint:** [BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md](BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md)
- **Permission Matrix (Proposed, ADR-027):** [PERMISSIONS_MATRIX.md](PERMISSIONS_MATRIX.md)
- **Decision-ID Crosswalk:** [files/DECISION_ID_CROSSWALK.md](files/DECISION_ID_CROSSWALK.md)
- **Agent entry point:** [../AGENTS.md](../AGENTS.md)
- **Progress & Backlog:** [PROJECT_TRACKING.md](PROJECT_TRACKING.md)
- **Owner Rules:** [OWNER_RULES.md](OWNER_RULES.md)
- **Agent Guide:** [AGENT_GUIDE.md](AGENT_GUIDE.md)
- **Canonical Baseline:** [START_HERE.md](START_HERE.md) (`00`–`24`)
- **Contributing & Branch Policy:** [../CONTRIBUTING.md](../CONTRIBUTING.md)
