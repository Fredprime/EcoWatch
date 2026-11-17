# 08 — Environmental Intelligence and AI

**Status:** AI-assisted analysis is a core direction; specific models and methods remain unselected.

## 1. Purpose

AI should help EcoWatch interpret and organise evidence, identify patterns and support timely review. It should not be added merely to make the project appear advanced.

## 2. Three capability levels

### Detection
Identify possible features or changes in incoming information. Examples include classifying an image, extracting text from a report or flagging an unusual sensor reading.

### Analysis
Compare observations across time and location, examine trends, group potentially related reports and explore relationships among environmental indicators.

### Prediction
Estimate possible future conditions or risks under stated assumptions. Predictions must be labelled as estimates and validated against appropriate historical or field data.

## 3. AI across the five stages

| Stage | Possible AI assistance | Human responsibility |
|---|---|---|
| Collect | Extract metadata, classify files, flag missing fields | Confirm source, rights, relevance and quality |
| Analyse | Compare images, detect trends, group evidence, identify anomalies | Review method, context, uncertainty and alternative explanations |
| Prioritise | Summarise risk factors and rank cases using approved criteria | Set priorities and authorise decisions |
| Intervene | Summarise options and track action records | Select and authorise response |
| Verify | Compare indicator trends and flag possible recovery or deterioration | Review measurements and approve conclusions |

## 4. Environmental relationship analysis

EcoWatch may represent relationships among:
- Activities or pressures.
- Locations and watersheds.
- Land condition.
- Water condition.
- Vegetation and habitat.
- Species observations.
- Community and livelihood reports.
- Interventions.
- Environmental outcomes.

A relationship should carry:
- The entities or observations it connects.
- Relationship type.
- Supporting evidence.
- Date range.
- Method or reasoning.
- Confidence or uncertainty.
- Review status.

A relationship such as “land disturbance may be associated with downstream sediment change” must not be presented as established causation without suitable evidence.

## 5. Multi-report grouping

AI may suggest that several observations refer to the same event using time, location, content and media similarity. The system should:
- Preserve each original observation.
- Show why records were grouped.
- Identify possible reposts or shared sources.
- Allow reviewers to separate incorrectly grouped reports.
- Avoid treating dependent reports as independent corroboration.

Four people repeating one online claim do not necessarily provide four independent confirmations.

## 6. Explainable alerts

An alert should include:
- What changed or was reported.
- Where and when.
- Which data sources were used.
- The comparison period or baseline.
- Why the system flagged it.
- Confidence and known uncertainty.
- What is missing.
- Suggested review action.
- Current verification status.

An alert should not simply declare “illegal mining confirmed” based on a satellite image or social-media post.

## 7. Model validation

Before a model is used operationally:
1. Define the exact task and intended user.
2. Assemble a representative, permissioned dataset.
3. Establish expert-labelled reference examples where feasible.
4. Separate training, validation and test data appropriately.
5. Measure false positives and false negatives.
6. Check performance across seasons, locations, sensors and image conditions.
7. Record limitations and known failure modes.
8. Test how users interpret model output.
9. Monitor performance after release.
10. Provide a way to report and correct errors.

A high overall accuracy figure can conceal poor performance on rare but important cases. Metrics must match the task and consequences.

## 8. Uncertainty and status

Suggested distinctions:
- Automated lead.
- Needs review.
- Corroborated by additional evidence.
- Field verified.
- Disputed or conflicting evidence.
- Not substantiated.
- Resolved or under recovery monitoring.

The exact status workflow must be approved with stakeholders. AI cannot promote its own result to “field verified”.

## 9. Model governance

Record:
- Model or algorithm name and version.
- Input data identifiers.
- Processing date.
- Parameters and thresholds.
- Output and confidence representation.
- Known limitations.
- Human reviewer and decision.
- Changes to the model or method.

Avoid sending sensitive personal information or restricted evidence to third-party AI services without an approved data-protection and security assessment.

## 10. Sensible pilot strategy

Start with deterministic analysis and established geospatial methods where they are adequate. Add machine learning only when there is a defined task, enough suitable data and a way to validate performance. Do not train a custom model from scratch simply because AI is part of the project vision.

## 11. AI risks

- False alarms and missed events.
- Seasonal or sensor-related artefacts.
- Bias toward areas with more reports or better connectivity.
- Incorrect location or date extraction.
- Overconfidence in correlations.
- Re-identification of contributors.
- Model drift as environmental conditions or data sources change.
- Users treating model output as official proof.

Each risk requires controls, review and transparent communication.
