# 11 — User Interface and User Experience

**Status:** Design principles and user groups identified; screen designs and workflows remain to be approved.

## 1. Purpose

The interface should make environmental reporting and investigation understandable to people with different levels of technical experience. It should not overwhelm a community reporter with scientific fields or expose restricted information through public views.

## 2. Interface areas

### Community reporting
A simple path to describe an observation, provide location and date information, attach evidence and submit anonymously or while signed in.

### Contributor area
For registered contributors to view their own submissions and follow-up requests where permitted.

### Review workspace
For authorised reviewers to inspect evidence, check provenance, request clarification, link observations to cases and update statuses.

### Case workspace
A consolidated view of the case summary, map, evidence, timeline, analysis, review history and next actions.

### Intervention workspace
For authorised users to record response plans, milestones, field evidence and outcome monitoring.

### Public information view
Where approved, provide carefully limited summaries, maps and progress information without exposing reporter identity, sensitive sites or unverified allegations.

### Administration
Manage accounts, roles, controlled vocabularies, data imports, audit logs and system configuration.

## 3. User journeys

### Anonymous report
1. Open reporting page.
2. Choose an observation category.
3. Describe what was observed.
4. Provide location and date precision.
5. Attach evidence if available.
6. Review privacy notice and submit.
7. Receive a reference code or confirmation that does not expose sensitive information.

### Registered report
The same steps, with the additional ability to associate the report with the account and view permitted status updates.

### Reviewer
1. Open review queue.
2. Inspect new observations.
3. Check date, location, source and evidence.
4. Identify missing or conflicting information.
5. Link to a case or create a new case.
6. Record rationale and next action.

### Investigator
1. Open assigned case.
2. Review evidence and timeline.
3. Identify data gaps.
4. Request field verification or additional measurements.
5. Record findings and update status.

### Intervention manager
1. Review an approved response plan.
2. Record activities and milestones.
3. Attach supporting evidence.
4. Enter outcome measurements.
5. Submit for verification.

## 4. Design principles

- Mobile-first for community submissions.
- Plain language and short explanations.
- Do not require a user to understand the five-stage model to submit a report.
- Clearly identify required and optional fields.
- Support approximate dates and uncertain locations.
- Explain what happens after submission.
- Use status labels consistently.
- Make AI-generated content visibly distinct from reviewed findings.
- Provide accessible contrast, labels and keyboard navigation.
- Avoid maps as the only way to provide or interpret location.
- Explain why personal information is requested.

## 5. Location and privacy

The interface should warn users not to put themselves at risk to obtain evidence. Do not encourage trespassing, confrontation or unsafe field activity. Public maps may need location generalisation to protect contributors, vulnerable communities or sensitive ecological sites.

## 6. Language and accessibility

The pilot should determine the languages needed through community consultation. Use clear language and consider local-language support where resources permit. Translation should be reviewed by fluent speakers; machine translation alone may distort environmental terms or reports.

## 7. Error and offline states

Users should receive clear messages when:
- Uploads fail.
- A file type is unsupported.
- Location is unavailable.
- A date is uncertain.
- Connectivity is lost.
- A queued submission has not yet reached the server.

If offline submission is later implemented, the interface must distinguish “saved on this device” from “received by EcoWatch”.

## 8. Interface validation

Test with representative users, including people with limited digital literacy and users on lower-cost mobile devices. Observe task completion, misunderstandings, accidental disclosure and abandonment. Do not assume that a technically functional form is usable.
