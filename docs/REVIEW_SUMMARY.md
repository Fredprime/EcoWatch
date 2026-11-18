# EcoWatch Review Summary

**Version:** 1.2  
**Last Updated:** 2026-11-18  
**Repository:** `Fredprime/EcoWatch`  
**Active Branch:** `prime`  
**Code Written:** Phase 1 Backend (`EcoWatch/backend/`) implemented (`frontend/` not started)

This is the single review document for checking progress, recent changes, and verification items for review.

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
- **Application folders:** Phase 1 `backend/` (`core/`, `api/`, 8 modules, Alembic `0001_phase1_initial_schema.py`, and unit/integration/security tests) is implemented on `prime`; `frontend/` does not exist yet.

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
| 2026-11-18 | `cd1c74b` (`prime`) | Added `docs/GLOBAL_AGENT_RULES_MERGED.md` and pushed to `origin/prime`. | `docs/GLOBAL_AGENT_RULES_MERGED.md` |
| 2026-11-18 | `068070f` (`prime`) | Removed `RULES_COMPARISON_AND_MERGE_REPORT.md` from repo and local `docs/`, and updated `PACKAGE_MANIFEST.json`, `REVIEW_SUMMARY.md`, and `PROJECT_TRACKING.md`. | `docs/RULES_COMPARISON_AND_MERGE_REPORT.md` (removed), `docs/PACKAGE_MANIFEST.json`, `docs/REVIEW_SUMMARY.md`, `docs/PROJECT_TRACKING.md` |
| 2026-11-18 | Phase 1 Build (`prime`) | Implemented full Phase 1 backend (`core/`, `api/`, `audit`, `identity`, `notifications`, `observations`, `collection`, `evidence`, `jobs`, `cases`, Alembic `0001_phase1_initial_schema.py`, and test suite) in `camelCase` Python/JSON mapped to `lower snake_case` DB columns; ran Ponytail Audit; added `ADR-029`; verified `pytest` (`16 passed, 1 skipped`) and `compileall`. | `backend/`, `docs/20_Technical_Decision_Records.md`, `docs/PROJECT_TRACKING.md`, `docs/REVIEW_SUMMARY.md` |
| 2026-11-18 | Phase 2 start (`phase2-correlation`) | Correlation engine and evaluation harness (23 tests). Phase 1 merged in; `pyproject.toml`/`__init__.py` conceded to Phase 1. Contract test pins the columns correlation reads from the real `0001` schema. Finding: `observation_sources` had no original-source identifier, so `FR-027` (repost detection) was unimplementable — added nullable `source_ref`. | `backend/src/ecowatch/correlation/`, `backend/tests/unit/test_correlation_*.py`, `backend/tests/unit/test_phase1_contract.py`, `backend/alembic/versions/0002_phase2_correlation.py` |

---

## 3. Items For Owner Review & Local Environment Completion

1. **Install missing dev/runtime packages in local `.venv` (already declared in `backend/pyproject.toml`):**
   - Host system Python lacks `ruff` and `python-multipart` (needed for HTTP multipart evidence uploads and `make lint`). Run `make venv && .venv/bin/pip install -e "backend[dev]"` (or inspect `backend/pyproject.toml`).
2. **Verify live PostgreSQL 16 + PostGIS 3.4 migrations & `SKIP LOCKED` worker test:**
   - Start DB container (`make up`), apply migrations (`cd backend && alembic upgrade head`), and run `ECOWATCH_RUN_POSTGIS_TESTS=1 .venv/bin/pytest -m postgis`.
3. **Run Ruff lint & CI verification:**
   - Run `make lint` (`ruff check backend`) and `make test`.
4. **Formal ADR status alignment (`docs/20_Technical_Decision_Records.md`):**
   - `ADR-029` records the Phase 1 build and `camelCase` naming boundary (`Approved 2026-11-18`); formally promote `ADR-014`–`ADR-016` and `ADR-026`–`ADR-028` statuses in `docs/20_Technical_Decision_Records.md` + `docs/08` when ready to merge `prime -> master`.

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
