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

23 tests in `backend/tests/`. `ruff check backend` and `pytest backend` both pass, and CI's `backend` job now activates itself because `backend/pyproject.toml` exists.

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

## 3. Not built, and why

| Missing | Blocked on |
|---|---|
| `evidence_relationships` table | foreign keys to `observations`, which does not exist yet |
| `correlation_embeddings` table + vector index | the vector-store decision (plan §6 item 3) — `pgvector` is the assumed default and has not been approved |
| Rejected-pair unique index | same as above; it normalises `(observation_a_id, observation_b_id)` so rejection is an index probe instead of a rescan |
| Candidate retrieval SQL (spatial + temporal bounding) | needs PostGIS and the Phase 1 tables to test against |
| Worker job types | `processing_jobs` + worker are Phase 1 |
| Review API (`accept` / `reject` / `mark_ambiguous` / `promote_to_case` / `merge` / `split`) | needs reviewer identity, audit, and the tables above |

I did not create these as placeholder migrations. A migration that cannot be run is not a design, and it would collide with the team's Phase 1 revisions.

## 4. Honest limits of the current engine

- `token_similarity` is exact word overlap, not embeddings. It is the documented keyword fallback, not the semantic model. Marked in the code as a shortcut with the upgrade point.
- Thresholds (`0.5`, 72 hours, 25 km, 0.45/0.25/0.20/0.10 weights) are reasoned defaults, not tuned values. Tuning requires labelled reviewed data, which does not exist yet.
- `evaluate` cannot report reviewer override rate; that needs real reviewer decisions. Reported as absent rather than approximated.
- No accuracy claim is made anywhere. Per plan §2.2, a harness on a consented set is the acceptance route; a number in this document would be a fabrication.
