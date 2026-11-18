# Phase 2 — Evidence Correlation: what exists, what it needs

**Branch:** `phase2-correlation` · **Status:** engine built and tested; storage and API not built
**Parent plan:** `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md` §2

Phase 2 answers one question: *do these two reports look like they are about the same thing, and why does the system think so?* A person decides. The engine never does.

## 1. Built

`backend/src/ecowatch/correlation/` — standard library only, no database, no network.

| File | What it does |
|---|---|
| `features.py` | `ObservationFeatures` (what may be compared), `PairSuggestion` (the result), `Ranking` (ordered results plus a tie flag) |
| `scoring.py` | `token_similarity`, `temporal_proximity`, `spatial_proximity`, `category_agreement`, `score_pair`, `rank` |
| `evaluate.py` | Precision / recall / false links / missed links / unlabelled count against human labels |

49 tests pass and 2 are skipped by default (the PostGIS-gated ones run with `ECOWATCH_RUN_POSTGIS_TESTS=1`). `ruff check backend` is clean, and CI's `backend` job now activates itself because `backend/pyproject.toml` exists.

### The four decisions the code makes, which are the whole point

1. **A missing signal is dropped, not filled.** The score is a weighted mean over the signals that exist. A report with no location is compared on text and time only — it is not scored low for having no location, and no location is invented.
2. **"No comparable signal" is not zero.** If nothing can be compared, `score_pair` returns `None` and no suggestion is made. Returning `0` would read as "checked and unrelated", which is a claim we cannot make.
3. **Known-and-unrelated is a real result.** If both times are known and 100 hours apart in a 72-hour window, temporal proximity is `0.0` and is *present*. That is a different statement from "no time recorded", and the two must never collapse into each other.
4. **A repost is not a second witness.** Two reports sharing a `source_ref` are still scored (duplicate detection is a legitimate task) but are marked `source_independent = False` with a reason that says so. Otherwise five copied posts look like five independent accounts and inflate exactly the thing the product is supposed to detect.

The score is named `score` and only ever `score`. It is not a probability, not a confidence, not a severity, and not a danger level (`docs/13` §3, `docs/AGENT_GUIDE.md` §5). Every `PairSuggestion` has `status="unverified"` and there is no code path that changes it.

## 2. Needs from Phase 1 (team-owned)

Correlation compares observations, so it cannot run until these exist. This is the contract, not a request for extra work — each row is already in the Phase 1 plan.

| Phase 1 object | Field correlation reads | Why |
|---|---|---|
| `observations` | id, original text, category, `observed_at` (timezone-aware), location | the things being compared |
| `observation_sources` | the original source identifier | repost / copy-paste detection (`FR-027`) |
| `evidence_assets` | asset id per observation | photos for scan/EXIF jobs (`FR-017`) |
| `processing_jobs` | table and worker loop | correlation runs in the background, not in the intake request (`NFR-001`) |
| `users`, `organisations`, `memberships` | reviewer identity and organisation | a reviewer must not review their own submission, and results must not cross organisations |
| `audit_events` | append-only log | every review action is recorded |

Two schema facts Phase 2 needs that are decided on Phase 1's side:

- `observed_at` must be **timezone-aware** in the database. `ObservationFeatures` raises on a naive datetime rather than guessing an offset.
- Category must come from a controlled vocabulary, or `category_agreement` compares free text and means nothing.

## 3. Built against the real Phase 1 schema

Phase 1 (`3713211`) answered the contract questions from code, so the columns are now pinned by a test rather than read from a chat message.

| # | Now exists | Where |
|---|---|---|
| T0 | `evidence_relationships` with canonical-pair ordering, uniqueness per `(pair, task)`, status, components, missing signals, reasons, method version, decision record | `models.py`, migration `0002_phase2_correlation` |
| T1 | Rejected-pair guarantee: `CHECK (observation_a_id < observation_b_id)` plus `UNIQUE (pair, task)`, so rejection is an index probe and re-rejection is a no-op | migration `0002` |
| T2 | `observations.source_ref` (nullable, indexed) — **`FR-027` was unimplementable without it** | migration `0002` |
| T3 | Bounded candidate retrieval, organisation-scoped and hidden-aware | `repository.py` |
| T4 | `CorrelationService.scan_observation` — scores, persists, never overwrites a decision | `service.py` |
| T5 | Worker job type `correlation.scan`, so intake latency never includes scoring | `jobs/worker.py` |
| T6 | API: `GET /correlation/suggestions`, `POST /correlation/observations/{id}/scan`, `POST /correlation/suggestions/{id}/decision` | `router.py` |
| T7 | RBAC: `correlation:read` / `correlation:review`, deny-by-default, granted to reviewer, investigator, environmental specialist, org admin, system admin | `identity/permissions.py` |

### Deliberate deviations from the plan, and why

- **Retrieval filters distance in Python, not `ST_DWithin`.** The SQL prefilter (organisation, hidden, time window) runs on both dialects; the exact distance test runs over that bounded set. Honest limitation: it is bounded by the prefilter limit rather than a GiST index. Marked in code as a shortcut with its upgrade point. This is what let retrieval be tested on SQLite today instead of waiting for a database fixture.
- **Review decisions are one-way with `409` on re-decision.** "Reversible by a new action, not by an edit" is enforced as a refusal rather than silently allowing overwrite. Reopening a decision needs its own explicit action, which is not built.
- **`source_ref` lives on `observations`, not `observation_sources`.** The latter is the isolated contributor-identity table; a source reference is provenance, not a person, and mixing them would put correlation reads next to PII.

## 4. Not built, and why

| Missing | Blocked on |
|---|---|
| `correlation_embeddings` + vector index | the vector-store decision (plan §6 item 3) — `pgvector` assumed, not approved |
| Semantic similarity | same: `token_similarity` is the keyword fallback, not the model |
| Duplicate / repost / cross-case detectors as separate tasks | only `same_event` is wired; the enum and storage support all four, the scoring does not yet differentiate |
| `promote_to_case`, `merge`, `split` | needs the case-side rules and the two-key rules in `PERMISSIONS_MATRIX.md` §4 |
| Reopening a decided suggestion | needs a designed action, not an overwrite |
| Scored harness run | needs a labelled set and the evaluation-route decision (plan §6 item 5) |

## 4. Honest limits of the current engine

- `token_similarity` is exact word overlap, not embeddings. It is the documented keyword fallback, not the semantic model. Marked in the code as a shortcut with the upgrade point.
- Thresholds (`0.5`, 72 hours, 25 km, 0.45/0.25/0.20/0.10 weights) are reasoned defaults, not tuned values. Tuning requires labelled reviewed data, which does not exist yet.
- `evaluate` cannot report reviewer override rate; that needs real reviewer decisions. Reported as absent rather than approximated.
- No accuracy claim is made anywhere. Per plan §2.2, a harness on a consented set is the acceptance route; a number in this document would be a fabrication.
