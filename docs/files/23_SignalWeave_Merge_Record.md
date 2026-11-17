# 23 — SignalWeave Merge Record

**Status:** Record of the merge (v0.8). Approved as a direction by the owner on 12 Nov 2026 (DR-035); individual proposals are marked.

## 1. What was merged
SignalWeave (PRD version 1.0 and Technical Design version 1.0, described as a hackathon MVP) is fitted into EcoWatch as its **correlation engine and offline-first collection layer**. EcoWatch remains the umbrella system with its five stages, three areas, evidence rules and governance. The detailed design is in document 22.

## 2. Where each SignalWeave requirement went
| SignalWeave | EcoWatch |
|---|---|
| FR-01 to FR-04 intake and validation | FR-001, FR-003, FR-004, FR-005 |
| FR-05 idempotent submission | FR-015 |
| FR-06 categories | Controlled categories (document 06) |
| FR-07 correct a report before review | FR-049 (as an amendment through the tracking code) |
| FR-08 to FR-12 similarity, distance, time, combined score, candidate filtering | FR-031, FR-032, FR-033 |
| FR-13, FR-14 suggest or create, store score components | FR-034, FR-035, FR-032 |
| FR-15 context signal | FR-031 |
| FR-16 re-evaluate clusters | FR-037 |
| FR-17 to FR-21 accept, reject, merge, split, audit | FR-036, FR-021, FR-060 |
| FR-22 to FR-27 map, detail, timeline, confidence, live update, filters | FR-063, FR-026, FR-032, FR-038, FR-062 |
| FR-28 to FR-34 offline queue, retry, IDs, ordering, compression, states | FR-011, FR-016, FR-017, FR-018, FR-019 |
| FR-35 incident statuses | Case statuses with a new "provisional" status (document 06) |
| FR-36 label machine output unverified | FR-030 |
| FR-37 keep reporter identity private | FR-048, NFR-002 |
| FR-38 roles | FR-065 to FR-070 |
| FR-39 audit trail | FR-060 |
| FR-40 hide or flag abusive reports | FR-050 |

## 3. What changed to fit EcoWatch
| SignalWeave | In EcoWatch | Why |
|---|---|---|
| Reporters may be authenticated | The public has no login or accounts; staff submit from the Staff area (DR-023, DR-024) | Approved earlier |
| Provisional incident created for every new report | A provisional cluster in the Staff area only; not a case until promoted | Cases are human decisions (DR-032, DR-040) |
| Server `submitted_at` | `received_at`; device `submitted_at` kept separately | Four times (DR-004) |
| Emergency-style incidents (flooding, fire, roads) | Environmental categories; scales per category; not an emergency service | EcoWatch scope, document 09 |
| Hackathon MVP prototype | Full working system in capability phases | DR-017 |
| Fixed illustrative weights | Starting values tuned on real reviewed data | Not established science |
| Prototype performance targets | Design targets, measured, not claimed | Honesty |
| Python, FastAPI, React, PostGIS and related tools "recommended" | Proposed candidates only; only PostgreSQL is Approved | DR-005, DR-015 |
| Offline capture as one feature | Un-deferred in EcoWatch (was Deferred) and placed in Phase 1 | Reliability for low connectivity |

## 4. What was left out
- **The seeded demonstration dataset, sample media, seed command, labelled demo reports, simulated scenarios, the demo script and the demo acceptance criteria.** EcoWatch holds no example, demo, sample or seed data (DR-018). The acceptance ideas are kept as tests using temporary records (document 13).
- **Build material:** the repository tree, sample requests and responses, environment variable lists, container setup and the implementation sequence. This package includes no build instructions or prompts (DR-007).
- **Hackathon scoping language** such as P0 and P1 delivery order tied to a demonstration day.

## 5. What was kept in spirit
Evidence before automation; human in the loop; explainability; connectivity resilience; privacy by design; graceful uncertainty; no transitive merging; missing signals disclosed; rejected suggestions kept; correlation never run inside the submission request; no hosted AI dependency for core correlation.

## 6. Decisions the owner still needs to make
1. **Hackathon demonstration (DR-041, Open):** if a live demonstration is needed, it would need data. That conflicts with DR-018. Options are to demonstrate with temporary records in a separate throwaway environment that is never connected to the real system, or to make no live demonstration. Nothing is assumed.
2. Approve PostGIS (DR-008), now more important for candidate search.
3. Approve running correlation locally with no hosted AI service (DR-036).
4. Approve provisional clusters as Staff-only and not cases (DR-040).
5. Choose how real review decisions may be reused for evaluation, and their retention.
6. Confirm whether the SignalWeave name stays as the component name.

## 7. Documents changed
00, 01, 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21 and START_HERE were updated; 22 and 23 are new.
