# 10 — Evidence Correlation and Incident Intelligence

**Status:** SignalWeave capability merger approved; redesigned algorithm and thresholds proposed.

## 1. Purpose

This subsystem finds candidate relationships among observations and evidence items. It reduces fragmentation and helps reviewers identify material that may belong in the same investigation. It does not establish truth, causation, legal responsibility or environmental severity.

## 2. Inputs and outputs

Inputs may include:
- Text descriptions and categories.
- Event/observation time and precision.
- Point or area geometry and location precision.
- Source type and source dependencies.
- Media metadata or derived visual features, if separately validated.
- Environmental context such as site, catchment or waterbody identifiers.

Outputs:
- Candidate relationship.
- Relationship type.
- Component scores or qualitative signals.
- Missing information.
- Explanation/reason codes.
- Method/model version.
- Review status.

## 3. Relationship types

Do not use one generic “same incident” link for every relationship. Candidate types include:
- Possible duplicate submission.
- Same-source repost or derivative.
- Similar report about the same suspected event.
- Same monitoring site, different observation time.
- Potentially related environmental observations.
- Possible upstream/downstream association.
- Shared case relevance.
- Contradictory or conflicting evidence.

Different relationship types require different criteria and validation.

## 4. Candidate generation

Avoid comparing every observation with every other observation. Use bounded candidate retrieval:
- Time windows appropriate to the process and observation type.
- Spatial indexes for nearby candidates where geometry is suitable.
- Shared site, catchment or waterbody identifiers where available.
- Text retrieval or embeddings for semantically similar descriptions.
- Source lineage to identify copied/reposted material.

Do not apply one fixed distance or time window to every environmental problem.

## 5. SignalWeave baseline scoring

The original SignalWeave prototype proposed:
- Semantic similarity: 0.40.
- Spatial proximity: 0.25.
- Temporal proximity: 0.25.
- Context: 0.10.

This is a prototype starting point only. It is not approved as EcoWatch's universal model. It was designed for reports of a developing incident and is too narrow for cumulative environmental processes, watershed connectivity and multi-source scientific evidence.

The original formula normalises weights over available signals. Missing values should be marked unavailable, not fabricated. The combined score is a ranking/similarity score, not a probability of truth.

## 6. Proposed redesigned approach

Use task-specific relationship models:
- **Duplicate detection:** same or near-identical content/media/source.
- **Same-event grouping:** semantic, temporal, spatial and contextual compatibility.
- **Environmental association:** environmental entity, process pathway, hydrological/ecological connectivity, time lag and supporting measurements.
- **Case relevance:** whether an observation may inform a case, even if it is not the same event.

For each task, define its own candidate rules, score semantics, evaluation dataset and thresholds. Avoid a single “universal EcoWatch score”.

## 7. Environmental spatial reasoning

Candidate spatial relationships:
- Proximity.
- Same site or monitoring station.
- Same waterbody.
- Same catchment/sub-catchment.
- Upstream/downstream network relation.
- Intersecting or adjacent land areas.
- Habitat or ecological corridor connectivity.

A spatial relationship must identify the source geometry/network and method. Straight-line proximity does not prove a hydrological connection.

## 8. Temporal reasoning

Different processes have different temporal patterns:
- Acute events may require narrow windows.
- Pollution transport may involve a time lag.
- Seasonal vegetation or water conditions require season-aware comparison.
- Cumulative degradation may develop over months or years.
- Restoration requires repeated follow-up observations.

Keep observed time separate from submission time. If only submission time is available, label it as a weak proxy.

## 9. Human review and clustering

Reviewers can accept, reject, mark ambiguous or request more evidence. Merge/split actions must preserve history and audit records. Avoid naive transitive clustering: A related to B and B related to C does not automatically prove A and C are the same event.

One observation may relate to multiple cases. Case membership should not erase alternative links.

## 10. Explainability

Every suggestion should show:
- Relationship type.
- Candidate records.
- Signals used and unavailable.
- Component values or qualitative evidence.
- Reasons for the suggestion.
- Method/model version.
- Known limitations.
- Review state.

## 11. Evaluation

Build labelled examples for each relationship task. Include:
- True related records with different wording.
- Similar wording in different places or periods.
- Same site but distinct events.
- Missing time/location.
- Upstream/downstream examples with known network context.
- Reposts and dependent reports.
- Ambiguous cases that should not be auto-linked.

Measure precision, recall, false links, missed links, ambiguity rate and reviewer correction rate. Evaluate across language, geography and source types. No model or threshold is approved until tested.

## 12. Safety boundary

No correlation result may automatically declare a pollution source, illegal activity, responsible party, environmental harm or recovery status.
