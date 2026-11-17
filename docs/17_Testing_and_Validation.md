# 17 — Testing and Validation

**Status:** Quality strategy defined; test data and numerical acceptance thresholds open.

## 1. Two kinds of correctness

EcoWatch requires both software correctness and evidential/scientific validity. A successful API test does not prove a correlation is meaningful. A visually plausible map does not prove an environmental interpretation is correct.

## 2. Software test categories

- Unit: validation, time precision, scoring, spatial helpers, permission checks.
- Integration: API/database, media storage, processing jobs, case links and audit.
- End-to-end: report to review to case to intervention/verification workflow.
- Offline: local queue persistence, retry, duplicate prevention and interrupted media upload.
- Security: authentication, authorisation, upload safety, injection, access leakage and secret handling.
- Usability: representative user task completion and comprehension.
- Performance: realistic data volumes, candidate counts, upload sizes and analytical jobs.
- Recovery: database and media backup restoration.

## 3. Correlation evaluation

Build labelled datasets for each relationship task. Include true matches, hard negatives, same wording in different locations, same site at different times, missing data, dependent reposts and ambiguous cases.

Measure precision, recall, false-positive rate, false-negative rate, ambiguity rate, reviewer override rate and processing latency. Evaluate by source type, language, geography and season where data permits.

Do not use one aggregate accuracy number as the only quality measure.

## 4. Environmental analysis validation

For each analysis:
- Define the environmental question.
- Document input source and version.
- Check coordinate reference systems, units and time periods.
- Apply quality masks and data-quality checks.
- Compare with field measurements or expert-reviewed references where possible.
- Test seasonality and alternative explanations.
- Record uncertainty and known limitations.
- Make the workflow reproducible.

## 5. Intervention verification

Check that baseline and follow-up methods are comparable, dates are appropriate, seasonal effects are considered, measurement quality is known and outcome claims match the evidence. Activity completion and ecological recovery must be tested as separate concepts.

## 6. Acceptance evidence

A feature is not accepted solely because it runs. Attach test results, labelled examples, reviewer sign-off, method/version, limitations and unresolved defects.

## 7. Release gates

Do not expose live community reporting until:
- Access controls and upload protections pass review.
- Privacy notice and retention policy are approved.
- Backup/restore is tested.
- Incident response ownership is assigned.
- User-facing safety guidance is approved.
- Pilot data permissions are confirmed.
- Critical workflows pass acceptance tests.
