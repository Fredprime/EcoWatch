# 09 — Evidence Collection and Provenance

**Status:** Hybrid collection and provenance principles approved; detailed protocols open.

## 1. Sources

Potential sources:
- Anonymous and registered community reports.
- Field-team observations.
- Sensor and IoT readings.
- Laboratory measurements.
- Satellite and aerial imagery where permitted.
- Public institutional datasets and reports.
- Research datasets.
- Weather, rainfall and hydrological data.
- Approved partner feeds.

Each source has different authority, accuracy, coverage and permission conditions.

## 2. Observation form

Collect only what is necessary:
- What was observed or measured?
- Where did it occur?
- When was it observed?
- Is the date exact, approximate, a range or unknown?
- Is the report firsthand?
- What method or instrument was used?
- What units apply?
- What supporting media or document exists?
- Can the contributor be contacted, if they choose?
- What consent and privacy terms apply?

Do not encourage trespassing, confrontation or unsafe evidence collection.

## 3. Four core time concepts

1. `event_start_at`: when the problem is believed to have started; may be estimated or unknown.
2. `observed_at`: when the contributor/instrument observed the condition.
3. `submitted_at`: when the contributor submitted it.
4. `received_at`: when the server received and recorded it.

Store precision, source and original wording where relevant. The earliest report found is not necessarily the start of the environmental problem.

## 4. Evidence preservation

- Preserve original uploaded files in restricted storage.
- Generate previews and analysis derivatives separately.
- Calculate checksums where appropriate.
- Record metadata extraction and security scanning outcomes.
- Do not overwrite originals with compressed, cropped, annotated or AI-modified copies.
- Restrict sensitive files.
- Record access or change events for high-risk evidence where appropriate.

SignalWeave's original idea of stripping EXIF must not be applied destructively to the only copy. Sensitive metadata may be restricted or removed from public derivatives while the original is preserved under access controls, subject to the approved privacy policy.

## 5. Ingestion pipeline

1. Receive request and idempotency key.
2. Validate payload and permissions.
3. Validate file type by content, not extension alone.
4. Apply size limits and quarantine/scanning process.
5. Record server receipt time.
6. Store original evidence securely.
7. Extract permitted metadata separately.
8. Create observation and provenance records.
9. Queue optional processing.
10. Return durable receipt.
11. Process asynchronously and record status/errors.

## 6. Independence and corroboration

Multiple submissions do not necessarily mean multiple independent sources. Reposts, shared photographs, copied captions and coordinated reports may be dependent. Record known source relationships and do not count duplicated claims as independent corroboration.

## 7. Data rights

For each imported dataset or media item, record:
- Provider/owner.
- Source and acquisition date.
- Licence and terms.
- Attribution requirements.
- Geographic and temporal coverage.
- Resolution and method.
- Known limitations.
- Retention and redistribution restrictions.

Public accessibility does not automatically grant unrestricted reuse. Drone imagery and sensitive field data require particular attention to permission and safety.

## 8. Offline collection

Offline support should:
- Save a draft locally before network transmission.
- Use a stable client-generated UUID.
- Display local-only, queued, syncing, received and failed states.
- Retry transient failures with backoff and jitter.
- Avoid retrying permanent validation errors without correction.
- Upload text/location before large media when appropriate.
- Preserve local device time separately from server receipt time.
- Protect local data on shared or lost devices as far as practical.

For a web PWA, IndexedDB is the candidate durable queue. Offline support must be explicitly tested; it must not be assumed merely because a service worker exists.
