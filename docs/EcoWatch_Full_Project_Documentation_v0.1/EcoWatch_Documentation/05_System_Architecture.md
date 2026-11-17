# 05 — System Architecture

**Status:** Logical architecture proposal; technology selection beyond PostgreSQL remains open.

## 1. Architecture goals

The architecture should support the five-stage process, preserve evidence, allow different data sources to enter one managed workflow, and make analytical components replaceable. It should be understandable and maintainable by a small beginner-led project team.

The initial system should favour a modular application over a large microservices architecture. Separate services should be introduced only when scale, reliability, security or team ownership justify the added operational complexity.

## 2. Logical architecture

### A. User and source interfaces
- Community reporting interface.
- Registered contributor interface.
- Reviewer and investigator workspace.
- Administrator interface.
- Data import interfaces for approved datasets and automated sources.

### B. Collection and ingestion
- Validate incoming forms and metadata.
- Receive file uploads.
- Record source and timestamps.
- Check file safety and format.
- Store original files in controlled file/object storage.
- Create observation records in PostgreSQL.
- Track failed or incomplete ingestion.

### C. Data management
- PostgreSQL stores structured records, relationships, workflow states and metadata.
- Geospatial support may be added through PostGIS after the spatial requirements are confirmed.
- A separate object-storage service is expected for large images, videos and documents; provider selection is open.
- Imported datasets should retain source, licence, version, date and processing history.

### D. Environmental intelligence
- Historical image comparison.
- Geospatial analysis.
- Indicator trend analysis.
- Report classification and grouping.
- Anomaly detection and evidence correlation.
- Explainable alerts and analytical summaries.

### E. Incident management
- Observation review.
- Case creation and linking.
- Evidence timeline.
- Assignment and investigation notes.
- Status and decision history.

### F. Response and recovery
- Action plans.
- Responsible parties.
- Milestones and field records.
- Outcome indicators.
- Follow-up monitoring.

### G. Verification and reporting
- Before/after comparison.
- Quality and uncertainty review.
- Outcome status.
- Reports for different audiences with access controls.

## 3. Information flow

1. A person or automated source submits an observation or dataset.
2. The ingestion process validates the submission and records provenance.
3. The original evidence is stored in controlled storage; structured metadata is recorded in PostgreSQL.
4. Automated checks may classify, extract or flag information.
5. Reviewers inspect the observation and decide whether it is relevant to an existing case or a new case.
6. Analysis may compare evidence across time, location and environmental domains.
7. Prioritisation supports a human decision about investigation or response.
8. Approved actions are recorded and monitored.
9. Verification compares outcomes against documented indicators.
10. New evidence updates the environmental history without erasing prior records.

## 4. Conceptual component boundaries

The five stages describe the operating process. The architecture describes the software components that support it. They are related but not identical. For example, user interfaces support all five stages rather than forming a separate environmental stage.

## 5. Proposed technology direction

| Area | Current position |
|---|---|
| Relational database | **PostgreSQL approved** |
| Spatial database extension | PostGIS proposed; approval pending |
| Backend framework | Python/FastAPI proposed; pending |
| Frontend | Next.js/React proposed; pending |
| Mobile access | Responsive web/PWA proposed; pending |
| File storage | S3-compatible object storage proposed; provider pending |
| Geospatial processing | Python geospatial tools proposed; methods pending |
| Background jobs | A job queue may be needed for heavy processing; technology pending |
| Maps | Open geospatial mapping approach to be evaluated |
| Hosting | Deferred until requirements, budget and operating model are known |
| Supabase/Firebase | Deferred to separate platform evaluation document |

These are candidates, not a locked stack. PostgreSQL is the only technology in this table explicitly approved.

## 6. Why avoid microservices initially?

A microservice design requires service discovery, network communication, distributed logging, deployment coordination, monitoring and more complex failure handling. Those costs are difficult to justify before the pilot's actual load and team structure are known.

A modular application can still separate responsibilities in code and database design. Components can later be extracted if there is evidence that separate scaling or independent deployment is necessary.

## 7. Architectural quality attributes

- **Traceability:** every analysis result can point back to source observations and datasets.
- **Modularity:** ingestion, analysis, case management and reporting have clear responsibilities.
- **Replaceability:** AI models and external providers can be changed without rewriting the entire system.
- **Security:** public reporting and restricted investigation workflows are separated.
- **Resilience:** long-running processing can be retried and monitored.
- **Portability:** structured data can be exported and interfaces documented.
- **Observability:** failures, processing delays and data-quality problems can be detected.

## 8. Key architecture risks

- Treating a dashboard as the whole product.
- Building AI before collecting a representative validation dataset.
- Making the system dependent on unavailable social-media APIs.
- Storing large media files directly in relational database rows.
- Allowing unreviewed reports to appear as confirmed incidents.
- Overengineering infrastructure before pilot usage is understood.
- Failing to assign an operational owner.

## 9. Architecture decisions still required

- Whether the pilot requires PostGIS from the first release.
- Backend and frontend framework selection.
- File storage and upload scanning approach.
- Identity and authentication design.
- Hosting region and backup strategy.
- External data ingestion schedule.
- Job processing and alert delivery.
- System monitoring and incident response.
