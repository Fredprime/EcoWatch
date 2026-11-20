# Phase 3 Progress Log

**Last updated:** 2026-11-20
**Purpose:** Durable, curated record of the Phase 3 integration work so a future
session can resume without re-discovering decisions, commands, results and open
items. Read this before making further Phase 3 changes.

> This is a curated progress log, not a byte-for-byte chat transcript. The
> coding agent has no persistent memory between sessions; this file and the
> pointer in `AGENTS.md` are the continuity mechanism.

## Resume checklist

1. Read `AGENTS.md`, then this file.
2. `git status -sb` and `git log --oneline -5`.
3. Confirm the current branch and working tree. The active follow-up branch is
   `feat/remaining-gaps-and-report-ux`; older Phase 3 work landed on `feat/Randy_Branch`.
4. Check the current PR state from `gh pr list --head <branch> --base master` rather than
   assuming an old PR number. PR #9 (`feat/Randy_Branch`) is historical and merged.
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
- Recovery verification requires approved criteria and two role-qualified, distinct
  human approvers: `environmental_specialist` plus `organisation_admin`, with neither
  the intervention owner and the acting caller as one of the two keys (ADR-041).
- Publication requires the same two-key approval and stores both approvers (ADR-041).
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
- `SYSTEM_ADMIN`: read/operational permissions only; no
  `VERIFICATION_WRITE`, `VERIFICATION_APPROVE` or `PUBLICATION_WRITE` (ADR-041)

## Alembic / migration state

- Phase 3 migration: `backend/alembic/versions/0003_phase3_schema.py`
- Historical Phase 3 revision at first merge: `0003_phase3_schema`, down revision
  `0002_phase2_correlation`.
- Current head on this branch: `0008_two_key_governance`; the full chain is
  `0001_phase1_initial_schema -> 0002_phase2_correlation -> {0003_phase2_clusters,
  0003_phase3_schema} -> 0004_merge_phase2_phase3 -> 0005_phase2_embeddings ->
  0006_evidence_upload_idempotency -> 0007_token_revocation -> 0008_two_key_governance`.
- The Phase 3 migration was originally `0002_phase3_schema.py`; renamed after merging
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

## Current state at 2026-11-19 (superseded by the 2026-11-20 update above)

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

### Update 2026-11-19 — Phase 3 merged; remaining backend work in flight

- Phase 3 is **merged into `master`** and must not be redone: PR #9
  (`c3aafd4`, initial Phase 3) followed by PR #21 (`3a13520`, Phase 3 HTTP API).
  The paragraph above records the state at the time it was written; the branch
  `feat/Randy_Branch` work it describes has since landed.
- Separate streams also merged: pgvector PR #19, frontend PR #20, and the
  earlier Phase 2 PRs #10/#11/#12/#17/#18.
- **Current active branch:** `backend/remaining-work` off `master`, with three
  commits pending PR into `master`: `c7218a7` (FR-057 governance erasure/export,
  ADR-034), `c8bd4cc` (ADR-031 case-side actions, authority clarified by
  ADR-035), and `67e9c38` (ADR-036 Phase 2 contract hardening).
- Verification on that branch: `ruff check backend` clean; single Alembic head
  `0006_evidence_upload_idempotency` with valid upgrade/downgrade SQL;
  `pytest backend -q` → 123 passed / 4 skipped.
- The frontend is already merged and verified; keep the phone-check tunnel
  available and do not fold frontend changes into the backend PR.

### Update 2026-11-20 — remaining gaps, two-key governance and report UX

- **Current branch:** `feat/remaining-gaps-and-report-ux` off `master` (`ca450a9`).
  The detailed work list is `docs/REMAINING_WORK_TODO.md`; PR **#40** into `master` is open
  for owner review. Earlier Phase 3 branches and PRs remain historical and must not be redone.
- **Why this branch exists:** the owner reported that contributors could not copy their tracking
  ID and wanted a confirmation popup after a successful report. While fixing those, the code was
  treated as the source of truth for the remaining governance gaps; stale documentation was
  updated afterwards (ADR-041 and ADR-042).
- **Report UX:** `frontend/src/components/CopyButton.tsx` copies via the clipboard API with a
  hidden-textarea fallback; `ReceiptDialog.tsx` is a labelled native `<dialog>` showing the
  server receipt, copyable tracking reference, precision fields and Done/Track actions. The
  report receipt card and tracking lookup page also carry copy buttons. A front-end test renders
  both controls and asserts the dialog/receipt markup.
- **Two-key governance (ADR-041):** recovery verification and publication now require
  `specialistApproverUserId` and `authorityApproverUserId`, role-qualified in the organisation,
  distinct, neither the intervention owner, with the acting caller as one key. Both approvers
  and `twoKeyApprovedAt` are stored and audited. `system_admin` keeps read/operational access
  but loses scientific write/approve/publication grants. Intervention approval requires an
  uninvolved `organisation_admin`; the proposer is recorded; the `recovery_verified` transition
  accepts only a final two-key assessment for the same intervention.
- **Admin lifecycle (ADR-042):** `GET /users`, `PATCH /users/{userId}` and
  `PATCH /organisations/{orgId}` are `system_admin`-only, audited, omit password hashes, refuse
  self-lockout, and are exposed in the Administration page as user/org activate-deactivate
  controls.
- **Migration:** `0008_two_key_governance` is the single head (`down_revision`
  `0007_token_revocation`). It adds `proposed_by_user_id` to interventions and specialist,
  authority and two-key timestamp columns to verification assessments and publications.
- **Breaking request contract:** `RecoveryVerificationRequest` and `PublishSummaryRequest` now
  require the two approver UUID fields. Old clients must be updated before redeploying the API.
- **Verification on this branch (2026-11-20):**

  ```bash
  .venv/bin/ruff check backend
  # All checks passed.

  .venv/bin/pytest backend -q
  # 143 passed, 4 skipped, 1 warning in 230.40s
  # warning is the pre-existing httpx/starlette TestClient deprecation.

  cd backend && ../.venv/bin/python -m alembic heads
  # 0008_two_key_governance (head)

  cd frontend
  npm run lint
  # Pre-existing src/components/WktMap.tsx set-state-in-effect warning only.

  npm test
  # 6 frontend core tests pass.

  npm run build
  # Passes.
  ```

- **Not claimed:** no analytical engine, malware scanner, trained semantic model, database-level
  audit immutability, controlled-vocabulary admin API, case `field_verified` two-key gate,
  token-revocation purge job, real-device offline validation or release-gate sign-off. These stay
  in `docs/REMAINING_WORK_TODO.md` §4.

## Open items

1. ~~Obtain owner approval for the Phase 3 permissions matrix.~~ Resolved by
   merge of PR #21 into `master`.
2. ~~Obtain owner approval for recovery-verification criteria.~~ Resolved by
   merge of PR #21 into `master`.
3. ~~Review and approve the Phase 3 route paths/payload shapes in
   `backend/phase3Integration.md` §11 as the stable API contract.~~ Resolved by
   merge of PR #21 into `master`.
4. Run the PostGIS migration test locally on a machine with Docker/PostgreSQL;
   CI already passes it.
5. Decide whether to fix the pre-existing Phase 1 `ix_audit_events_target`
   Alembic drift.
6. ~~Decide whether to commit/push the local documentation and API changes.~~
   Phase 3 API changes landed in PR #21; the documentation was committed.
7. **Current PR (`backend/remaining-work` → `master`) owner decisions:** confirm
   ADR-034's tombstone-only reading of FR-057 erasure (originals retained per
   hard boundary), ADR-035's single-actor reading of case-action authority, and
   the ADR-036 scope boundary (no WebSocket, no server-side sync-state column).
8. **Current follow-up PR #40 (`feat/remaining-gaps-and-report-ux` → `master`) owner decisions:**
   confirm the breaking request contract in ADR-041 (both approver UUIDs are required), that
   `system_admin` is no longer a scientific approver, and that admin lifecycle changes in
   ADR-042 are audited UI conveniences over server-side enforcement. Owner merges and redeploys;
   no production action is taken from this branch.

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
