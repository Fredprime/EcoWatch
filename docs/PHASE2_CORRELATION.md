# Phase 2 — Evidence Correlation: what exists, what it needs

**Branch:** `phase2-correlation` · **Parent plan:** `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md` §2
**Task list with status:** `docs/PHASE2_TODO.md`

Phase 2 answers one question: *do these two reports look like they are about the same thing, and why does the system think so?* A person decides. The engine never does.

## 1. The engine

`backend/src/ecowatch/modules/correlation/` — standard library only, no database, no network.

| File | What it does |
|---|---|
| `features.py` | `ObservationFeatures` (what may be compared, including an optional stored vector), `PairSuggestion` (the result), `Ranking` (ordered results plus a tie flag) |
| `scoring.py` | `semantic_similarity` (vector cosine, or `token_similarity` fallback), `vector_similarity`, `tokens`, `temporal_proximity`, `spatial_proximity`, `category_agreement`, `score_pair`, `rank` |
| `embeddings.py` | `build_embedding` / `embedding_input_hash`: deterministic hashed-word vector input (`hashed-words-v1`, 384 dims). Not a validated semantic model |
| `policy.py` | per-category radius and time window, and the tighter window used when a report has no point |
| `detectors.py` | which task a pair belongs to (`duplicate`, `source_dependency`, `same_event`) and the thresholds that decide it |
| `evaluate.py` | precision / recall / false links / missed links / unlabelled count against human labels |

### The four decisions the code makes, which are the whole point

1. **A missing signal is dropped, not filled.** The score is a weighted mean over the signals that exist. A report with no location is compared on text and time only — it is not scored low for having no location, and no location is invented.
2. **"No comparable signal" is not zero.** If nothing can be compared, `score_pair` returns `None` and no suggestion is made. Returning `0` would read as "checked and unrelated", which is a claim we cannot make.
3. **Known-and-unrelated is a real result.** If both times are known and 100 hours apart in a 72-hour window, temporal proximity is `0.0` and is *present*. That is a different statement from "no time recorded", and the two must never collapse into each other.
4. **A repost is not a second witness.** Two reports sharing a `source_ref` are still scored but marked `source_independent = False`, and stored as a `source_dependency` suggestion. Otherwise five copied posts look like five independent accounts and inflate exactly the thing the product is supposed to detect.

The score is named `score` and only ever `score`. It is not a probability, not a confidence, not a severity, and not a danger level (`docs/13` §3, `docs/AGENT_GUIDE.md` §5). Every `PairSuggestion` has `status="unverified"` and there is no code path that changes it.

`semantic_similarity` uses cosine overlap of stored vectors when both observations have one; if either vector is absent it falls back to the labelled `token_similarity` keyword signal. The nearest-vector query is a **candidate prefilter** — it narrows the time/space-bounded candidate set, never widens it and never establishes a relationship on its own.

## 2. Built against the real Phase 1 schema

Phase 1 (`3713211`) answered the contract questions from code, so the columns are pinned by tests rather than read from a chat message.

| # | Now exists | Where |
|---|---|---|
| T0 | `evidence_relationships`: canonical-pair ordering, uniqueness per `(pair, task)`, task, score, components, missing signals, reasons, method version, `ambiguous`, decision record | `models.py`, migration `0002_phase2_correlation` |
| T1 | Rejected-pair guarantee: `CHECK (observation_a_id < observation_b_id)` plus `UNIQUE (pair, task)`, so rejection is an index probe and re-rejection is a no-op | migration `0002` |
| T2 | `observations.source_ref` (nullable, indexed) — **`FR-027` was unimplementable without it** | migration `0002` |
| T3 | Bounded candidate retrieval, organisation-scoped and hidden-aware, distance filtered by `ST_DWithin` on PostgreSQL; optional nearest-vector prefilter narrows (never widens) that set | `repository.py` |
| T3b | `correlation_embeddings`: `vector(384)` + HNSW cosine index on PostgreSQL (JSON fallback on SQLite), unique per `(observation, model version, input hash)`, unchanged inputs skip the write; deterministic hashed-word vectors, no accuracy claim | `models.py`, `embeddings.py`, `core/vector.py`, migration `0005_phase2_embeddings` |
| T4 | Per-category retrieval policy; a report without a location gets a tighter time window instead of a wider scan | `policy.py` |
| T5 | Detector differentiation: `source_dependency` > `duplicate` > `same_event`, one task per pair, and nothing below the review threshold | `detectors.py` |
| T6 | `CorrelationService.scan_observation` — scores, persists, never overwrites a decision; `decide` and `reopen` record reviewer actions | `service.py` |
| T7 | Worker job type `correlation.scan`, queued on intake, on demand and on re-scan triggers; each scan materialises its observation's vector, so no separate backfill job is needed; scoring never runs in the intake request | `jobs/worker.py`, `collection/service.py`, `service.py` |
| T8 | API: `GET /correlation/suggestions`, `POST /correlation/observations/{id}/scan`, `POST /correlation/suggestions/{id}/decision`, `POST /correlation/suggestions/{id}/reopen`, `GET /correlation/clusters` | `router.py` |
| T9 | `correlation_clusters` + members, one cluster per report, provisional and staff-only — never a case | migration `0003_phase2_clusters` |
| T10 | RBAC: `correlation:read` / `correlation:review`, deny-by-default; review implies read, enforced by a test | `identity/permissions.py` |
| T12 | Corrections and evidence uploads enqueue another `correlation.scan` in the same transaction as the change | `observations/service.py`, `evidence/service.py` |
| T11 | Evaluation harness smoke test on temporary synthetic fixtures; counts assert wiring, not accuracy | `backend/tests/evaluation/test_correlation_smoke.py` |

### Deliberate deviations from the plan, and why

- **Retrieval filters distance with `ST_DWithin` on PostgreSQL, in Python on SQLite.** The GiST index Phase 1 created is what bounds the scan in production. SQLite has no spatial functions, so the test dialect keeps a haversine over the prefiltered set. Marked in code as a shortcut.
- **Decisions are reversible only by a named action.** Re-deciding a decided suggestion returns `409`; `POST /suggestions/{id}/reopen` returns it to the queue and requires a reason. The row holds current state, `audit_events` holds the append-only history, so reversal is an action rather than an edit.
- **One task per pair, most specific wins.** A repost with identical wording is one fact about the pair, so it gets one row. Storage still allows several tasks per pair if the detectors ever need to disagree.
- **`source_ref` lives on `observations`, not `observation_sources`.** The latter is the isolated contributor-identity table; a source reference is provenance, not a person, and mixing them would put correlation reads next to PII.

## 3. Not built, and why

| Missing | Status |
|---|---|
| An approved semantic embedding model | ADR-019 is still open. The current vectors are deterministic hashed-word inputs (`hashed-words-v1`) that let the pgvector storage/prefilter path be tested; they are **not** a validated semantic model and carry no accuracy claim. `token_similarity` remains the labelled keyword fallback. |
| `cross_case` detector | still not built: the correlation engine emits no cross-case *suggestion signal*. The separate case-side `cross_case` **action** (moving selected links between two cases) is built in the cases module under `ADR-031`/`ADR-035`. |
| `promote_to_case`, `merge`, `split` case-side actions | **built 2026-11-19** in the Phase 1 cases module under `ADR-031`, with authority clarified by `ADR-035` (single-actor IV/OA/SA, org-scoped, self-review guarded, audited). Correlation itself still keeps suggestions and provisional clusters only — no detector was promoted to a conclusion. |
| Scored harness run on real labelled reports | needs a consented, human-reviewed set; smoke test approved and run on temporary fixtures only, no accuracy claim |
| Split-phase intake hardening | **built 2026-11-19** (`ADR-036`): permanent/transient error category, `Retry-After`, and idempotent media re-upload via `Idempotency-Key`. See `BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md` §2.1 for the concrete contract. |
| Notification push / WebSocket invalidation | still not built and explicitly deferred (`ADR-036`); REST remains authoritative. Durable client queueing and sync states belong to the frontend PWA. |

## 4. Honest limits

- The stored vectors come from deterministic word hashing (`hashed-words-v1`, 384 dims), not a learned semantic model. They give pgvector a stable input so the storage, skip-on-unchanged and candidate-prefilter paths can be tested; they do **not** make the engine semantically accurate and no accuracy claim is made (ADR-019 is still open). `token_similarity` is exact word overlap and is the labelled keyword fallback whenever either vector is absent.
- The nearest-vector query runs only on PostgreSQL (pgvector). SQLite — the test dialect — keeps the time/space candidate set and the keyword fallback, so the two dialects are equivalent in behaviour, not in retrieval index.
- Thresholds (`0.45` same-event, `0.9` duplicate, 72 hours, 25 km, weights `0.45/0.25/0.20/0.10`) are reasoned defaults, not tuned values. Tuning needs labelled reviewed data, which does not exist yet.
- Category matching in `policy.py` is an exact normalised string match against a small table. An unknown category gets the default window; this costs recall, never correctness.
- `evaluate` cannot report reviewer override rate; that needs real reviewer decisions. Reported as absent rather than approximated.
- Cluster membership grows only when a person acts, but no action yet adds to a cluster beyond creation — `accept` records the relationship without merging clusters. The case-side `merge` action is now built (2026-11-19), but it moves case-observation links; it does not mutate a correlation cluster, which stays a read-only suggestion container.
- No accuracy claim is made anywhere. Per plan §2.2, a harness on a consented set is the acceptance route; a number in this document would be a fabrication.
