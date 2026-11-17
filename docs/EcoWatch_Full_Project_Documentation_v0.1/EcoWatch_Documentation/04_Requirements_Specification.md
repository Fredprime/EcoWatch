# 04 — Functional and Non-Functional Requirements

**Status:** Initial requirements baseline. Requirements need stakeholder validation and prioritisation before implementation.

## 1. Requirement conventions

Identifiers are stable references. Priority:
- **Must:** essential for the pilot's intended integrity or workflow.
- **Should:** important but may be phased.
- **Could:** useful if resources allow.
- **Deferred:** intentionally not part of the current pilot.

A requirement is not considered complete until its acceptance criteria have been tested.

## 2. Functional requirements

### Collection and submissions
- **FR-001 (Must):** The system shall accept structured environmental observations from authorised interfaces.
- **FR-002 (Must):** The system shall support anonymous and registered submissions.
- **FR-003 (Must):** The system shall allow supported photographs, videos and documents to be attached to an observation.
- **FR-004 (Must):** The system shall record the source type and submission channel.
- **FR-005 (Must):** The system shall support exact, approximate, range-based and unknown observation dates.
- **FR-006 (Must):** The system shall distinguish `observed_at`, `submitted_at` and `received_at` where available.
- **FR-007 (Should):** The system should support offline-friendly submission capture and later synchronisation, subject to a separate design and security review.
- **FR-008 (Must):** The system shall preserve the original uploaded evidence and not silently replace it with an AI-modified version.

### Evidence and data management
- **FR-009 (Must):** The system shall store observation metadata in PostgreSQL.
- **FR-010 (Must):** The system shall preserve provenance for imported datasets and files.
- **FR-011 (Must):** The system shall record location precision and location source.
- **FR-012 (Must):** The system shall distinguish measured, observed, reported, reconstructed and predicted information.
- **FR-013 (Must):** The system shall record data-quality and verification status.
- **FR-014 (Should):** The system should support geospatial queries when spatial requirements are finalised.

### Case and investigation management
- **FR-015 (Must):** The system shall keep an original observation distinct from an incident/case.
- **FR-016 (Must):** The system shall allow a reviewer to link observations to a case without deleting or overwriting the observations.
- **FR-017 (Must):** The system shall record why a case status changed and who or what initiated the change.
- **FR-018 (Must):** The system shall support statuses such as unreviewed, under review, corroborated, field verified, referred, under response, monitoring, resolved and closed, with definitions refined during workflow design.
- **FR-019 (Should):** The system should identify possible duplicate or related observations for human review.

### Analysis and prioritisation
- **FR-020 (Should):** The system should compare selected observations with a documented baseline.
- **FR-021 (Should):** The system should show the evidence and assumptions behind an analytical result.
- **FR-022 (Should):** The system should support transparent prioritisation criteria.
- **FR-023 (Could):** The system could generate alerts for unusual changes after validation of the method and thresholds.
- **FR-024 (Must):** AI-generated suggestions shall be distinguishable from human-verified findings.

### Intervention and verification
- **FR-025 (Should):** The system should record a proposed or approved response action, responsible party, dates and status.
- **FR-026 (Should):** The system should record intended outcomes and indicators for an intervention.
- **FR-027 (Should):** The system should compare suitable pre-intervention and post-intervention evidence.
- **FR-028 (Must):** The system shall not mark an environmental outcome as verified solely because an activity was reported as completed.

### User access and accountability
- **FR-029 (Must):** The system shall separate public information from restricted contributor and investigation information.
- **FR-030 (Must):** The system shall enforce role-based permissions for restricted actions.
- **FR-031 (Must):** The system shall maintain an audit trail for sensitive changes.
- **FR-032 (Should):** Registered contributors should be able to view their own submission history and status where safe and appropriate.

## 3. Non-functional requirements

- **NFR-001 Security:** Validate uploads, restrict file types and sizes, scan files where feasible, and store files outside public executable paths.
- **NFR-002 Privacy:** Collect the minimum personal information necessary for the workflow.
- **NFR-003 Availability:** Define a realistic pilot availability target after hosting and operational capacity are known; do not promise 24/7 availability without support arrangements.
- **NFR-004 Performance:** Common list and case views should remain usable on typical mobile connections; measurable response-time targets must be set during technical design.
- **NFR-005 Usability:** Core reporting tasks should be understandable to users with limited technical experience.
- **NFR-006 Accessibility:** Interfaces should support keyboard access, readable contrast, clear labels and assistive technologies.
- **NFR-007 Maintainability:** Prefer modular components, documented interfaces, automated tests and understandable code.
- **NFR-008 Portability:** Keep data exportable in documented formats and avoid unnecessary provider-specific coupling.
- **NFR-009 Reliability:** Failed uploads and imports must be visible and recoverable without silently losing records.
- **NFR-010 Auditability:** Important status changes, access to sensitive records and administrative actions should be logged.
- **NFR-011 Data integrity:** Use validation constraints, transactions and backups appropriate to the data's importance.
- **NFR-012 Scientific transparency:** Analytical outputs must identify input sources, date ranges, methods and limitations.

## 4. Acceptance principles

- An anonymous submission can be received without requiring an account.
- A registered submission can be associated with an account without exposing the contributor's identity publicly by default.
- A submission with an approximate date does not get silently converted to an exact date.
- A delayed upload preserves the contributor's stated observation date and the server receipt date separately.
- Four reports that repeat the same original post are not automatically treated as four independent confirmations.
- A suspected incident can be investigated while its original observations remain intact.
- An AI suggestion is visibly labelled and reviewable.
- An intervention record and an environmental recovery finding are separate records.

## 5. Requirement traceability

Each requirement should eventually link to:
- Design component.
- Database entities or external data involved.
- User journey.
- Test case.
- Release or phase.
- Approval status.

## 6. Open requirement questions

- Which roles can verify a case?
- Can community reports be publicly visible, and at what level of location precision?
- What are the supported file types and size limits?
- Which notification channels are permitted and affordable?
- What service-level targets are realistic?
- What retention and deletion rules apply to each data category?
