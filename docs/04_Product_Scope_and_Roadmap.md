# 04 — Product Scope and Roadmap

**Status:** Long-term direction approved; first pilot scope open.

## 1. Scope strategy

The architecture should support interconnected land, water and ecosystem evidence, but the first pilot must not attempt to monitor all environmental problems or all of Ghana. A bounded pilot geography—potentially one watershed or sub-watershed—is recommended, not yet selected.

## 2. Prototype objective

Demonstrate a reliable end-to-end workflow:
- Collect selected observations and evidence.
- Preserve source, time, location, method and permissions.
- Identify candidate relationships with explainable reasons.
- Allow authorised humans to review and investigate.
- Display a case map and evidence timeline.
- Perform a small number of validated environmental analyses.
- Prioritise transparently.
- Record a response or intervention.
- Assess outcomes where suitable baseline and follow-up data exist.

If a real intervention cannot be safely and credibly evaluated during the prototype, demonstrate the workflow using clearly labelled synthetic or historical training data. Do not claim a real recovery outcome.

## 3. In scope for the first usable prototype

- Anonymous and registered submissions.
- Structured observations with uncertain or approximate date/location.
- Evidence upload with original-file preservation.
- Separate event-start, observed, submitted and received timestamps.
- PostgreSQL-backed observations and cases.
- Case and evidence relationship review.
- Basic map, list and timeline.
- Manual import of a small number of permitted datasets.
- Audit trail for consequential actions.
- Basic offline queue design and staged implementation.
- One correlation method tested on a labelled dataset.
- One selected environmental analysis workflow after pilot selection.

## 4. Later capabilities

- More automated satellite data ingestion.
- Multiple environmental indicators and model pipelines.
- Watershed-network analysis.
- Environmental relationship graphs.
- Advanced image analysis.
- Validated risk/prediction models.
- Partner integrations and controlled data exchange.
- Multi-region operations.
- More extensive language support and offline field workflows.

## 5. Out of scope unless separately approved

- Nationwide real-time environmental surveillance.
- Automatic declarations of illegal activity or legal responsibility.
- Autonomous enforcement dispatch.
- Replacement of regulators, laboratories or qualified field professionals.
- Guaranteed access to all social-media content.
- Building a nationwide sensor network.
- Training foundation models from scratch.
- Medical diagnosis or individual health-risk determination.
- Claiming that software itself restores an ecosystem.
- Premature microservices, streaming infrastructure or Kubernetes.

## 6. Development phases

### Phase 0 — Pilot definition and evidence readiness
Choose pilot geography, problem, indicators, data sources, review experts, partner pathway and evaluation method.

### Phase 1 — Unified evidence foundation
Identity/anonymous intake, observation model, evidence storage, provenance, timestamps, permissions, case records, basic map/timeline and audit.

### Phase 2 — Evidence correlation (SignalWeave subsystem)
Candidate retrieval, semantic similarity, spatial/temporal/context signals, explainable relationship suggestions, ambiguity handling, analyst decisions and offline synchronisation hardening.

### Phase 3 — Environmental intelligence
Selected remote-sensing or field-data analysis, historical comparison and environmental relationship representation. Start with deterministic methods and validated datasets.

### Phase 4 — Prioritisation and intervention
Transparent prioritisation criteria, assignment, referral, intervention records, milestones and evidence capture.

### Phase 5 — Verification and advanced intelligence
Outcome monitoring, baseline comparison, recovery assessment and only then predictive models if data and validation justify them.

## 7. Success measures

- Evidence records retain source and time provenance.
- Duplicate submissions do not create duplicate records.
- Related-observation suggestions are evaluated against labelled examples.
- False merges and missed relationships are measured.
- Reviewers can understand and reverse machine suggestions.
- A case timeline distinguishes all relevant date types.
- Selected environmental analysis can be reproduced and reviewed.
- Prioritisation shows its factors and limitations.
- Intervention activity and outcome are represented separately.
- Backup restoration, access controls and user workflows pass acceptance tests.

Numeric targets must be set after pilot conditions and datasets are known.
