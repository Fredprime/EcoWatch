# 02 — Merger Strategy and Product Boundaries

**Status:** Merger direction approved; detailed subsystem interfaces proposed.

## 1. Merger decision

SignalWeave becomes a core EcoWatch subsystem. It will not remain a separate product with its own independent product identity, database or deployment in the initial architecture.

The capability is renamed **Evidence Correlation and Incident Intelligence (ECII)**. “SignalWeave” may be retained as an internal historical name in source-control history, but new product documentation and user-facing interfaces should use EcoWatch terminology unless the owner later decides otherwise.

## 2. Why this is a partial capability merger, not a wholesale algorithm merger

SignalWeave answers: “Which reports may describe the same developing incident?”

EcoWatch asks a broader question: “What environmental condition is occurring, what evidence supports it, how may it relate to other environmental changes, what response is justified, and what happened afterwards?”

These are not equivalent tasks. A report-clustering score cannot establish environmental causation, watershed connectivity, ecological impact or recovery.

Therefore:
- Merge common evidence intake, provenance, timestamps, offline submission, candidate retrieval, semantic similarity, relationship suggestions, review and audit capabilities.
- Retain specialist environmental analysis as a separate subsystem.
- Redesign spatial and temporal correlation to support environmental relationships beyond simple proximity.
- Keep observation/evidence records distinct from environmental cases.
- Never equate a cluster with a scientifically confirmed incident or cause.

## 3. Capability disposition

| SignalWeave capability | Disposition | Reason |
|---|---|---|
| Report intake | Merge into collection | Common intake path |
| Client-generated IDs/idempotency | Adopt | Safe retry and offline sync |
| Offline queue | Adopt, implementation phased | Valuable in low-connectivity field contexts |
| Semantic embeddings | Retain as optional signal | Helps identify similar descriptions |
| Spatial proximity | Redesign | Proximity alone misses drainage/watershed relationships |
| Temporal proximity | Redesign | Environmental processes may be cumulative or delayed |
| Context/category score | Retain and expand | Must reflect environmental domain and evidence type |
| Incident clustering | Adapt | Observations can relate to multiple cases |
| Analyst review | Merge into case/evidence review | One review and audit process |
| Map/timeline | Merge and expand | Shared spatial and temporal workspace |
| WebSocket updates | Optional implementation choice | Use only where live collaboration needs it |
| Image compression/EXIF removal | Do not apply destructively to originals | EcoWatch preserves restricted originals and creates derivatives |
| Standalone SignalWeave dashboard | Retire as separate product | Avoid duplicate workflows |

## 4. Core conceptual boundaries

### Observation
A record of something reported, measured, observed, detected or imported. It remains immutable in its original meaning; corrections are versioned.

### Evidence asset
A file or data object supporting an observation or investigation, with provenance and access controls.

### Evidence relationship
A typed, explainable link between observations/assets or between an observation and a case. It may be suggested, reviewed, disputed or rejected.

### Environmental case
A managed investigation or response record concerning a suspected environmental event, condition, pressure or impact. A case may contain multiple observations and hypotheses.

### Environmental relationship
A domain-specific relationship such as upstream/downstream, possible source/pathway/receptor, habitat connectivity or temporal association. It is not proof of causation by itself.

### Intervention
A planned or completed action linked to one or more cases.

### Verification assessment
A documented assessment of whether defined outcomes are supported by measurements or other suitable evidence.

## 5. What must not be merged

- Correlation confidence must not become an environmental severity score.
- Similar descriptions must not be treated as independent corroboration.
- Geographic distance must not be the only spatial relationship.
- Submission time must not be substituted for observation time without disclosure.
- A case must not overwrite original observations.
- AI-generated interpretation must not become a verified finding automatically.
- Public visibility must not be the default for sensitive evidence.

## 6. Recommended system boundary

One EcoWatch product and one logical application, with clear internal modules and explicit interfaces. Start as a modular monolith. Expensive raster, imagery or model processing may later move to separate workers/services when workload and operational evidence justify it.

## 7. Merger success criteria

The merger is successful if it:
- Eliminates duplicate reporting, identity, evidence and review implementations.
- Preserves SignalWeave's explainable correlation capability.
- Adds environmental relationships that ordinary incident clustering cannot represent.
- Preserves evidence provenance and case integrity.
- Supports the complete five-stage EcoWatch lifecycle.
- Remains buildable by a small team without premature distributed infrastructure.
