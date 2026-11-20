# Release readiness

**Status:** prototype, not release-approved. This checklist records evidence still required before any deployment or live use. Passing local tests is not validation, certification or legal clearance. Branch under review: `feat/remaining-gaps-and-report-ux` (PR #40).

## Gates still open

- [ ] **Real-device offline/PWA validation.** Exercise queueing with no network, reconnect drain, idempotent media re-upload, service-worker update and storage/permission failures on the actual target phones and browsers; record device, OS and browser for each run. `npm run test:release` only checks built artefacts and route strings — it runs no browser, service worker or device.
- [ ] **Backup and restore.** Dump PostgreSQL (schema, PostGIS and pgvector data), uploads and deployment configuration; restore into a clean environment and verify the restored app. Recovery point/time objectives are still an owner decision.
- [ ] **Performance.** Measure on target hardware with representative bounded datasets: intake latency, correlation prefilter and scoring, page load and offline-queue growth. The build currently warns about a large lazy-loaded `WktMap` chunk. Design targets are not results.
- [ ] **Usability.** Keyboard and screen-reader passes, contrast checks, and plain-language review of public reporting, receipt/copy dialog and staff decision flows, with human sign-off.
- [ ] **Legal and governance sign-off.** Owner/legal review of Ghanaian data protection, environmental and evidence rules, copyright/licences, drone and cybersecurity requirements, plus retention/deletion schedule, consent and third-party package data practices.
- [ ] **Embedding model decision.** ADR-019 remains open. The provider contract only labels the current hashed-word method non-semantic and gates imported vectors from an operator-allowed internal source; it does not approve a trained model, wire an import job into the scan path, or make any accuracy claim. A scored run on a consented, human-reviewed set is still required.
- [ ] **Release decision.** Owner approves the reviewed branch and deployment plan. This document makes no production change.

## Local commands already used for verification

Run at the repository root unless a directory is shown. These are repeatable checks, not release gates.

```bash
.venv/bin/ruff check backend
# Prior branch check: All checks passed.

.venv/bin/pytest backend -q
# Prior branch check: 143 passed, 4 skipped (httpx/starlette TestClient deprecation warning).

cd backend && ../.venv/bin/python -m alembic heads
# Prior branch check: 0008_two_key_governance (head).
```

```bash
cd frontend
npm run lint
# Prior branch check: only the pre-existing WktMap set-state-in-effect warning.

npm test
# Prior branch check: 6 frontend core tests pass.

npm run build
# Prior branch check: passes; large-chunk warning on lazy-loaded WktMap.

npm run test:release
# Artefact and route-shell smoke check only; no real-device claims.
```

Targeted checks for the embeddings change:

```bash
.venv/bin/ruff check \
  backend/src/ecowatch/modules/correlation/embeddings.py \
  backend/tests/unit/test_correlation_embeddings.py
.venv/bin/pytest \
  backend/tests/unit/test_correlation_embeddings.py \
  backend/tests/integration/test_correlation_embeddings_store.py -q
git diff --check
```
