# 21 — Risks, Assumptions and Open Questions

**Status:** Initial register; must be reviewed during pilot definition.

## 1. Critical risks

| Risk | Why it matters | Proposed mitigation |
|---|---|---|
| Scope explosion | Broad environmental remit can overwhelm a small team | One bounded pilot area and a small number of indicators |
| False evidence correlation | Incorrect grouping may mislead investigators | Task-specific models, explanation, human review and labelled evaluation |
| False causal inference | Spatial/temporal association may be mistaken for source attribution | Explicit hypotheses, alternative explanations and expert review |
| Weak scientific data | Poor measurements can produce misleading outputs | Protocols, calibration, provenance and quality flags |
| Reporter exposure | Sensitive submissions may create retaliation risk | Identity separation, restricted access and safe reporting |
| Duplicate/dependent reports | Reposts can look like independent corroboration | Source lineage and dependency review |
| Model bias | Reporting coverage differs across communities | Coverage analysis and non-report-based indicators |
| Offline data loss | Field submissions may be lost or duplicated | Durable queue, idempotency and sync tests |
| Media breach | Uploaded evidence may contain sensitive information | Quarantine, access control and secure storage |
| Unfunded operations | Prototype may become unmaintained | Identify owner, cost and partner model before live pilot |

## 2. Assumptions to test

- A suitable pilot area has accessible historical and current data.
- Local experts can help select and interpret indicators.
- Community and institutional stakeholders see value in a shared workflow.
- A small set of data sources can be legally and practically reused.
- A real intervention or credible historical case can support lifecycle demonstration.
- The team can operate the selected stack and hosting within available resources.

None of these assumptions should be presented as confirmed until checked.

## 3. Open product questions

1. Which watershed/district or bounded geography is the pilot?
2. Which one environmental pressure/use case is first?
3. Which indicators can be collected consistently?
4. Who is the first operational user: community group, research team or institution?
5. Who is allowed to verify findings and approve public summaries?
6. What referral pathway exists when a case needs official action?
7. What is the safe process for sensitive or anonymous submissions?
8. What languages and accessibility needs apply?
9. What is the budget and operational owner?

## 4. Open technical questions

1. Is PostGIS approved for the database?
2. Is React/TypeScript + FastAPI the chosen application stack?
3. Which authentication and organisation model is appropriate?
4. Which object-storage provider and region are acceptable?
5. Which map tile/data services have suitable licences?
6. What is the initial deployment and backup plan?
7. What offline capabilities are essential in the first field test?
8. What data volume and image/raster workload should be expected?
9. Which processing jobs require separate workers?
10. What are the retention and deletion requirements?

## 5. Open scientific questions

1. Which environmental indicators are valid for the selected use case?
2. What sampling protocols, units and quality controls apply?
3. What baseline period and reference sites are defensible?
4. Which remote-sensing products have suitable resolution and coverage?
5. How will seasonality and rainfall be accounted for?
6. What evidence is needed to support a source/pathway/receptor hypothesis?
7. What criteria define outcome improvement or verified recovery?

## 6. Go/no-go rule

Do not start a live environmental pilot until the geography, problem, indicators, data permissions, review expertise, safety process, privacy controls and operational ownership are sufficiently defined.
