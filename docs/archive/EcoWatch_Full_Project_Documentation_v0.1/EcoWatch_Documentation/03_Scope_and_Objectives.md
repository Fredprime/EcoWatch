# 03 — Project Scope and Objectives

**Status:** Pilot approach proposed; exact pilot geography and indicators remain open.

## 1. Scope strategy

EcoWatch has a broad long-term vision, but a pilot that attempts to monitor every environmental issue across Ghana would be difficult to validate and maintain. The recommended approach is to begin in one clearly defined pilot geography, potentially a watershed, selected using evidence availability, environmental relevance, safe access, stakeholder interest and realistic intervention opportunities.

The one-watershed approach is a proposal, not an approved site decision.

## 2. Pilot objective

Demonstrate a reliable end-to-end workflow that collects selected environmental evidence, organises it with accurate provenance and timestamps, supports analysis and investigation, prioritises cases transparently, records response actions and evaluates selected outcomes.

## 3. Proposed pilot capabilities

### Core capabilities
- Anonymous and registered community submissions.
- Upload of supported photographs, videos and documents.
- Structured observations with location and date precision.
- Separate observed, submitted and server-received timestamps.
- A PostgreSQL-backed record of observations and cases.
- Human review and verification statuses.
- Basic map and case views.
- Manual entry or import of selected environmental datasets.
- Audit trail for important changes.
- Basic notifications or status updates where operationally feasible.

### Candidate intelligence capabilities
- Historical image comparison for a selected area.
- Basic geospatial change indicators.
- Duplicate or related-report suggestions.
- Search and filtering by location, date, category and status.
- Evidence timeline generation.
- Transparent prioritisation support.

These candidate intelligence features require data and validation. They should not all be assumed feasible in the first prototype.

## 4. Out of scope for the initial pilot

Unless separately approved, the pilot will not:
- Claim to monitor all of Ghana in real time.
- Automatically declare that a person or organisation has committed an offence.
- Replace environmental regulators, laboratories or professional field investigations.
- Automatically dispatch enforcement or restoration teams.
- Guarantee that every social-media platform can be accessed programmatically.
- Build a nationwide sensor network.
- Train large foundation models from scratch.
- Make medical diagnoses or determine individual health outcomes.
- Promise environmental restoration solely through software.
- Require a particular managed platform such as Supabase or Firebase.

## 5. Pilot success objectives

1. **Evidence integrity:** submitted files and source metadata remain traceable.
2. **Temporal clarity:** the system distinguishes when something was observed, submitted and received.
3. **Useful organisation:** users can find related observations without losing original records.
4. **Reviewability:** a human reviewer can see why a case has a particular status.
5. **Analytical usefulness:** selected comparisons provide interpretable results that experts can review.
6. **Operational workflow:** cases can be assigned, investigated and updated.
7. **Outcome measurement:** at least one selected intervention can be evaluated against documented indicators, if an appropriate intervention partner and data are available.

## 6. Pilot selection criteria

Score candidate locations against:
- Environmental significance and a clear use case.
- Availability of historical imagery and other baseline data.
- Availability of current measurements or feasible field collection.
- A manageable geographic boundary.
- Safe and ethical access.
- Local stakeholder interest.
- Potential for an actual response or restoration activity.
- Data permissions and partner capacity.
- Cost and connectivity constraints.

Do not choose a location solely because it is prominent in news or likely to attract attention.

## 7. Phased delivery

### Phase 0 — Design and validation
Complete documentation, stakeholder discovery, data inventory, pilot selection, indicator definitions, governance and risk review.

### Phase 1 — Evidence and case foundation
Implement the basic reporting, upload, timestamp, observation, case, review and map workflows after design approval.

### Phase 2 — Environmental intelligence
Add selected historical comparisons, geospatial analysis, report clustering and explainable alerts where data quality supports them.

### Phase 3 — Intervention and verification
Track approved response activities and evaluate environmental outcomes using defined indicators and methods.

### Phase gates
Each phase requires documented acceptance criteria and review. A feature should not move forward merely because code exists; it must meet its intended operational and evidence-quality requirements.

## 8. Dependencies

- A selected pilot location.
- Environmental and geospatial data access.
- Scientific advice on indicators and sampling.
- A responsible case-review process.
- Data protection and consent design.
- Hosting and operating budget.
- A named party responsible for system administration and ongoing maintenance.

## 9. Scope change control

A proposed feature or expansion must state:
- Which user problem it solves.
- Which five-stage activity it supports.
- Required data and permissions.
- Cost and maintenance impact.
- New risks.
- Whether it changes existing requirements or architecture.
- Who approves the change.
