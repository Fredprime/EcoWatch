# Phase 2 — work list and dependencies

**Branch:** `phase2-correlation` · **Owner of Phase 2:** this agent · **Phase 1 and 3:** team
**Companion:** `docs/PHASE2_CORRELATION.md` (what is built today and the Phase 1 contract)

Rule for this list: nothing waits unless it physically cannot proceed. T0 planned an executable mirror of the Phase 1 contract so work could start before Phase 1 landed; Phase 1 (`3713211`) landed first, so the contract is now read from the real migration instead of a fixture.

Sizes are S / M / L, not hours.

## 0. Unblocking work (do first)

| # | Task | Depends on | Size | Status |
|---|---|---|---|---|
| T0 | `phase1_contract.sql` test fixture: minimal `observations`, `observation_sources`, `processing_jobs`, `audit_events` matching the agreed contract, plus a test that fails loudly if a real migration contradicts it | nothing | S | **superseded** — Phase 1 landed before the fixture was needed; the contract is now pinned by `test_correlation_postgis.py` and the SQLite flow tests. |
| T0b | Retrieval policy module: per-category temporal windows, radius per category, "no location → tighter time window" rule, rejected-pair exclusion | nothing | S | **done** — `policy.py`; per-category radius and window, tighter window when there is no location, tested. |

## 1. Storage (needs Phase 1 `observations` to run, developed against T0)

| # | Task | Depends on | Size | Status |
|---|---|---|---|---|
| T1 | `evidence_relationships` migration: a/b in canonical order, task type, score, component scores, method version, reason codes, status (`suggested`/`accepted`/`rejected`/`ambiguous`/`merged`), created/decided by and at | `observations` | M | **done** — migration `0002`, constraints proven on real PostgreSQL. |
| T2 | Rejected-pair guarantee: unique constraint on the canonical pair so rejection is an index probe and re-rejection is idempotent | T1 | S | **done** — `CHECK` + `UNIQUE` in migration `0002`. |
| T3 | `correlation_embeddings` + vector column + index (one row per observation, model version, input hash; skip re-embed when unchanged) | **owner decision made 2026-11-18: pgvector approved** | M | **unblocked, not built** — ADR-030; add the table and embedding job behind the approved pgvector choice. |
| T4b | `ST_DWithin` retrieval path + GiST usage on PostgreSQL | T1, PostGIS | M | **done** — `ST_DWithin` on geography in `repository.py`, on the GiST index Phase 1 created; proven on live PostgreSQL. |

## 2. Correlation

| # | Task | Depends on | Size | Status |
|---|---|---|---|---|
| T4 | Candidate retrieval SQL: `ST_DWithin` + temporal window + category pre-filter, excludes rejected pairs, applies lower-context bounds when location is absent, always `LIMIT` | T0, T1, PostGIS | M | **done** — bounded, org-scoped retrieval; distance filtered by `ST_DWithin` on PostgreSQL, in Python on SQLite (test dialect only). |
| T5 | Detector wiring: duplicate, same-event, repost/source-dependency (`FR-027`), cross-case relevance — each with its own thresholds and reason codes, all feeding one `PairSuggestion` shape | T1, T4 | M | **done** — `detectors.py`: one task per pair, `source_dependency` > `duplicate` > `same_event`, nothing below the review threshold. `cross_case` is deliberately absent: ADR-031 gives it to the cases module. |
| T6 | Provisional clusters: staff-only, never counted as cases, never transitively merged, ambiguity surfaced not broken | T1, T5 | M | **done (container only)** — `correlation_clusters` + members, one cluster per report, created on scan, staff-only. No auto-merge, so A~B and B~C stay separate; `merge`/`split` are not built. |
| T7 | Background job types `correlation_score` and `embedding_backfill`: idempotent, bounded retries, dead-letter state, intake latency never includes scoring (`NFR-001`) | **`processing_jobs` + worker** | M | **partly done** — `correlation.scan` queued automatically on intake and on demand, with bounded retries and a dead-letter state; `embedding_backfill` remains to build now that pgvector is approved. |
| T12 | Re-scan on observation corrections and evidence uploads | T1, Phase 1-owned modules | S | **done** — both triggers enqueue `correlation.scan` in the same transaction as the change; verified by two integration tests. |

## 3. Review boundary

| # | Task | Depends on | Size | Status |
|---|---|---|---|---|
| T8 | Review API: `accept`, `reject`, `mark_ambiguous`, `promote_to_case`, `merge`, `split` — reversible by new action, never by edit | T1, RBAC | M | **partly done** — accept / reject / ambiguous / reopen implemented and audited; case-side actions are owned by the cases module under ADR-031. |
| T9 | Separation of duties: a reviewer cannot decide on their own submission; cross-organisation reads return 404, not 403 | RBAC, org scoping | S | **done** — reuses `ensure_not_self_submitted`; cross-org returns 404. |
| T10 | Audit integration: every review decision writes an `audit_events` row in the same transaction | audit helper | S | **done** — same transaction as the decision, verified by test. |

## 4. Acceptance

| # | Task | Depends on | Size | Status |
|---|---|---|---|---|
| T11 | Scored run of the harness on a labelled set and a written result. No accuracy claim beyond what the run shows | **owner decision made 2026-11-18: smoke-test only** | S | **done (smoke test)** — `backend/tests/evaluation/test_correlation_smoke.py` proves scoring-to-evaluation wiring on temporary synthetic fixtures; no accuracy claim and no real-report result. |

## Not mine — hand back

| Item | Why |
|---|---|
| Split-phase intake contract (`FR-052`), offline error taxonomy, `notifications` + optional WebSocket | Plan §2.1 lists these under Phase 2, but they are inside the `collection` and `notifications` modules that Phase 1 owns. Two people editing one module is worse than one person doing it slightly later. |

---

## What Phase 1 answered, and the three gaps it left

Answered by reading `0001_phase1_initial_schema.py` rather than by asking:

- `observations.observed_at` is `timestamptz` — aware datetimes throughout, no guessing an offset.
- `observations.location` is PostGIS `geography(Point,4326)`; `geography_to_text_expr` already existed for the SQLite/PostgreSQL split.
- `processing_jobs` declares job type as a string, so `correlation.scan` registers without touching Phase 1's schema.
- RBAC is `Permission` + `ROLE_PERMISSIONS` deny-by-default; audit is `record_audit_event`, same-transaction.
- No category lookup table: `observation_type` is a string. Correlation treats it as an opaque label.

Three gaps that blocked Phase 2 outright, now closed from this side:

| Gap | Why it blocked | Closed by |
|---|---|---|
| No `correlation:*` permissions | correlation could not authorise anything without widening an existing permission, which would have leaked access | `CORRELATION_READ` / `CORRELATION_REVIEW` added to `permissions.py` |
| No `source_ref` anywhere | `FR-027` repost / shared-source detection had no way to tell two reports from one original source, so every repost scored as independent | nullable indexed column on `observations` (migration `0002`) |
| `observation_sources` is PII-only | reusing it for provenance would put correlation reads next to contributor identity | not reused; `source_ref` lives on `observations` |

## Owner decisions, 2026-11-18

1. **pgvector: approved.** T3 and semantic similarity proceed with `pgvector` in the existing PostgreSQL service; `token_similarity` stays as the labelled keyword fallback. Recorded in ADR-030.
2. **Evaluation route: smoke-test only.** T11 proves the harness mechanics on temporary fixtures. No accuracy number is reported and no claim is made about real reports.
3. **Case-side actions: cases module owns them.** `cross_case`, `promote_to_case`, `merge` and `split` use the two-key authority rules in `docs/PERMISSIONS_MATRIX.md` §4. Correlation records suggestions and clusters; it does not decide case state. Recorded in ADR-031.
4. **Re-scan triggers: corrections and evidence uploads.** Both enqueue another `correlation.scan` for the affected observation. They live in the Phase 1-owned `observations` and `evidence` modules, so each hook is a separate branch and PR.
