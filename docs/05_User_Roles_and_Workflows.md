# 05 — User Roles and Workflows

**Status:** Multi-role product direction approved; exact permission matrix proposed.

## 1. Role design principle

EcoWatch serves multiple groups, but not every user should see or change everything. Roles represent work responsibilities; permissions must be enforced by the backend, not merely hidden in the interface.

## 2. Candidate roles

| Role | Primary responsibility | Typical access |
|---|---|---|
| Anonymous contributor | Submit an observation without an account | Public reporting endpoint; own receipt/reference |
| Registered contributor | Submit and follow permitted reports | Own submissions and approved updates |
| Reviewer | Check quality and evidence relationships | Review queue, provenance, link suggestions |
| Investigator | Manage assigned cases | Case evidence, timeline, requests and findings |
| Environmental specialist | Review methods and environmental interpretation | Relevant datasets, analysis and technical notes |
| Intervention manager | Record authorised response activities | Approved interventions, milestones and evidence |
| Organisation administrator | Manage an organisation's users and assignments | Scoped organisation administration |
| System administrator | Operate platform configuration | Restricted technical administration and audit |

A person may hold multiple roles only where approved. Separation of duties should be considered for sensitive cases and verification decisions.

## 3. Workflow A — Anonymous community report

1. Reporter opens a mobile-friendly reporting page.
2. Selects a broad observation type or “not sure”.
3. Describes what was observed in plain language.
4. Adds approximate or exact location and date, if known.
5. Indicates whether the observation was firsthand.
6. Adds optional supporting media.
7. Reads the privacy and safety notice.
8. Submits; if offline, the client stores a local pending record where supported.
9. Receives a reference after server receipt. A locally queued item must not be described as received by EcoWatch.

## 4. Workflow B — Registered field observation

1. Authenticated contributor opens a field form.
2. Selects an observation protocol or free-form observation.
3. Enters location, observed time, method, units and instrument details where relevant.
4. Adds measurements and supporting evidence.
5. Submits and receives a server receipt.
6. Can view permitted status and clarification requests.

## 5. Workflow C — Evidence review and correlation

1. Reviewer opens unreviewed observations and candidate relationships.
2. Checks source, time precision, location precision, media provenance and possible duplication.
3. Reviews why the system suggested a link.
4. Accepts, rejects or marks ambiguous with a reason.
5. Links observations to one or more cases where justified.
6. Records any conflicts, missing information or follow-up request.
7. All decisions are audited and reversible through a new action; original records are retained.

## 6. Workflow D — Investigation

1. Investigator accepts or is assigned a case.
2. Reviews case summary, observations, evidence graph and timeline.
3. Defines investigation questions and evidence gaps.
4. Requests field verification, sampling or additional records.
5. Records findings, alternative explanations and uncertainty.
6. Updates case status with rationale.
7. Refers to an authorised organisation where appropriate.

## 7. Workflow E — Environmental analysis

1. Specialist selects a defined area, period and indicator.
2. Chooses suitable source datasets and records their versions.
3. Runs a documented analysis.
4. Reviews quality flags, seasonality, spatial coverage and method limitations.
5. Saves outputs as derived analytical artefacts linked to source data.
6. Adds interpretation as a separate reviewed record.

## 8. Workflow F — Intervention and verification

1. Authorised lead proposes or records an intervention.
2. Responsible organisation and approvals are recorded.
3. Baseline, intended outcome and monitoring plan are defined.
4. Activities and milestones are documented.
5. Follow-up observations and measurements are collected.
6. Qualified reviewer assesses outcome evidence.
7. Case is updated to recovery verified, inconclusive, no improvement or deterioration only where criteria support the status.

## 9. Public information workflow

Public summaries, if enabled, must be approved, carefully worded and stripped of sensitive contributor information, precise sensitive locations and unverified allegations. Publication is a governance decision, not an automatic consequence of submission.
