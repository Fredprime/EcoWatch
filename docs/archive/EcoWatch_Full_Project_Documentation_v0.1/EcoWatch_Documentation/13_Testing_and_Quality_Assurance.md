# 13 — Testing and Quality Assurance

**Status:** Quality principles defined; test plans and measurable thresholds must be created before implementation.

## 1. Purpose

EcoWatch must be tested not only as software but as an evidence-management and decision-support system. A working screen does not prove that environmental conclusions are correct.

## 2. Test categories

### Functional tests
Verify that reporting, uploads, timestamps, observations, cases, status changes, access permissions and intervention records behave as specified.

### Data integrity tests
Verify required fields, relationships, unique identifiers, units, date precision, provenance and audit history.

### Security tests
Test access control, upload handling, authentication, session management, injection risks, file access and administrative permissions.

### Usability tests
Observe representative users completing common tasks on mobile and desktop, including low-connectivity conditions.

### Performance tests
Measure common workflows using realistic data volumes and devices. Set targets only after the pilot's expected load is estimated.

### Backup and recovery tests
Restore database and file backups in a test environment and confirm records remain linked correctly.

### Analytical validation
Compare model or algorithm outputs against expert-reviewed reference data and record false positives, false negatives and limitations.

### Field and scientific quality checks
Review measurement methods, calibration, sampling location, seasonality, metadata and chain of custody where applicable.

## 3. Critical test scenarios

1. Anonymous user submits a report without a contact address.
2. Registered user submits a report and can view only their permitted records.
3. Observation date is earlier than submission and receipt dates.
4. User provides an approximate date; system preserves its uncertainty.
5. Upload is rejected safely when format or size is not allowed.
6. Duplicate upload does not silently create misleading independent evidence.
7. Two reports are linked to a case while remaining separate observations.
8. A reviewer reverses an incorrect case link and the history remains available.
9. AI suggestion is displayed as unverified.
10. A public view does not expose restricted contributor details.
11. A completed intervention is not automatically labelled verified recovery.
12. Database and media backup restoration preserves relationships.

## 4. Environmental analysis validation

For every analytical method:
- Define the target question.
- Identify source data and quality.
- Document preprocessing.
- Identify seasonal and sensor limitations.
- Compare outputs with independent or expert-reviewed evidence.
- Record uncertainty.
- Test on more than one date or site where feasible.
- Document cases where the method fails.

## 5. Acceptance gates

A feature should not be accepted until:
- Its requirement is identified.
- Expected behaviour is documented.
- Positive and negative tests pass.
- Security and privacy implications are reviewed.
- Known limitations are recorded.
- Relevant users or specialists review it.
- The release notes and documentation are updated.

## 6. Defect severity

- **Critical:** data exposure, loss/corruption of evidence, unauthorised consequential action, or system-wide failure.
- **High:** major workflow unavailable or serious incorrect case status/analysis.
- **Medium:** important feature impaired with workaround.
- **Low:** minor usability or presentation issue.

The project should define response and resolution targets once operational support is known.

## 7. Quality metrics

Potential measures include:
- Submission completion rate.
- Upload failure rate.
- Percentage of observations with usable date and location.
- Time from receipt to first review.
- Incorrect case-link rate.
- Analytical false-positive and false-negative rates.
- Percentage of interventions with baseline and follow-up measurements.
- Backup restore success.
- User task completion and reported confusion.

Do not optimise for raw report count alone.
