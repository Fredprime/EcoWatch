# Phase 3 Progress Log

**Last updated:** 2026-11-19
**Purpose:** Durable, curated record of the Phase 3 integration work so a future
session can resume without re-discovering decisions, commands, results and open
items. Read this before making further Phase 3 changes.

> This is a curated progress log, not a byte-for-byte chat transcript. The
> coding agent has no persistent memory between sessions; this file and the
> pointer in `AGENTS.md` are the continuity mechanism.

## Resume checklist

1. Read `AGENTS.md`, then this file.
2. `git status -sb` and `git log --oneline -5`.
3. Confirm the branch is `feat/Randy_Branch` and the working tree is understood.
4. Check PR #9 state:
   `https://github.com/Fredprime/EcoWatch/pull/9`.
5. Re-run the verification commands in the "Verification" section before making
   new claims about the branch.

## Repository and delivery state

- Repository: `C:\Users\RANDY\Desktop\IFestivalProject\EcoWatch`
- Remote: `https://github.com/Fredprime/EcoWatch.git`
- Working branch: `feat/Randy_Branch`
- PR base: `master`
- PR `#9` is **closed and merged**: `master` contains
  `c3aafd4 feat(backend): Phase 3 - catalogue, intelligence, prioritisation,
  interventions, verification (#9)`.
- `origin/master` was pulled into `feat/Randy_Branch` on 2026-11-19 as merge
  `aaaf3bf`; it also brought in `#14` (Phase 1 + Phase 2 integration),
  `#19` (correlation pgvector/semantic prefilter) and `#20` (frontend site).
- No further merge into `prime` or `main` was performed, per owner instruction.
- CI on `52ab50e`: all three jobs succeeded.
  - `infra / compose + postgis`
  - `backend / lint + test`
  - `frontend / build`

### Relevant commits

| Commit | Meaning |
| --- | --- |
| `feeeb8b` | Initial Phase 3 backend integration commit (`phase3-integration` branch) |
| `3f1e6bf` | Earlier merge of old `origin/master` into `feat/Randy_Branch` |
| `080ba8a` | `Prime (#5)` — latest `master` with backend Phase 1 + Phase 2 |
| `52ab50e` | Merge resolving Phase 3 against `master` and the Phase 2 migration chain |

### Branches

- `feat/Randy_Branch`: integration/PR branch.
- `phase3-integration`: local branch still at `feeeb8b`; not the PR branch.
- `origin/master`: now an ancestor of `feat/Randy_Branch`; PR should remain
  mergeable unless `master` advances again.

## User requests and outcomes

1. Integrate the locally built Phase 3 backend into the repository.
   - Ported all Phase 3 modules to Phase 1 conventions.
2. Push the work to GitHub and open a PR into `master`.
   - Pushed `feeeb8b`; created PR #9 via the GitHub API using stored git
     credentials because `gh` is not installed.
3. Resolve the GitHub "conflicts must be resolved" message.
   - Merged latest `origin/master` (`080ba8a`) and resolved 17 conflicts.
4. Create the pull request.
   - PR #9 already existed; confirmed and used it rather than duplicating.
5. Verify it works locally before full local review and resend the PR details.
   - Ran backend lint/tests, Alembic checks, and frontend lint/build; updated
     PR #9 body with the verification results.
6. Save chat history/progress so the work can be resumed and monitored.
   - Added this log and a pointer from `AGENTS.md`.

## Phase 3 scope

Phase 3 adds environmental intelligence, evidence-honest prioritisation,
interventions and verification.

### Modules

- `backend/src/ecowatch/modules/phase3Contracts.py` — shared RBAC, tenant scope,
  validation and audit helpers.
- `backend/src/ecowatch/modules/catalogue/` — dataset catalogue.
- `backend/src/ecowatch/modules/intelligence/` — entities, relationships,
  analyses, prediction gate.
- `backend/src/ecowatch/modules/prioritisation/` — prioritisation factors and
  scoring.
- `backend/src/ecowatch/modules/interventions/` — intervention lifecycle.
- `backend/src/ecowatch/modules/verification/` — measurements, verification,
  publication.

### Evidence-first guarantees (do not weaken)

- Missing prioritisation factors are reported, never imputed.
- Composite ranks require a method reference and `rank_is_not_severity=true`.
- Prediction is blocked without a validated model, validation report,
  representative data and target.
- Milestones derive activity status only, never environmental outcome.
- Recovery verification requires approved criteria and an environmental
  specialist reviewer.
- Activity, output, environmental outcome and recovery are separate concepts.
- No agent output may declare a pollution source, illegal activity, causal link,
  harm, `field verified` or `recovery verified`.

## Architecture decisions

- Phase 1 conventions win over the earlier camelCase-only Phase 3 draft.
- Classes: `PascalCase`.
- Functions/methods, DB tables/columns, enum values: `snake_case`.
- Python attributes/parameters and JSON API payloads: `camelCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Use portable SQLAlchemy types: `Uuid(as_uuid=True)`, `JSON`, `Numeric`,
  `GeographyType`; no `geoalchemy2`, `JSONB` or PostgreSQL-only UUID.
- Use Phase 1 `Base`, mixins, sync `Session`, `Principal`, `Permission`, `Role`,
  `DomainError`/`ErrorCode`, and `AuditService.record_event`.
- PostGIS-specific indexes are conditional so SQLite tests still run.

## Shared Phase 1 files extended

### `backend/src/ecowatch/core/errors.py`

Re-applied on top of the `master` version:

- `PREDICTION_BLOCKED`
- `RECOVERY_NOT_VERIFIABLE`

### `backend/src/ecowatch/modules/identity/permissions.py`

Re-applied on top of the `master` version:

- `CATALOGUE_WRITE`
- `INTELLIGENCE_WRITE`
- `INTELLIGENCE_REVIEW`
- `PRIORITISATION_WRITE`
- `INTERVENTION_WRITE`
- `VERIFICATION_WRITE`
- `VERIFICATION_APPROVE`
- `PUBLICATION_WRITE`

Role grants:

- `REVIEWER`: `INTELLIGENCE_REVIEW`
- `INVESTIGATOR`: `INTELLIGENCE_WRITE`, `INTELLIGENCE_REVIEW`,
  `PRIORITISATION_WRITE`, `VERIFICATION_WRITE`
- `ENVIRONMENTAL_SPECIALIST`: all eight Phase 3 permissions
- `INTERVENTION_MANAGER`: `INTERVENTION_WRITE`, `VERIFICATION_WRITE`
- `ORGANISATION_ADMIN`: all eight Phase 3 permissions
- `SYSTEM_ADMIN`: all eight Phase 3 permissions

## Alembic / migration state

- Phase 3 migration: `backend/alembic/versions/0003_phase3_schema.py`
- Revision: `0003_phase3_schema`
- Down revision: `0002_phase2_correlation`
- Chain:
  `base -> 0001_phase1_initial_schema -> 0002_phase2_correlation -> 0003_phase3_schema (head)`
- The migration was originally `0002_phase3_schema.py`; renamed after merging
  Phase 2 from `master`.
- `backend/alembic/env.py` imports all Phase 3 models and also imports
  `EvidenceRelationship` from the Phase 2 correlation module so Alembic sees
  Phase 2 metadata and does not report false drift.

## Conflict resolution record

Resolved during the merge of `origin/master` (`080ba8a`) into
`feat/Randy_Branch`.

Took the `master` version for these shared/Phase 1/Phase 2 files:

- `backend/alembic.ini`
- `backend/alembic/versions/0001_phase1_initial_schema.py`
- `backend/pyproject.toml`
- `backend/src/ecowatch/api/router.py`
- `backend/src/ecowatch/core/config.py`
- `backend/src/ecowatch/core/schemas.py`
- `backend/src/ecowatch/modules/collection/schemas.py`
- `backend/src/ecowatch/modules/jobs/worker.py`
- `backend/src/ecowatch/modules/observations/models.py`
- `backend/src/ecowatch/modules/observations/schemas.py`
- `backend/tests/conftest.py`
- `backend/tests/unit/test_core_and_rbac.py`
- `docs/PROJECT_TRACKING.md`
- `docs/REVIEW_SUMMARY.md`

Then re-applied Phase 3 additions:

- Error codes in `backend/src/ecowatch/core/errors.py`.
- Phase 3 permissions/grants in
  `backend/src/ecowatch/modules/identity/permissions.py`.
- Phase 3 and Phase 2 model imports in `backend/alembic/env.py`.

## Tests and test layout

- `backend/tests/unit/phase3/test_phase3Rules.py` — Phase 3 rule, RBAC and
  service smoke tests.
- The old `testPhase3Rules.py` name was removed.
- PostGIS tests are marked and skipped unless
  `ECOWATCH_RUN_POSTGIS_TESTS=1` and a database is available.

## Verification

Environment caveats:

- Local Python is 3.13; `backend/pyproject.toml` requires Python `>=3.14`.
- Use the temporary venv:
  `C:\Users\RANDY\AppData\Local\Temp\opencode\phase3venv`
- Run from `backend` with `PYTHONPATH=src` for direct test execution.
- Docker and PostgreSQL are not installed on this machine, so PostGIS tests
  cannot run locally.
- `npm audit` reports one high-severity dependency issue (pre-existing; not
  addressed by this work).

Commands and results at `52ab50e`:

```powershell
# From repository root
& "C:\Users\RANDY\AppData\Local\Temp\opencode\phase3venv\Scripts\python.exe" -m ruff check backend
# All checks passed.

& "C:\Users\RANDY\AppData\Local\Temp\opencode\phase3venv\Scripts\python.exe" -m compileall -q backend/src backend/alembic backend/tests
# Passed.

$env:PYTHONPATH="backend/src"
& "C:\Users\RANDY\AppData\Local\Temp\opencode\phase3venv\Scripts\python.exe" -m pytest backend -q
# 65 passed, 2 skipped, 1 warning.
```

Alembic on temporary SQLite:

- `alembic upgrade head` — passed.
- `alembic downgrade base` — passed.
- `alembic check` — no Phase 2 or Phase 3 drift.
- Remaining (pre-existing Phase 1) issue:
  `Detected removed index 'ix_audit_events_target' on 'audit_events'`.

Frontend (`frontend/`):

```powershell
npm ci
npm run lint
npm run build
```

All passed.

GitHub CI on `52ab50e`:

- `infra / compose + postgis` — success.
- `backend / lint + test` — success (ran the PostGIS tests in CI).
- `frontend / build` — success.

Verification after the HTTP API work (2026-11-19):

```powershell
& "C:\Users\RANDY\AppData\Local\Temp\opencode\phase3venv\Scripts\ruff.exe" check backend
# All checks passed.

$env:PYTHONPATH="...\phase3venv\Lib\site-packages;backend\src"
python -m pytest backend -q
# 112 passed, 4 skipped, 1 warning (httpx/TestClient deprecation only).
```

The venv on this machine has no `python.exe` launcher, so tests were run with the
system Python 3.13 plus `PYTHONPATH` pointed at the venv's `site-packages` and
`backend/src`. The 4 skips are PostGIS-gated tests; Docker/PostgreSQL is still
unavailable locally.

## Current state (2026-11-19)

- PR #9 is merged into `master` as `c3aafd4`; `feat/Randy_Branch` has pulled the
  latest `master` through merge `aaaf3bf`.
- Phase 3 now has a complete HTTP layer: five `schemas.py`, five `router.py`,
  all 24 routes mounted in `backend/src/ecowatch/api/router.py`, and six
  end-to-end endpoint integration tests in
  `backend/tests/integration/test_phase3_endpoints.py`.
- All five Phase 3 services were corrected to commit their own transactions.
  Without this, the request-scoped session closed without committing and every
  Phase 3 HTTP write was rolled back. This matches the Phase 1 service pattern.
- Verification after the changes: `ruff check backend` clean;
  `pytest backend -q` → 112 passed, 4 skipped.
- Local worktree still contains uncommitted changes: `AGENTS.md` modified,
  `docs/PHASE3_PROGRESS_LOG.md` untracked, plus the new API files and doc edits.
  Nothing was committed or pushed in this session.

## Open items

1. Obtain owner approval for the Phase 3 permissions matrix.
2. Obtain owner approval for recovery-verification criteria.
3. Review and approve the Phase 3 route paths/payload shapes in
   `backend/phase3Integration.md` §11 as the stable API contract.
4. Run the PostGIS migration test locally on a machine with Docker/PostgreSQL;
   CI already passes it.
5. Decide whether to fix the pre-existing Phase 1 `ix_audit_events_target`
   Alembic drift.
6. Decide whether to commit/push the local documentation and API changes (no
   commit was made automatically).

## Relevant files

- `backend/phase3Integration.md` — integration contract and verification record.
- `backend/alembic/versions/0003_phase3_schema.py` — Phase 3 migration.
- `backend/alembic/env.py` — Phase 1/2/3 model imports.
- `backend/src/ecowatch/core/errors.py` — Phase 3 error codes.
- `backend/src/ecowatch/modules/identity/permissions.py` — Phase 3 RBAC.
- `backend/src/ecowatch/modules/phase3Contracts.py` — shared helpers.
- `backend/src/ecowatch/modules/*/schemas.py` — five Phase 3 boundary schema files.
- `backend/src/ecowatch/modules/*/router.py` — five Phase 3 FastAPI routers.
- `backend/tests/integration/test_phase3_endpoints.py` — end-to-end endpoint tests.
- `backend/tests/unit/phase3/test_phase3Rules.py` — Phase 3 rule tests.
- `docs/PHASE3_PROGRESS_LOG.md` — this file.
- `AGENTS.md` — entry point pointing to this log.

## How to continue in a new session

Start the session with:

> Read `AGENTS.md` and `docs/PHASE3_PROGRESS_LOG.md`, then check the branch,
> PR #9 and the verification section before continuing Phase 3.

Do not assume the log is still current: verify `git status`, `git log`,
`origin/master` and the PR state first.
