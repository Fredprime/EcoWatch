# 07 — Data Collection and Evidence Management

**Status:** Hybrid collection, anonymous/registered submissions and separate timestamps are confirmed design directions.

## 1. Purpose

This document defines how EcoWatch should receive, validate, preserve and organise information from different sources.

## 2. Hybrid collection model

EcoWatch will support two broad entry routes into one managed collection process.

### Automated and institutional sources
Examples:
- Satellite imagery and derived products.
- Approved drone imagery.
- Environmental sensors.
- Weather and rainfall records.
- Scientific and government datasets.
- Research reports and structured monitoring data.

### Direct human submissions
Examples:
- Community observations.
- Environmental officer reports.
- Researcher field observations.
- Photographs and videos.
- Documents and laboratory reports.
- Public online environmental information collected through permitted methods.

Both routes feed a shared ingestion and evidence-management workflow. They do not automatically have equal evidential strength. Quality depends on method, source, timing, location, calibration, independence and corroboration.

## 3. Anonymous and registered submissions

### Anonymous
A person can submit information without creating an account. The system should not require a name merely to accept a useful observation.

Limitations should be explained: without a contact method, EcoWatch may be unable to ask follow-up questions or notify the contributor of progress.

### Registered
A registered contributor may be able to follow submissions, provide follow-up evidence and view submission history. Registration should not automatically make their identity public.

### Institutional
A future institutional workflow may associate records with an organisation and named authorised staff. This requires role, authority and accountability design.

## 4. Submission fields

A structured submission may include:
- What was observed.
- Environmental category.
- Where it occurred.
- When it was observed.
- Whether the date is exact, approximate, a range or unknown.
- Whether the contributor witnessed it directly.
- Supporting photographs, videos or documents.
- Optional contact details for follow-up.
- Consent and privacy notices appropriate to the use.

Avoid asking for unnecessary personal details. Do not request information that could put a reporter at risk.

## 5. Four time concepts

EcoWatch should distinguish:

1. **`event_start_at`:** when the problem is believed to have started. This may be unknown or estimated and must carry a source and confidence.
2. **`observed_at`:** when the contributor says they witnessed or recorded the condition.
3. **`submitted_at`:** when the contributor submitted the information to EcoWatch.
4. **`received_at`:** when the EcoWatch server successfully received and recorded it.

Example: a contributor says a photograph was taken on the 1st and uploads it on the 4th. EcoWatch preserves the stated observation date and the actual server receipt date separately.

The earliest report found is not necessarily the beginning of the environmental problem.

## 6. Date accuracy

Support:
- Exact date/time.
- Approximate date or period.
- Date range.
- Relative description such as “earlier this month”.
- Unknown.

Store the original wording where useful. Do not silently turn an approximate date into an exact timestamp.

Device metadata such as EXIF can be useful but may be missing, altered, incorrectly configured or inconsistent. It is a source to assess, not unquestionable proof.

## 7. Evidence preservation

- Preserve the original uploaded file in restricted storage.
- Generate previews or analysis derivatives separately.
- Record checksums where appropriate to help detect file changes.
- Record metadata extraction and security scanning outcomes.
- Do not overwrite original evidence with compressed, cropped, annotated or AI-edited versions.
- Restrict access to sensitive files.
- Record who accessed or changed sensitive evidence where appropriate.

## 8. Validation and ingestion pipeline

1. Receive submission.
2. Validate required fields and permitted formats.
3. Apply file-size and file-type limits.
4. Scan or quarantine files using an appropriate security process.
5. Record submission and receipt timestamps.
6. Store original evidence securely.
7. Extract permitted metadata into separate fields.
8. Create the observation record.
9. Run optional automated classification or quality checks.
10. Queue for human review where required.
11. Record errors and allow safe retry.

## 9. Social and public digital information

Public online information may provide useful leads, but public visibility does not mean unrestricted reuse or automated access. EcoWatch must respect platform terms, applicable law, privacy expectations and access controls.

Important distinctions:
- Post date is not necessarily capture date.
- Uploader location is not necessarily incident location.
- Reposted material is not independent corroboration.
- A caption is a claim, not a measurement.
- A photograph may not show the whole environmental context.

The pilot should not depend on unrestricted access to social-media APIs. Direct community reporting and permitted data sources are more controllable starting points.

## 10. Offline-friendly collection

Offline submission is a useful future capability for areas with unreliable connectivity. It requires careful handling of local device time, later server receipt time, queued uploads, duplicate prevention and secure local storage. It should be designed and tested explicitly rather than assumed to work automatically.

## 11. Evidence quality dimensions

Reviewers should consider:
- Source identity or source type.
- Firsthand versus secondhand account.
- Original versus reposted evidence.
- Date precision and consistency.
- Location precision.
- Measurement method and calibration.
- Image or document quality.
- Independence from other reports.
- Corroboration by other evidence.
- Known limitations or conflicts.

No single numerical score should hide these dimensions.

## 12. Data rights and permissions

Before importing or publishing a dataset or media item, record its source, permitted use, licence or terms, attribution requirements, geographic/time coverage and any restrictions. Obtain appropriate permission for drone imagery and sensitive field data. Contributors should be told how their submissions may be used.
