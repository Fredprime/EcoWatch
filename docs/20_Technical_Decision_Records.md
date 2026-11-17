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

## 3. Required ADR template

ID, title, date, status, decision owner, context, decision, rationale, alternatives, benefits, trade-offs, risks, dependencies, verification method, affected documents and review date.

## 4. Change rule

Do not erase a superseded decision. Add a new record and explain why the decision changed. Update all affected documents and tests.
