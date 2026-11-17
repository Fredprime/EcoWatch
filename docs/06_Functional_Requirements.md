# 06 — Functional Requirements

**Status:** Merged requirements baseline; priorities are proposed for prototype planning.

Priority: **P0** required for a credible core prototype; **P1** important after the core path; **P2** future capability. Requirements must be converted into test cases before implementation.

## 1. Collection and observations

- **FR-001 (P0):** Accept observations from anonymous and registered contributors.
- **FR-002 (P0):** Assign a stable unique identifier at client creation or server receipt.
- **FR-003 (P0):** Store description, observation type, source type and submission metadata.
- **FR-004 (P0):** Support optional and uncertain location.
- **FR-005 (P0):** Preserve event-start, observed, submitted and server-received times separately where known.
- **FR-006 (P0):** Represent exact, approximate, range and unknown date/location precision.
- **FR-007 (P0):** Validate text length, coordinate ranges, timestamps, units and payload size.
- **FR-008 (P0):** Make retries idempotent.
- **FR-009 (P1):** Support structured field protocols and measurement metadata.
- **FR-010 (P1):** Allow controlled correction with version history.

## 2. Evidence and provenance

- **FR-011 (P0):** Accept approved file types within configurable size limits.
- **FR-012 (P0):** Preserve originals separately from previews and analysis derivatives.
- **FR-013 (P0):** Record checksum, source, acquisition method, timestamps and processing history where applicable.
- **FR-014 (P0):** Keep storage keys server-generated; never use user filenames as paths.
- **FR-015 (P0):** Restrict access to sensitive evidence.
- **FR-016 (P1):** Record dataset licence, attribution, coverage and permitted use.
- **FR-017 (P1):** Record media scanning and metadata extraction outcomes.

## 3. Evidence correlation and incident intelligence

- **FR-018 (P0):** Generate candidate relationships using bounded retrieval.
- **FR-019 (P0):** Support semantic similarity as one optional signal.
- **FR-020 (P0):** Support spatial and temporal compatibility where source data permits.
- **FR-021 (P0):** Support missing-signal handling without inventing values.
- **FR-022 (P0):** Persist component scores, method/version and human-readable reason codes.
- **FR-023 (P0):** Label automated links as suggestions, not facts.
- **FR-024 (P0):** Allow authorised reviewers to accept, reject or mark ambiguous.
- **FR-025 (P1):** Allow one observation to relate to multiple cases through typed links.
- **FR-026 (P1):** Support merge/split operations with audit and preserved history.
- **FR-027 (P1):** Detect possible reposts/shared-source dependence where feasible.

## 4. Case management and investigation

- **FR-028 (P0):** Create a case independently of its source observations.
- **FR-029 (P0):** Display case summary, status, geography, timeline and linked evidence.
- **FR-030 (P0):** Record reviewer/investigator, status changes and rationale.
- **FR-031 (P1):** Assign cases and define follow-up actions.
- **FR-032 (P1):** Record competing hypotheses and evidence gaps.
- **FR-033 (P1):** Support controlled referral and external reference records.

## 5. Environmental intelligence

- **FR-034 (P0):** Import a small, permissioned pilot dataset with source metadata.
- **FR-035 (P0):** Distinguish raw observations from derived analysis and interpretation.
- **FR-036 (P1):** Support selected historical comparisons and map overlays.
- **FR-037 (P1):** Record spatial/temporal method, parameters, input versions and limitations.
- **FR-038 (P1):** Represent environmental relationship types such as upstream/downstream or possible source-pathway-receptor.
- **FR-039 (P2):** Support validated predictive models only after suitable data and evaluation.

## 6. Prioritisation, intervention and verification

- **FR-040 (P1):** Display transparent prioritisation factors and missing information.
- **FR-041 (P1):** Allow authorised users to set and record priorities with rationale.
- **FR-042 (P1):** Record intervention objective, owner, location, dates, milestones and supporting evidence.
- **FR-043 (P1):** Distinguish activity completion, output delivery, environmental outcome and recovery.
- **FR-044 (P1):** Record baseline and follow-up indicators, methods, units and uncertainty.
- **FR-045 (P1):** Support outcome states including improvement, no improvement, deterioration and inconclusive.

## 7. Interface, notifications and offline operation

- **FR-046 (P0):** Provide a mobile-friendly reporting workflow.
- **FR-047 (P0):** Provide reviewer access to evidence and relationship explanations.
- **FR-048 (P0):** Provide map, list and chronological timeline views.
- **FR-049 (P1):** Support live update notifications where useful.
- **FR-050 (P1):** Persist draft reports locally when offline.
- **FR-051 (P1):** Retry transient failures safely and show queued/syncing/submitted/failed states.
- **FR-052 (P1):** Upload text and coordinates before large media where bandwidth is limited.

## 8. Security and governance

- **FR-053 (P0):** Enforce role-based permissions server-side.
- **FR-054 (P0):** Keep contributor identity separate from ordinary public case views.
- **FR-055 (P0):** Record audit events for sensitive actions.
- **FR-056 (P0):** Protect uploaded media from public unauthorised access.
- **FR-057 (P1):** Support data correction, export and deletion workflows consistent with approved policy.
- **FR-058 (P1):** Support approved public summaries without sensitive data.

## 9. Non-functional requirements

- **NFR-001 Reliability:** API receipt must not depend on completion of expensive model processing.
- **NFR-002 Integrity:** duplicate retries must not create duplicate observation records.
- **NFR-003 Explainability:** every automated relationship must expose its method and reasons.
- **NFR-004 Resilience:** offline-capable workflows must distinguish local storage from server receipt.
- **NFR-005 Security:** least privilege, secure upload handling and secret management.
- **NFR-006 Privacy:** minimise personal data and restrict sensitive location/media.
- **NFR-007 Performance:** establish measurable targets using pilot hardware and expected load.
- **NFR-008 Portability:** maintain exportable database and media references.
- **NFR-009 Accessibility:** plain language, keyboard access, readable contrast and mobile usability.
- **NFR-010 Scientific integrity:** no automated output may be represented as verified causation or recovery without an approved evidential basis.
