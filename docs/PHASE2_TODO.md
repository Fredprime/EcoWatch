# Phase 2 — work list and dependencies

**Branch:** `phase2-correlation` · **Owner of Phase 2:** this agent · **Phase 1 and 3:** team
**Companion:** `docs/PHASE2_CORRELATION.md` (what is built today and the Phase 1 contract)

Rule for this list: nothing waits unless it physically cannot proceed. Where the only blocker is a Phase 1 table, the work is developed and tested against `backend/tests/sql/phase1_contract.sql` — an executable mirror of the contract — so the real table is a swap, not a restart.

Sizes are S / M / L, not hours.

## 0. Unblocking work (do first)

| # | Task | Depends on | Size |
|---|---|---|---|
| T0 | `phase1_contract.sql` test fixture: minimal `observations`, `observation_sources`, `processing_jobs`, `audit_events` matching the agreed contract, plus a test that fails loudly if a real migration contradicts it | nothing | S |
| T0b | Retrieval policy module: per-category temporal windows, radius per category, "no location → tighter time window" rule, rejected-pair exclusion | nothing | S |

## 1. Storage (needs Phase 1 `observations` to run, developed against T0)

| # | Task | Depends on | Size |
|---|---|---|---|
| T1 | `evidence_relationships` migration: a/b in canonical order, task type, score, component scores, method version, reason codes, status (`suggested`/`accepted`/`rejected`/`ambiguous`/`merged`), created/decided by and at | `observations` | M |
| T2 | Rejected-pair guarantee: unique constraint on the canonical pair so rejection is an index probe and re-rejection is idempotent | T1 | S |
| T3 | `correlation_embeddings` + vector column + index (one row per observation, model version, input hash; skip re-embed when unchanged) | **owner: pgvector decision** | M |

## 2. Correlation

| # | Task | Depends on | Size |
|---|---|---|---|
| T4 | Candidate retrieval SQL: `ST_DWithin` + temporal window + category pre-filter, excludes rejected pairs, applies lower-context bounds when location is absent, always `LIMIT` | T0, T1, PostGIS | M |
| T5 | Detector wiring: duplicate, same-event, repost/source-dependency (`FR-027`), cross-case relevance — each with its own thresholds and reason codes, all feeding one `PairSuggestion` shape | T1, T4 | M |
| T6 | Provisional clusters: staff-only, never counted as cases, never transitively merged, ambiguity surfaced not broken | T1, T5 | M |
| T7 | Background job types `correlation_score` and `embedding_backfill`: idempotent, bounded retries, dead-letter state, intake latency never includes scoring (`NFR-001`) | **`processing_jobs` + worker** | M |

## 3. Review boundary

| # | Task | Depends on | Size |
|---|---|---|---|
| T8 | Review API: `accept`, `reject`, `mark_ambiguous`, `promote_to_case`, `merge`, `split` — reversible by new action, never by edit | T1, RBAC | M |
| T9 | Separation of duties: a reviewer cannot decide on their own submission; cross-organisation reads return 404, not 403 | RBAC, org scoping | S |
| T10 | Audit integration: every review decision writes an `audit_events` row in the same transaction | audit helper | S |

## 4. Acceptance

| # | Task | Depends on | Size |
|---|---|---|---|
| T11 | Scored run of the harness on a labelled set and a written result. No accuracy claim beyond what the run shows | **owner: evaluation route (plan §6 item 5)** | M |

## Not mine — hand back

| Item | Why |
|---|---|
| Split-phase intake contract (`FR-052`), offline error taxonomy, `notifications` + optional WebSocket | Plan §2.1 lists these under Phase 2, but they are inside the `collection` and `notifications` modules that Phase 1 owns. Two people editing one module is worse than one person doing it slightly later. |

---

## What I need from the Phase 1 teammate

Fastest possible answer: **paste the four `CREATE TABLE` statements.** Everything below is answerable in two minutes and each answer removes a guess from my side.

Priority 1 — without these I am guessing:

1. `observations` — the `CREATE TABLE`. I need the exact name and type of: primary key, original text, category, `observed_at`, and the location column.
2. `observed_at` — is it `timestamptz`? If a naive `timestamp`, the engine rejects it and correlation silently stops being trustworthy.
3. `observation_sources` — how do I get "the original source this report came from"? Column name, and whether reposts point at a shared root id.
4. Alembic — who owns the migrations directory, and may I add my own revision on top of theirs? Two revision heads in one chain is the most common way parallel backend work breaks.

Priority 2 — needed before T5/T7/T8:

5. `processing_jobs` — column names for claim/complete/fail, and how a job type is declared (enum, string, table). I need to register `correlation_score` and `embedding_backfill`.
6. Category — is it a lookup table, a Postgres enum, or free text? Exact values for water / air / land / waste / noise if they exist.
7. PostGIS — extension enabled, and what SRID observations are stored in.
8. RBAC and audit — signature of the "current user + organisation" dependency, and the audit-writing helper. If neither exists yet, say so and I will call a one-line stub I control.
9. Timing — which branch and roughly when does `observations` land on `prime`? Not to rush you: I am building against a fixture either way, and I would rather know when to swap it.

## What I need from the owner

1. **pgvector** (plan §6 item 3). Gates T3 only. Everything else proceeds without it.
2. **Phase 2 evaluation route** (plan §6 item 5): harness on a consented set, or a separate synthetic corpus. Gates T11 only, which is the last task.
3. **Confirm the module split** in "Not mine" above, so nobody builds split-phase intake twice.
