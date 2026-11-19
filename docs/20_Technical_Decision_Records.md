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
| ADR-034 | Governance erasure is tombstone + restrict, keeping originals | Approved 2026-11-19 | FR-057 deletion is implemented as `obs:hide` tombstoning: hide the observation from all public/staff list and detail views and clear safe PII pointers, but never delete the observation row, its versions, evidence files or audit events. Reconciles FR-057 with the immutability hard boundary in `AGENTS.md`. Full record in §5. |
| ADR-035 | Clarify ADR-031 authority for case-side correlation actions | Approved 2026-11-19 | ADR-031's "two-key authority rules in §4" is clarified to apply to §1.7 scientific conclusions (`field_verified`/`recovery_verified`) only. `promote_to_case`, `merge`, `split` and `cross_case` use the single-actor IV/OA/SA + org-scope + self-review guard + same-transaction audit rules in `docs/PERMISSIONS_MATRIX.md` §3.4/§3.5/§4. Full record in §5. |
| ADR-036 | Phase 2 backend error taxonomy and idempotent media upload | Approved 2026-11-19 | Backend-only split-phase hardening: classify errors permanent vs transient in the error envelope, send `Retry-After` on 429/5xx, make media re-upload idempotent via an idempotency key, and document the split-phase contract. WebSocket invalidation and a server-side observation sync-state column are out of scope (frontend PWA queue's responsibility). Full record in §5. |

## 3. Required ADR template

ID, title, date, status, decision owner, context, decision, rationale, alternatives, benefits, trade-offs, risks, dependencies, verification method, affected documents and review date.

## 4. Change rule

Do not erase a superseded decision. Add a new record and explain why the decision changed. Update all affected documents and tests.

## 5. Detailed records (2026-11-19 backend hardening)

### ADR-034 — Governance erasure is tombstone + restrict, keeping originals

- **ID:** ADR-034
- **Title:** Governance erasure is tombstone + restrict, keeping originals
- **Date:** 2026-11-19
- **Status:** Approved
- **Decision owner:** Owner (Randy)
- **Context:** `FR-057` requires deletion workflows "consistent with approved policy", while the hard boundary in `AGENTS.md` states that original observations, versions, evidence files and audit events are immutable and that corrections create versions. A literal hard delete would break that boundary. `FR-058` publication is already implemented (`case.isPublicSummaryApproved` + `publications` table + `publish_summary()`), so it is out of scope here.
- **Decision:** Erasure reuses the existing `obs:hide` permission and `Observation.isHidden` flag. A governance endpoint tombstones an observation: it disappears from all public and staff list/detail views (and from evidence/correlation/receipt-lookup paths, where `isHidden` is already enforced), and safe PII pointers are cleared where possible. No `observations` row, `ObservationVersion`, evidence file or audit event is ever deleted. Data export and the existing append-only correction versions complete the rest of `FR-057`.
- **Rationale:** Meets the data-subject erasure need at the presentation layer while preserving provenance, auditability and the immutability boundary. No schema migration is required because `isHidden` already exists.
- **Alternatives considered:** (1) Full hard delete — rejected, breaks the immutability hard boundary. (2) Erasure-request queue only — rejected as insufficient for `FR-057`. (3) Export + correction only — rejected because it leaves no way to remove a record from active views.
- **Benefits:** Boundary-preserving; small change surface; reversible presentation state; reuses existing privacy enforcement.
- **Trade-offs / risks:** Tombstoned originals remain stored and could resurface if `isHidden` filtering is bypassed in a new query path; any new observation query must enforce `isHidden`. Erasure metadata (`hiddenAt`/`hiddenBy`/`reason`) is not added now; the audit event is the provenance record.
- **Dependencies:** `obs:hide` permission grant; `Observation.isHidden`; existing redaction/projection logic; `AuditService`.
- **Verification method:** Integration tests create temporary users/observations, verify hidden records are absent from list/detail and receipt lookup, verify audit event written, verify original row still present, then delete temporary records.
- **Affected documents:** `docs/06_Functional_Requirements.md` (FR-057), `docs/REVIEW_SUMMARY.md`, `docs/PROJECT_TRACKING.md`.
- **Review date:** 2026-12-19.

### ADR-035 — Clarify ADR-031 authority for case-side correlation actions

- **ID:** ADR-035
- **Title:** Clarify ADR-031 authority for case-side correlation actions
- **Date:** 2026-11-19
- **Status:** Approved
- **Decision owner:** Owner (Randy)
- **Context:** ADR-031 assigned `cross_case`, `promote_to_case`, `merge` and `split` to the cases module and said they "must use the two-key authority rules in `docs/PERMISSIONS_MATRIX.md` §4". However §4 defines two-key (ES + OA) authority only for the scientific conclusions `field_verified` and `recovery_verified` (§1.7). The same tables list merge/split/promote as single-actor `IV, OA, SA` + audit, and `cross_case` has no separate authority row. ADR-031's wording is therefore ambiguous.
- **Decision:** ADR-031's "two-key" reference applies only to §1.7 scientific conclusions. The four case-side actions use the single-actor rules in `docs/PERMISSIONS_MATRIX.md` §3.4/§3.5/§4: an investigator (IV), org authority (OA) or system admin (SA) actor, organisation-scoped (cross-org access returns 404), with a self-review guard and a same-transaction audit event. No new approval-slot columns or migration are introduced.
- **Rationale:** Matches the explicit authority tables and the existing case-status/merge behaviour; avoids inventing a stronger gate than the approved matrix specifies. Keeps correlation strictly decision-support (it records suggestions; it never sets case state).
- **Alternatives considered:** (1) Generalise ES+OA two-key approval to all four actions — rejected, not in the approved matrix and requires new columns + migration. (2) Two-key only for `promote_to_case` — rejected, no matrix basis; promote is an org-scoped case operation, not a §1.7 scientific conclusion.
- **Benefits:** Consistent with existing authority enforcement; minimal change surface; no schema change.
- **Trade-offs / risks:** Single-actor authority is weaker than two-key; mitigated by org-scoping, self-review guard and mandatory audit. `cross_case` has no explicit matrix row so it inherits the case-action single-actor default; revisit if the matrix is amended.
- **Dependencies:** `docs/PERMISSIONS_MATRIX.md` §3.4/§3.5/§4; cases service permission checks; `AuditService`.
- **Verification method:** Integration tests assert each action succeeds for IV/OA/SA, is denied for other roles, returns 404 cross-org, is blocked by the self-review guard, and writes exactly one audit event in the same transaction.
- **Affected documents:** ADR-031 (clarified, not overwritten), `docs/PERMISSIONS_MATRIX.md`, `docs/REVIEW_SUMMARY.md`.
- **Review date:** 2026-12-19.

### ADR-036 — Phase 2 backend error taxonomy and idempotent media upload

- **ID:** ADR-036
- **Title:** Phase 2 backend error taxonomy and idempotent media upload
- **Date:** 2026-11-19
- **Status:** Approved
- **Decision owner:** Owner (Randy)
- **Context:** The Phase 2 offline sync contract has no backend error classification: clients cannot tell a permanent failure (do not retry) from a transient one (retry later), 429 responses do not carry a `Retry-After`, and media re-upload mints a new `assetId` on every call so a retry after a lost response is not idempotent. The plan's "sync states" are largely a frontend PWA queue concern; WebSocket invalidation is marked optional.
- **Decision:** Backend-contract-only hardening: (1) add a permanent-vs-transient classification to the error envelope; (2) send `Retry-After` on 429 and 5xx, surfacing the existing rate-limit `lockedUntil`/retry seconds; (3) accept an idempotency key on media upload so replay returns the original `assetId`; (4) document the split-phase (text/coords first, media second) contract. WebSocket invalidation and a server-side observation `syncState` column are explicitly out of scope.
- **Rationale:** Gives offline clients enough information to back off and retry safely without overlapping frontend queue work or adding infrastructure.
- **Alternatives considered:** (1) Add sync-state column + endpoint + migration — rejected, overlaps frontend PWA queue. (2) Add thin WebSocket push — rejected as optional/deferred. (3) Error taxonomy only — rejected as too narrow; idempotent media replay is needed for correctness.
- **Benefits:** Small, bounded change (one nullable, uniquely-scoped column on `evidence_assets` via migration `0006_evidence_upload_idempotency`); deterministic retry behaviour; no new datastore or transport.
- **Trade-offs / risks:** Idempotency keys must be scoped and retained long enough for a realistic retry window; retention policy is bounded in the service. `Retry-After` on 5xx is a conservative hint, not a guarantee of recovery.
- **Dependencies:** `core/errors.py`, `core/schemas.py`, `core/rate_limit.py`, evidence module, split-phase contract docs.
- **Verification method:** Integration tests assert Retry-After on 429/5xx and that replaying a media upload with the same key returns the same `assetId` without creating a duplicate asset.
- **Affected documents:** `docs/BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md` §2.1, `docs/PHASE2_CORRELATION.md`, `docs/REVIEW_SUMMARY.md`.
- **Review date:** 2026-12-19.
