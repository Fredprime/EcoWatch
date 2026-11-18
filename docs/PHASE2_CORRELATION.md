# Phase 2 — Evidence Correlation: what exists, what it needs

**Branch:** `phase2-correlation` · **Parent plan:** `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md` §2
**Task list with status:** `docs/PHASE2_TODO.md`

Phase 2 answers one question: *do these two reports look like they are about the same thing, and why does the system think so?* A person decides. The engine never does.

## 1. The engine

`backend/src/ecowatch/modules/correlation/` — standard library only, no database, no network.

| File | What it does |
|---|---|
| `features.py` | `ObservationFeatures` (what may be compared), `PairSuggestion` (the result), `Ranking` (ordered results plus a tie flag) |
| `scoring.py` | `token_similarity`, `temporal_proximity`, `spatial_proximity`, `category_agreement`, `score_pair`, `rank` |
| `policy.py` | per-category radius and time window, and the tighter window used when a report has no point |
| `detectors.py` | which task a pair belongs to (`duplicate`, `source_dependency`, `same_event`) and the thresholds that decide it |
| `evaluate.py` | precision / recall / false links / missed links / unlabelled count against human labels |

### The four decisions the code makes, which are the whole point

1. **A missing signal is dropped, not filled.** The score is a weighted mean over the signals that exist. A report with no location is compared on text and time only — it is not scored low for having no location, and no location is invented.
2. **"No comparable signal" is not zero.** If nothing can be compared, `score_pair` returns `None` and no suggestion is made. Returning `0` would read as "checked and unrelated", which is a claim we cannot make.
3. **Known-and-unrelated is a real result.** If both times are known and 100 hours apart in a 72-hour window, temporal proximity is `0.0` and is *present*. That is a different statement from "no time recorded", and the two must never collapse into each other.
4. **A repost is not a second witness.** Two reports sharing a `source_ref` are still scored but marked `source_independent = False`, and stored as a `source_dependency` suggestion. Otherwise five copied posts look like five independent accounts and inflate exactly the thing the product is supposed to detect.

The score is named `score` and only ever `score`. It is not a probability, not a confidence, not a severity, and not a danger level (`docs/13` §3, `docs/AGENT_GUIDE.md` §5). Every `PairSuggestion` has `status="unverified"` and there is no code path that changes it.

## 2. Built against the real Phase 1 schema

Phase 1 (`3713211`) answered the contract questions from code, so the columns are pinned by tests rather than read from a chat message.

| # | Now exists | Where |
|---|---|---|
| T0 | `evidence_relationships`: canonical-pair ordering, uniqueness per `(pair, task)`, task, score, components, missing signals, reasons, method version, `ambiguous`, decision record | `models.py`, migration `0002_phase2_correlation` |
| T1 | Rejected-pair guarantee: `CHECK (observation_a_id < observation_b_id)` plus `UNIQUE (pair, task)`, so rejection is an index probe and re-rejection is a no-op | migration `0002` |
| T2 | `observations.source_ref` (nullable, indexed) — **`FR-027` was unimplementable without it** | migration `0002` |
| T3 | Bounded candidate retrieval, organisation-scoped and hidden-aware, distance filtered by `ST_DWithin` on PostgreSQL | `repository.py` |
| T4 | Per-category retrieval policy; a report without a location gets a tighter time window instead of a wider scan | `policy.py` |
| T5 | Detector differentiation: `source_dependency` > `duplicate` > `same_event`, one task per pair, and nothing below the review threshold | `detectors.py` |
| T6 | `CorrelationService.scan_observation` — scores, persists, never overwrites a decision; `decide` and `reopen` record reviewer actions | `service.py` |
| T7 | Worker job type `correlation.scan`, queued automatically on observation intake and also available on demand; scoring never runs in the intake request | `jobs/worker.py`, `collection/service.py` |
| T8 | API: `GET /correlation/suggestions`, `POST /correlation/observations/{id}/scan`, `POST /correlation/suggestions/{id}/decision`, `POST /correlation/suggestions/{id}/reopen`, `GET /correlation/clusters` | `router.py` |
| T9 | `correlation_clusters` + members, one cluster per report, provisional and staff-only — never a case | migration `0003_phase2_clusters` |
| T10 | RBAC: `correlation:read` / `correlation:review`, deny-by-default; review implies read, enforced by a test | `identity/permissions.py` |
| T12 | Corrections and evidence uploads enqueue another `correlation.scan` in the same transaction as the change | `observations/service.py`, `evidence/service.py` |

### Deliberate deviations from the plan, and why

- **Retrieval filters distance with `ST_DWithin` on PostgreSQL, in Python on SQLite.** The GiST index Phase 1 created is what bounds the scan in production. SQLite has no spatial functions, so the test dialect keeps a haversine over the prefiltered set. Marked in code as a shortcut.
- **Decisions are reversible only by a named action.** Re-deciding a decided suggestion returns `409`; `POST /suggestions/{id}/reopen` returns it to the queue and requires a reason. The row holds current state, `audit_events` holds the append-only history, so reversal is an action rather than an edit.
- **One task per pair, most specific wins.** A repost with identical wording is one fact about the pair, so it gets one row. Storage still allows several tasks per pair if the detectors ever need to disagree.
- **`source_ref` lives on `observations`, not `observation_sources`.** The latter is the isolated contributor-identity table; a source reference is provenance, not a person, and mixing them would put correlation reads next to PII.

## 3. Not built, and why

| Missing | Status |
|---|---|
| `correlation_embeddings` + vector index | pgvector approved 2026-11-18 (`ADR-030`); table and index not built yet |
| Semantic similarity | same approval; `token_similarity` remains the labelled keyword fallback, not the model |
| `cross_case` detector | case-side rules and authority owner decided 2026-11-18 (`ADR-031`); not built |
| `promote_to_case`, `merge`, `split` | owned by the Phase 1 cases module under `ADR-031`; correlation keeps suggestions and provisional clusters only |
| Scored harness run | smoke-test only approved 2026-11-18; temporary fixtures prove mechanics, no accuracy claim |
| Split-phase intake, notification push | plan §2.1 lists them under Phase 2, but they live in `collection` and `notifications`, which Phase 1 owns |

## 4. Honest limits

- `token_similarity` is exact word overlap, not embeddings. It is the documented keyword fallback, not the semantic model. Marked in the code as a shortcut with the upgrade point.
- Thresholds (`0.45` same-event, `0.9` duplicate, 72 hours, 25 km, weights `0.45/0.25/0.20/0.10`) are reasoned defaults, not tuned values. Tuning needs labelled reviewed data, which does not exist yet.
- Category matching in `policy.py` is an exact normalised string match against a small table. An unknown category gets the default window; this costs recall, never correctness.
- `evaluate` cannot report reviewer override rate; that needs real reviewer decisions. Reported as absent rather than approximated.
- Cluster membership grows only when a person acts, but no action yet adds to a cluster beyond creation — `accept` records the relationship without merging clusters, because merging is `merge`, which is not built.
- No accuracy claim is made anywhere. Per plan §2.2, a harness on a consented set is the acceptance route; a number in this document would be a fabrication.
