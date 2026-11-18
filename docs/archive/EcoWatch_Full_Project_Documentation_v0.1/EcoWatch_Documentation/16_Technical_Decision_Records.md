# 16 — Technical Decision Records

**Status:** Living register. Only explicitly confirmed choices are marked approved.

## 1. Decision status definitions

- **Approved:** confirmed by the project owner.
- **Proposed:** recommended but not approved.
- **Deferred:** intentionally postponed.
- **Open:** requires investigation or a decision.
- **Rejected:** considered and not selected.

## 2. Decision register

| ID | Decision | Status | Rationale / notes |
|---|---|---|---|
| ADR-001 | Use a five-stage process: Collect, Analyse, Prioritise, Intervene, Verify | Approved | This is the foundational operating model. |
| ADR-002 | Use hybrid data collection | Approved | Automated sources and direct submissions should feed one collection process. |
| ADR-003 | Support anonymous and registered submissions | Approved | Enables participation without mandatory accounts while supporting follow-up for registered users. |
| ADR-004 | Track distinct event, observation, submission and receipt times where available | Approved | Preserves reporting delay and timeline evidence without conflating dates. |
| ADR-005 | Use PostgreSQL as the relational database technology | Approved | Explicitly approved by project owner. |
| ADR-006 | Evaluate Supabase separately | Deferred | Not a pilot concern; to be covered in a different document. |
| ADR-007 | Evaluate Firebase separately | Deferred | Not a pilot concern; to be covered in a different document. |
| ADR-008 | Start with one pilot watershed or similarly bounded area | Proposed | Limits complexity while allowing connected land/water analysis. Exact site not selected. |
| ADR-009 | Use PostGIS for geospatial database operations | Proposed | Likely useful for watershed, river and spatial relationship queries; requires approval. |
| ADR-010 | Use a modular application before microservices | Proposed | Reduces operational complexity for a small initial team. |
| ADR-011 | Consider Next.js/React for frontend | Proposed | Candidate responsive web stack; not approved. |
| ADR-012 | Consider Python/FastAPI for backend | Proposed | Candidate stack for scientific and geospatial integration; not approved. |
| ADR-013 | Use external object storage for large media | Proposed | Keeps large files separate from relational metadata; provider not selected. |
| ADR-014 | Use AI as decision support, not autonomous authority | Approved principle | AI suggestions require human review for consequential decisions. |
| ADR-015 | Keep observations distinct from incidents/cases | Approved design principle | Prevents loss of source detail and premature merging. |
| ADR-016 | Build detailed documentation before implementation/deployment | Approved | Project owner explicitly requested documentation-first development. |
| ADR-017 | Do not create build prompts or master prompts | Approved | Explicit project instruction. |

## 3. Decision record template

For each new decision, record:

**ID:**  
**Title:**  
**Status:**  
**Date:**  
**Decision owner:**  
**Context/problem:**  
**Decision:**  
**Why this option:**  
**Alternatives considered:**  
**Benefits:**  
**Trade-offs:**  
**Risks:**  
**Dependencies:**  
**Verification/acceptance method:**  
**Documents affected:**  
**Review date:**

## 4. Important distinction

A recommendation in an architecture document is not an approved decision unless the decision register says so. When a decision changes, do not erase the previous decision. Record the new decision, date, reason and affected documents.
