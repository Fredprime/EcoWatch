# 20 — Technical Decision Records

**Status:** Living register. A product-direction decision does not automatically approve every implementation detail.

## 1. Status definitions

Approved = explicitly selected. Proposed = recommended. Deferred = postponed. Open = requires evidence or decision. Rejected = considered and not selected.

## 2. Decision register

| ID | Decision | Status | Rationale / note |
|---|---|---|---|
| ADR-001 | EcoWatch five-stage lifecycle | Approved | Foundational operating model retained. |
| ADR-002 | Hybrid human and automated collection | Approved | Shared collection process. |
| ADR-003 | Anonymous and registered submissions | Approved | Participation and follow-up options. |
| ADR-004 | Separate event, observation, submission and receipt times | Approved | Preserve temporal meaning. |
| ADR-005 | PostgreSQL | Approved | Explicit prior project decision. |
| ADR-006 | SignalWeave becomes EcoWatch subsystem | Approved 2026-11-16 | User's merger decision. |
| ADR-007 | Long-term scope covers land, water and connected ecosystems | Approved 2026-11-16 | User's merger decision. |
| ADR-008 | Correlation, geospatial analysis and environmental relationship assessment developed in phases | Approved 2026-11-16 | Strategic capability direction; sequence detailed in roadmap. |
| ADR-009 | Multi-role platform | Approved 2026-11-16 | Communities, researchers/investigators and organisations/institutions. |
| ADR-010 | Prototype evolves toward long-term product | Approved 2026-11-16 | Design for extensibility without overbuilding pilot. |
| ADR-011 | Monitoring, investigation/referral, intervention and verification form one lifecycle | Approved 2026-11-16 | Connected end-to-end direction. |
| ADR-012 | One bounded pilot geography | Proposed | Prevents scope explosion; exact site open. |
| ADR-013 | Modular monolith initially | Proposed | Reduces operational complexity. |
| ADR-014 | React + TypeScript | Proposed | SignalWeave candidate stack; not approved. |
| ADR-015 | Python + FastAPI | Proposed | Supports geospatial/data workflows; not approved. |
| ADR-016 | PostGIS | Proposed | Strong fit for spatial queries; requires approval. |
| ADR-017 | MapLibre | Proposed | Candidate map technology. |
| ADR-018 | IndexedDB offline queue | Proposed | Candidate for browser PWA. |
| ADR-019 | Sentence Transformers for semantic similarity | Proposed | Candidate model family; task evaluation required. |
| ADR-020 | SignalWeave weights 0.40/0.25/0.25/0.10 | Not adopted as universal | Prototype baseline only; unsuitable as global environmental score. |
| ADR-021 | Preserve original evidence and create derivatives | Approved design principle | Retain EcoWatch provenance approach. |
| ADR-022 | AI is decision support, not autonomous authority | Approved | Human review for consequential decisions. |
| ADR-023 | Supabase evaluation | Deferred | Separate platform evaluation. |
| ADR-024 | Firebase evaluation | Deferred | Separate platform evaluation. |
| ADR-025 | No build/master prompts in this documentation package | Approved | Retained documentation instruction. |
| ADR-026 | Three-phase backend build structure and modular monolith layout | Proposed | Organises backend delivery into Phase 1 (Core/Intake/Cases), Phase 2 (ECII Correlation/Worker/Offline Sync), and Phase 3 (Intelligence/Prioritisation/Interventions/Verification) in `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md`. |
| ADR-027 | Role permission matrix and status-transition authority | Proposed | Defines deny-by-default grants for the eight roles, separation-of-duties rules, two-key `field_verified`/`recovery_verified`, and who may set each case/intervention status, in `docs/PERMISSIONS_MATRIX.md`. Required to implement `FR-053`; approval unblocks Phase 1 RBAC. |
| ADR-028 | Schema additions to `docs/08` before Phase 1 | Proposed | Adds `organisation_id` scoping on seven aggregates, plus `methods`, `units`, `clarification_requests`, `publications`, and (Phase 2) `correlation_embeddings`. Rationale and the "deliberately not added" list are in `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md` §5. `docs/08` must be amended to match on approval. |
| ADR-029 | Phase 1 backend implementation, `camelCase` Python/JSON convention, and minimal stdlib/SQLAlchemy adapters | Approved 2026-11-18 | Owner directed immediate Phase 1 backend build with `camelCase` Python variables, parameters, ORM attributes, config attributes, and JSON API payloads mapped to `lower snake_case` SQL tables/columns (`AGENT_GUIDE.md` §8). Activates `ADR-026`, `ADR-027`, and `ADR-028` defaults for Phase 1 inside `backend/`, and uses native stdlib/SQLAlchemy (`os.environ` + `.env` parser, `UserDefinedType`/`with_variant` PostGIS `GEOGRAPHY`, regex WGS84 WKT validator, swappable auth & filesystem storage) to avoid redundant runtime dependencies. |
| ADR-030 | pgvector for Phase 2 embeddings and semantic candidate prefilter | Approved 2026-11-18 | Owner selected the plan's default vector store. `correlation_embeddings` and semantic similarity use pgvector inside the existing PostgreSQL 16 + PostGIS service, avoiding a second datastore and its credential/privacy review. `token_similarity` remains the labelled keyword fallback. No accuracy claim is made until a real reviewed set is evaluated. Implemented 2026-11-18: migration `0005_phase2_embeddings` and a deterministic hashed-word input (`hashed-words-v1`) exercise the storage/prefilter path; the semantic model itself stays open under ADR-019 and no accuracy is claimed. The dev/CI DB image now ships pgvector + PostGIS together. |
| ADR-031 | Case-side correlation actions belong to the Phase 1 cases module | Approved 2026-11-18 | Owner assigned `cross_case`, `promote_to_case`, `merge` and `split` to the cases module. Those actions must use the two-key authority rules in `docs/PERMISSIONS_MATRIX.md` §4. Correlation remains decision support: it records suggestions and provisional clusters and never declares case state, source, harm or verification. |
| ADR-032 | Database-backed login throttling and client-only token clearing | Approved 2026-11-18 | Owner directed "add the rate limiting accordingly and put it in writing". Login failures reuse the existing DB-backed `rate_limit` helper, keyed by SHA-256 of normalised email + client IP so no raw PII is stored in the bucket key; defaults are 5 attempts per 300 s window and a 900 s lockout, configurable through `loginMaxAttempts` / `loginWindowSeconds` / `loginLockoutSeconds` (`ECOWATCH_LOGIN_*`). A successful login resets the bucket. Accepted limitation: logout and 401 clearing are client-only; the stateless HMAC bearer token is not server-side revocable and stays valid until expiry, though deactivated users are rejected on every request. Immediate server-side revocation is deferred. Detail in `docs/REVIEW_SUMMARY.md` §3 item 5. |
| ADR-033 | Public observation DTO omits raw location wording | Approved 2026-11-18 | Owner selected "remove from public DTO". `ObservationPublicSummaryResponse` no longer exposes `originalLocationWording`, so public/redacted projections cannot leak raw location text; the restricted staff/owner DTO `ObservationRestrictedResponse` still includes it for permitted reviewers. Preserves the identity/location privacy boundary in `docs/AGENT_GUIDE.md` §5 and `docs/OWNER_RULES.md` §6 without altering the stored original observation. Detail in `docs/REVIEW_SUMMARY.md` §3 item 5. |

## 3. Required ADR template

ID, title, date, status, decision owner, context, decision, rationale, alternatives, benefits, trade-offs, risks, dependencies, verification method, affected documents and review date.

## 4. Change rule

Do not erase a superseded decision. Add a new record and explain why the decision changed. Update all affected documents and tests.
