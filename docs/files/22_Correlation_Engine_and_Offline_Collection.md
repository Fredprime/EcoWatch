# 22 — Correlation Engine and Offline-First Collection

**Status:** Proposed design (v0.8), merged from the SignalWeave product requirements and technical design. The merge itself is Approved (DR-035). Models, weights, thresholds and providers are Proposed or Open. No example, demo or seed data is part of this design.

## 1. Purpose and fit
EcoWatch receives many separate reports about the same developing condition. They arrive in different words, at different times, from different places, and some lack a location or time. The **SignalWeave correlation engine** is the part of EcoWatch that finds related reports, groups them into suggested clusters, explains why, and shows them to Staff for review. The **offline-first collection layer** lets people capture reports with poor connectivity and sends them safely later.

| Five-stage activity | Contribution |
|---|---|
| Collect | Offline capture, safe retry, idempotent intake, bandwidth priority |
| Analyse | Candidate search, explainable correlation, suggested clusters |
| Prioritise | Cluster size, evidence quality and confidence feed the transparent rubric (never the sole input) |

SignalWeave is a working component name and Open to change (DR-035).

## 2. Terminology map
| SignalWeave term | EcoWatch term |
|---|---|
| Report | Observation |
| Incident or cluster | Case (a suggested cluster is a provisional case until Staff review it) |
| Evidence relationship | Case link |
| Reporter | Member of the public (no login) |
| Analyst or operator | Staff (workers and analysts) |
| Administrator | Admin |
| `event_time` | `observed_at` and `event_start_at` |
| Server `submitted_at` | `received_at` |
| `sync_status` | Client submission state (not a substitute for server receipt) |

## 3. Boundaries
The engine organises and surfaces evidence. It does not verify that a report is true, certify an event, determine legal responsibility, dispatch anyone, or act as an emergency service. It does not identify people in photographs, use facial recognition or track individuals, and it does not train a foundation model. Core correlation does not depend on a hosted AI service. Every machine suggestion is labelled unverified and needs a human decision.

## 4. Two levels of linking
- **Level 1, same-condition correlation (this document):** are these reports about the same event or condition? It uses meaning, place, time and category.
- **Level 2, environmental relationship analysis (document 08):** how may land, water, vegetation and livelihoods be connected? It needs expert-reviewed method and never claims causation from correlation scores.

Reports about a slow process, such as land disturbance over months or water changes along a river, will not fit the short time and small distance scales that suit a sudden local event. Scales are therefore set per category with expert input (Open).

## 5. Processing sequence
1. The client creates a unique ID and stores the report locally.
2. The client sends it with that ID as its duplicate-protection key.
3. The server validates, stores the report once, records `received_at`, and returns a receipt immediately.
4. The report is marked pending correlation.
5. A bounded background worker claims pending reports.
6. The worker retrieves candidates by place and time.
7. The correlation service scores available signals.
8. Suggestions and explanations are stored; a provisional cluster is created or updated.
9. A small notification goes to open Staff dashboards, which fetch the authoritative detail.
The person is never made to wait for correlation before getting a receipt.

## 6. Candidate generation
Do not compare every report with every other. Narrow first:
- **With a location:** reports and clusters within a configurable radius and event-time window, excluding rejected relationships and, by rule, closed cases.
- **Without a location:** a wider but bounded time window over a limited recent set; the result is marked lower-context and is never grouped overconfidently.
- **Category-aware** where category data is reliable: radius and window depend on category.
PostGIS-style spatial search is what makes this efficient, which strengthens the case for approving PostGIS (DR-008, still Proposed).

## 7. Signals
| Signal | What it measures | Notes |
|---|---|---|
| S, semantic | Similarity of description meaning | Compact local sentence-embedding model (Proposed); embeddings cached; text normalised; empty or oversized text rejected |
| D, spatial | Closeness of places | Distance decay with a configurable, per-category scale; unavailable if either point is missing |
| T, temporal | Closeness of observation times | Prefers `observed_at`; `submitted_at` only as a weaker proxy, and the explanation says so |
| C, context | Category agreement or compatibility | Simple rules only; no entity extraction is claimed until built and tested |
A deterministic keyword fallback may exist for testing when the model cannot load. It is labelled as fallback and never presented as equivalent.

Distance decay: `D = exp(-distance / distance_scale)`. Time decay: `T = exp(-time_difference / time_scale)`.

## 8. Combined score
`score = (wS*S + wD*D + wT*T + wC*C) / (sum of the weights of the signals that are available)`

- Missing signals are left out of the denominator, never invented, and the interface says the score used fewer signals.
- Starting weights to be tuned on real reviewed data, not established values: semantic 0.40, spatial 0.25, temporal 0.25, context 0.10.
- Starting bands, configurable: 0.75 and above strong candidate; 0.50 to 0.74 possible; below 0.50 not attached automatically. Even a strong candidate needs human review.
- The score is a ranking signal. It is never described as a probability that an event is real.
- Weights, bands and scales are recorded with every result so any score can be reproduced.

## 9. Cluster assignment
For each new report: generate candidate clusters; score against each using representative evidence plus cluster-level place and time; rank; if the best exceeds the suggestion threshold, record a suggested relationship; otherwise create a new provisional cluster. If several candidates score closely, flag the ambiguity for Staff rather than choosing silently. **No naive transitive merging:** if A matches B and B matches C, A and C are not assumed to match; pairwise evidence and cluster limits stay visible.

A **provisional cluster is not a case.** It lives only in the Staff area, counts for nothing in prioritisation, and is never public until Staff promote it to a case (DR-040). Affected clusters are re-evaluated when new reports arrive or Staff change a relationship.

## 10. Explanation record
Each suggestion stores: combined score; each component score; reason statements in plain words; the list of missing signals; the weights, bands and scales used; model and method version; status (suggested, accepted, rejected); reviewer, time and note. Rejected suggestions are kept in history, never deleted.

## 11. Human review
Staff can accept or reject a suggested relationship, view all evidence in a cluster, promote a provisional cluster to a case, merge two clusters or cases, and split a cluster. Every action records who and when, and originals are untouched. Staff cannot review their own staff-submitted observations (DR-026). Merge and split need a permission check and an audit event. Staff can flag abusive, duplicate or sensitive reports; hiding a report from view is an Admin action; nothing is deleted from evidence.

## 12. Offline-first collection
### Client behaviour
- Save each report on the device before any upload attempt.
- Create a unique client ID at the moment of creation.
- Show states: queued, syncing, submitted, failed. "Saved on this device" is not "received by EcoWatch".
- Retry temporary failures with growing delays and some randomness.
- Stop automatic retries on permanent validation errors and tell the person what to fix.
- Send text, location and times first; send images afterwards and separately.
- Compress images and enforce a size limit before upload, and validate again on the server.
- Fetch only changes and details on demand, not full histories.
- A web app uses the browser's durable storage for the queue; a native collector would use its own local database (technology Proposed).

### Server behaviour
- The client ID is a unique key, so a retry returns the existing receipt instead of a duplicate.
- A receipt is returned as soon as the report is durably stored.
- Correlation is asynchronous and safe to retry.
- Processing state lives in the database so a restarted worker resumes.

### Bandwidth priority
1. Report text and ID. 2. Location and times. 3. Small metadata. 4. Compressed image. 5. Optional extra media.

### Times when offline
`submitted_at` is the device time when the person pressed submit and may be wrong; `received_at` is the server time and is authoritative. The gap is shown to reviewers, not hidden.

### Privacy of the local queue
A queued report may sit on a shared or borrowed phone. Store only what is needed, never reporter identity, clear entries once received, tell the person what is stored, and warn about shared devices.

## 13. Background processing
A small, bounded worker inside the application takes a batch of pending reports from the database, claims each safely so two workers never take the same one, marks it processing, correlates, stores results and marks it processed. Recoverable failures return it to pending with a retry time and an attempt count; repeated failure marks it failed with a safe status visible to Admin. Model inference concurrency is bounded and the model loads once at start. No message broker, task queue or microservice is added initially (DR-027, DR-037); this is not a substitute for a distributed task system if load grows, and that is reviewed then.

## 14. Realtime updates
Small notifications push to open Staff dashboards, and the dashboard then fetches the authoritative record. The notification is never the source of truth. One application instance is assumed at first; a shared event broker is added only if several instances run. The Public area receives no pushed notifications.

## 15. Images
Images are supporting evidence first, never the sole basis of correlation. Safeguards: size and format limits; verify file signatures, not just names or reported types; generated storage names; strip sensitive metadata from public and working copies while keeping the original and recording extracted metadata as unverified; never execute uploads; keep access controlled. Image classification or similarity is a later phase and does not delay text, place and time correlation. An image does not prove when or where it was taken.

## 16. Interfaces (conceptual)
Versioned operations, with Staff operations behind sign-in and server-side permission checks:
- Public: submit an observation (accepted after durable receipt); check a report by tracking code; add follow-up information through the tracking code, kept as an amendment (Could); health check.
- Staff: list clusters and cases with bounded filters (status, category, time, confidence band); get detail with relationships, reports, explanations and timeline; review a relationship; reject a relationship; merge; split; flag.
- Admin: hide or restore a report from view; worker and health status; configuration of weights, bands and scales with audit.
Public intake is rate-limited. All inputs are validated with strict bounds. Report text is untrusted data, never instructions.

## 17. Staff dashboard
Overview of provisional and active clusters and recent reports; map and an equivalent list; cluster detail with status, confidence, summary and evidence; timeline distinguishing observation time from received time; review panel with component scores and reasons and accept or reject controls; filters. Labels and icons accompany colour. Confidence is never shown as a danger level. Screen records are in document 20.

## 18. Performance design targets (Proposed, to be measured)
- Receipt does not depend on model inference.
- Warm correlation fast path of about 250 ms for a small candidate set, and dashboard visibility of a new report within about 500 ms, under documented test conditions.
- Bounded queues; no unbounded task creation.
Measure and record receipt latency, queue wait, candidate count, inference time, scoring time, database write time and end-to-end time. These are design targets, not claims, and no target is considered met until measured on the actual hosting setup.

## 19. Evaluation and quality
Metrics: precision of suggested links; recall of related pairs; false-merge rate; staff review time per case; sync correctness (each queued report arrives exactly once); end-to-end latency; whether staff can see why a link was suggested.

**Evaluation data policy (DR-018):** no seeded, sample or invented dataset, no demonstration script and no sample media are added. Tests that need records create temporary ones in the test environment and delete them afterwards. Real evaluation data comes from real, consented, Staff-reviewed relationship decisions made during use, stored with their retention rules and used only after the owner approves how they are used. Because Staff mostly review what the engine suggests, a periodic random sample of unsuggested pairs is also reviewed so recall is not overstated. Until enough real decisions exist, correlation is shown to Staff only as a clearly labelled suggestion with no accuracy claim, and the minimum evidence required before wider reliance is Open.

## 20. Known limitations
Similarity scores are not truth scores or calibrated probabilities. Reports can be false, malicious, duplicated or mistaken. A pin may be approximate or misleading. Sparse evidence can make correct correlation impossible. A compact text model may perform unevenly on local languages, slang and mixed-language reports, so language support is tested before it is relied on. Image processing does not establish time or place. Human review remains essential.

## 21. Phase placement
Phase 1 (collection foundation): idempotent intake, offline queue and states, safe retry, image rules. Phase 2 (intelligence): candidate search, scoring, provisional clusters, explanation, review, realtime notifications, evaluation. Merge and split, image similarity and further signals follow within Phase 2 or 3 as capacity allows.

## 22. Open questions
Which embedding model and whether an optimised runtime is used; per-category scales, weights and bands; which languages must be supported; minimum evidence before wider reliance; whether followers can add information through tracking codes; retention of review decisions used for evaluation; who may change engine configuration.
