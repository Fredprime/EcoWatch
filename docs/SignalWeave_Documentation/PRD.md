# SignalWeave — Product Requirements Document

**Version:** 1.0  
**Status:** Hackathon MVP specification  
**Product type:** Offline-first, AI-assisted incident intelligence platform

## 1. Product summary

SignalWeave turns fragmented community reports into coherent, evidence-backed incident intelligence.

People often report the same developing situation through separate messages, photographs, locations and timestamps. Those reports may look unrelated because they use different wording, arrive at different times, or describe different parts of an event. SignalWeave correlates the available evidence, groups likely related reports, estimates confidence and presents the developing incident on a map and timeline for human review.

**Example:** One person reports water entering a road; another uploads a photograph of a submerged junction; a third reports that vehicles cannot pass nearby. SignalWeave can identify that these reports may describe one flooding incident rather than three unrelated events.

SignalWeave is a decision-support and situational-awareness tool. It does not independently declare emergencies, verify truth, dispatch responders or replace official emergency services.

## 2. Problem statement

During fast-moving local incidents:

- Reports are scattered across channels and submitted in inconsistent formats.
- Different witnesses describe the same event using different words.
- Reports may lack complete location or time information.
- Duplicate reports create noise, while genuinely related reports can be missed.
- Decision-makers lack a consolidated view of what is happening, where, when and what evidence supports it.
- Poor or intermittent connectivity makes reporting and synchronisation difficult.

The result is fragmented situational awareness and slower human assessment.

## 3. Product vision

Provide a lightweight platform that converts separate reports into a continuously updated, explainable picture of developing incidents, even when connectivity is unreliable.

### Product principles

1. **Evidence before automation:** show the reports and signals behind every suggested relationship.
2. **Human-in-the-loop:** operators review, confirm, reject, merge and split incident clusters.
3. **Explainability:** show why two reports were linked and how confidence was calculated.
4. **Connectivity resilience:** allow reports to be captured offline and synchronised later.
5. **Privacy by design:** collect only what is needed and avoid exposing reporter identity.
6. **Graceful uncertainty:** missing or conflicting information must reduce confidence, not be silently invented.

## 4. Goals and non-goals

### Goals

- Accept structured and unstructured incident reports containing text, time, location and optional images.
- Find candidate reports that may refer to the same real-world event.
- Correlate reports using semantic, spatial, temporal and contextual signals.
- Group related reports into incident clusters.
- Produce a transparent confidence score and reasons for each suggested link.
- Display incidents, reports and evidence on an interactive map and timeline.
- Support human review and correction of automated suggestions.
- Queue reports during connectivity loss and synchronise them safely later.
- Demonstrate the complete workflow on a small, realistic dataset.

### Non-goals for the hackathon MVP

- Replacing emergency dispatch, police, fire or medical systems.
- Automatically sending responders or issuing public emergency alerts.
- Predicting disasters or claiming to forecast an event.
- Identifying people in photographs, performing facial recognition or tracking individuals.
- Training a new foundation model.
- Depending on a hosted LLM for core correlation.
- Building a nationwide production-grade emergency network.
- Integrating with every social network or messaging platform.
- Guaranteeing the truth of user-submitted reports.

## 5. Target users and roles

### Reporter
A community member or field observer who submits a report.

**Needs:** simple reporting, minimal data usage, clear submission status and the ability to submit when offline.

### Analyst / operator
A person monitoring incoming reports and reviewing suggested incidents.

**Needs:** a prioritised incident queue, map and timeline, evidence provenance, confidence explanations, and tools to correct clusters.

### Administrator
A trusted person managing access and system configuration.

**Needs:** user and role management, audit history, report moderation and basic system health visibility.

For the hackathon demonstration, reporter and analyst workflows are essential. A basic administrator role is desirable if time permits.

## 6. Core user journeys

### Journey A — Submit a report

1. Reporter opens the reporting interface.
2. Reporter enters a short description.
3. Reporter adds a location using device location or a map pin; location may be omitted.
4. Reporter confirms the event time or accepts the captured submission time.
5. Reporter optionally attaches a photograph.
6. The client validates the report and assigns a unique client-generated ID.
7. If online, it submits the report. If offline, it stores the report in a local queue.
8. The interface shows whether the report is queued, synchronising, received or failed.

### Journey B — Correlate incoming reports

1. Backend validates and stores a received report.
2. The correlation engine retrieves plausible candidates using available time and geographic information.
3. It compares report text semantically and evaluates spatial, temporal and contextual compatibility.
4. It generates explainable pairwise scores.
5. A report is suggested for an existing incident, or a new provisional incident is created.
6. The dashboard updates with the new report and its suggested relationship.

### Journey C — Review an incident

1. Analyst opens the incident queue or selects an incident on the map.
2. Analyst sees the incident summary, status, confidence, timeline and contributing reports.
3. Analyst opens the explanation for a linked report.
4. Analyst accepts or rejects the suggested relationship, or merges/splits clusters.
5. The system records the decision and updates the incident view.
6. The original reports and audit history remain available.

## 7. Functional requirements

Priority definitions: **P0** = essential for the hackathon demonstration; **P1** = important if time permits; **P2** = future enhancement.

### 7.1 Report intake

- **FR-01 (P0):** Accept a report with description, client-generated ID and submission timestamp.
- **FR-02 (P0):** Accept optional latitude/longitude and event timestamp.
- **FR-03 (P0):** Accept an optional image attachment with file type and size validation.
- **FR-04 (P0):** Validate coordinates, timestamps, text length and attachment constraints.
- **FR-05 (P0):** Make report submission idempotent so retries do not create duplicate records.
- **FR-06 (P1):** Support report categories such as flooding, fire, road obstruction, infrastructure damage and other.
- **FR-07 (P1):** Allow a reporter to correct a report before it is reviewed, while preserving an audit record.

### 7.2 Correlation and clustering

- **FR-08 (P0):** Generate semantic similarity between report descriptions.
- **FR-09 (P0):** Calculate spatial proximity when both reports have valid coordinates.
- **FR-10 (P0):** Calculate temporal proximity when both reports have usable event times.
- **FR-11 (P0):** Combine available signals into an explainable correlation score.
- **FR-12 (P0):** Use geographic and temporal candidate filtering to avoid comparing every report with every other report.
- **FR-13 (P0):** Suggest an existing incident or create a provisional incident for a new report.
- **FR-14 (P0):** Store the score components and explanation for each suggested report-to-incident relationship.
- **FR-15 (P1):** Support category and named-entity/context compatibility as additional signals.
- **FR-16 (P1):** Re-evaluate affected clusters when new reports arrive or an analyst changes a relationship.

### 7.3 Human review

- **FR-17 (P0):** Allow an analyst to accept or reject a suggested report-to-incident relationship.
- **FR-18 (P0):** Allow an analyst to view all evidence associated with an incident.
- **FR-19 (P1):** Allow authorised analysts to merge two incidents.
- **FR-20 (P1):** Allow authorised analysts to split a cluster when reports have been grouped incorrectly.
- **FR-21 (P1):** Record who made a review decision and when.

### 7.4 Dashboard and visualisation

- **FR-22 (P0):** Display incidents on an interactive map.
- **FR-23 (P0):** Display incident details and contributing reports.
- **FR-24 (P0):** Display a chronological timeline of reports within an incident.
- **FR-25 (P0):** Show confidence and the reasons behind suggested relationships.
- **FR-26 (P0):** Update the dashboard when new reports or review decisions arrive.
- **FR-27 (P1):** Filter by incident status, category, time range and confidence band.

### 7.5 Offline and low-connectivity support

- **FR-28 (P0):** Allow report composition and local queuing when the network is unavailable.
- **FR-29 (P0):** Retry queued reports with exponential backoff when connectivity returns.
- **FR-30 (P0):** Use stable client-generated IDs and idempotency keys to prevent duplicates.
- **FR-31 (P0):** Send text and coordinates before optional image uploads.
- **FR-32 (P1):** Compress images before upload and support upload size limits.
- **FR-33 (P1):** Show pending, synchronising, submitted and failed states.
- **FR-34 (P1):** Resume interrupted uploads where the chosen storage implementation supports it.

### 7.6 Administration and safety

- **FR-35 (P0):** Distinguish provisional, analyst-reviewed and closed incidents.
- **FR-36 (P0):** Clearly label machine-generated suggestions as unverified.
- **FR-37 (P0):** Keep reporter identity private from ordinary dashboard viewers.
- **FR-38 (P1):** Provide role-based access for reporter, analyst and administrator.
- **FR-39 (P1):** Maintain an audit trail for analyst actions.
- **FR-40 (P1):** Allow an administrator to hide or flag abusive, duplicate or sensitive reports.

## 8. Correlation model and confidence

SignalWeave must not treat semantic similarity alone as proof that two reports describe the same event. Two reports can use similar language while describing separate incidents.

For each candidate pair, calculate available signals:

- **S — Semantic similarity:** similarity between text embeddings.
- **D — Distance compatibility:** how geographically close the reports are.
- **T — Temporal compatibility:** how close their event times are.
- **C — Context compatibility:** category, extracted entities or other available contextual clues.

A simple initial score is:

`score = (wS*S + wD*D + wT*T + wC*C) / (sum of weights for available signals)`

The weights are configurable and must be documented. Missing information is excluded from the denominator rather than fabricated. If a signal is unavailable, the interface should disclose that the score was calculated from fewer signals.

Initial illustrative weights for a prototype:

- Semantic: 0.40
- Spatial: 0.25
- Temporal: 0.25
- Context: 0.10

These are starting values for validation, not scientifically established weights. The team must tune them against its demonstration dataset.

### Initial decision bands

- **0.75–1.00:** strong candidate; still requires human review.
- **0.50–0.74:** possible relationship; show for analyst consideration.
- **Below 0.50:** do not automatically attach; retain as a separate/provisional report.

Thresholds must be configurable. A high score is a ranking signal, not a probability that an incident is real.

### Spatial and temporal decay

A practical first implementation can use distance and time decay functions. For example:

`D = exp(-distance_km / distance_scale_km)`

`T = exp(-time_difference_minutes / time_scale_minutes)`

The scale parameters should depend on the incident category and be configurable. A road obstruction and a large-area flood should not necessarily use identical spatial thresholds.

## 9. Data requirements

### Report
- `id`: UUID, unique and stable across retries.
- `description`: report text.
- `category`: optional controlled category.
- `event_time`: optional time the event was observed or occurred.
- `submitted_at`: server receipt time.
- `latitude`, `longitude`: optional coordinates.
- `attachment_ids`: optional image references.
- `reporter_id`: internal/private reference where authentication is enabled.
- `sync_status`: client-side state, not a substitute for server receipt status.

### Incident
- `id`: UUID.
- `title`: concise generated or analyst-edited label.
- `summary`: concise evidence-based description.
- `category`: optional category.
- `status`: provisional, under_review, confirmed_by_analyst, rejected or closed.
- `created_at`, `updated_at`.
- `centroid`: calculated from valid contributing report coordinates, if available.
- `confidence_score`: current correlation/cluster score with an explanation of its meaning.

### Evidence relationship
- `report_id`, `incident_id`.
- `score`, `score_components`.
- `relationship_status`: suggested, accepted or rejected.
- `created_at`, `reviewed_at`, `reviewed_by`.

### Audit event
- `id`, `actor_id`, `action`, `target_type`, `target_id`, `metadata`, `created_at`.

## 10. Non-functional requirements

### Performance
- Keep report intake responsive and avoid running heavy model inference in the HTTP request path.
- Target a fast-path correlation response around 250 ms for a warm, small local demonstration workload, excluding image upload and cold model startup.
- Target dashboard visibility of a newly accepted report within roughly 500 ms under the same controlled demonstration conditions.
- Measure and report actual latency; these are prototype targets, not production guarantees.
- Use bounded queues and sensible upload limits.

### Reliability
- Do not lose a locally queued report when the app is refreshed or briefly disconnected.
- Make retries safe through idempotency.
- Preserve original report evidence when clusters are merged, split or corrected.
- Handle missing location, time or image data without failing the whole report.

### Scalability
- Use database indexes and candidate filtering before semantic comparison.
- Keep model inference behind an interface so it can be optimised or replaced.
- Avoid premature microservices and distributed infrastructure in the hackathon MVP.

### Security and privacy
- Validate all user input and uploaded file types.
- Enforce upload size limits and generate server-side storage names.
- Do not trust client-supplied filenames or MIME types.
- Restrict analyst and administrator actions by role.
- Avoid exposing reporter contact details or exact identity in public views.
- Use HTTPS in deployed environments and protect secrets with environment variables.
- Apply retention rules to uploaded images and sensitive metadata.
- Treat reports and images as untrusted data; do not execute or interpret embedded content as instructions.

### Accessibility and usability
- Make report submission short and usable on mobile screens.
- Use clear text labels, not colour alone, for status and confidence.
- Provide map/list alternatives for users who cannot use the map.

## 11. Success metrics

For the hackathon, evaluate the product on a labelled demonstration dataset:

- **Correlation precision:** of the suggested links, how many are correct?
- **Correlation recall:** of the known related report pairs, how many are found?
- **False-merge rate:** how often are unrelated reports grouped together?
- **Review time:** how long does an analyst take to understand a sample incident?
- **Sync correctness:** are queued reports eventually submitted once, without duplicates?
- **End-to-end latency:** time from server receipt to visible dashboard update.
- **Explainability:** can the analyst see why a report was linked?

A strong demonstration should show both a successful cluster and a deliberately misleading pair that the system keeps separate or flags as uncertain.

## 12. MVP scope and delivery order

### Must build (P0)
1. Report submission with text, optional location/time and optional image.
2. PostgreSQL persistence.
3. Candidate filtering by time and geography.
4. Semantic similarity and weighted correlation score.
5. Provisional incident creation and report grouping.
6. Analyst dashboard with map, incident detail and evidence timeline.
7. Accept/reject relationship controls.
8. Offline report queue and safe retry.
9. A seeded demonstration dataset and repeatable demo script.

### Should build (P1)
- Category/context signal.
- Image compression.
- Incident merge/split.
- Audit history and basic role-based access.
- Filters and improved moderation.

### Later
- Multi-source ingestion connectors.
- Advanced image understanding.
- Model fine-tuning with consented, labelled data.
- More sophisticated geospatial event models.
- Production-grade multi-region availability and integrations with official systems.

## 13. Demo acceptance criteria

The MVP is ready to demonstrate when:

1. A user can submit at least three reports describing one simulated event with different wording.
2. SignalWeave identifies them as likely related and shows the contributing evidence.
3. A separate, nearby but unrelated report is not silently merged into that incident.
4. The analyst can inspect why a relationship was suggested and accept or reject it.
5. The map and timeline update when a new report is received.
6. A report created while offline is queued and synchronised after connectivity returns without duplication.
7. The interface clearly distinguishes machine suggestions from analyst-reviewed status.
8. The demo can run locally without requiring a hosted LLM or external AI API.

## 14. Assumptions and risks

### Assumptions
- The hackathon prototype can use a small seeded dataset and controlled scenarios.
- The team can obtain or create consent-safe sample reports and images.
- A laptop CPU is the primary inference target; GPU is optional.
- The initial deployment can be a single application environment.

### Risks and mitigations
- **False correlation:** use multiple signals, conservative thresholds and human review.
- **Sparse or inaccurate locations:** allow missing coordinates and display uncertainty.
- **Poor connectivity:** local queue, retries, idempotency and prioritised text/location sync.
- **Model download/internet dependency:** cache model artefacts before the demo and provide a deterministic fallback/test mode.
- **Scope creep:** protect P0 requirements; defer advanced vision and integrations.
- **Sensitive or misleading reports:** label unverified evidence and restrict public exposure.

## 15. Product boundary

SignalWeave organises and surfaces evidence. It does not certify reports as true, determine legal responsibility, diagnose emergencies, or make dispatch decisions. Any real-world response must remain with authorised human operators and official services.
