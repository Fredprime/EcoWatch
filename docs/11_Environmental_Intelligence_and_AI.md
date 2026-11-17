# 11 — Environmental Intelligence and AI

**Status:** Strategic capability approved; models, indicators and methods unselected.

## 1. Purpose

Environmental intelligence examines changes and relationships in land, water and ecosystems. It uses suitable measurements, geospatial data, historical records and specialist interpretation. AI is one tool among deterministic analysis, statistical methods, remote sensing and expert review.

## 2. Separate capability families

### A. Evidence correlation
Finds potentially related reports/observations. Inherits SignalWeave's core capability but redesigned for multiple relationship types.

### B. Geospatial environmental analysis
Analyses land cover, surface features, waterbody/catchment context, spatial patterns and change over time.

### C. Environmental relationship and impact assessment
Examines possible pathways among pressures, environmental conditions, receptors and reported impacts. It must distinguish association from causation.

### D. Prediction
Estimates future conditions only when sufficient representative data, a defined target and validation are available. Prediction is not required for the first prototype.

## 3. Three levels of analytical assistance

- **Detection:** flag possible features, unusual readings, missing values or change.
- **Analysis:** compare datasets, trends, spatial patterns and candidate relationships.
- **Prediction:** estimate possible future conditions under stated assumptions.

Each output must identify which level it represents.

## 4. Environmental relationship model

A relationship record should include:
- Entities/observations connected.
- Relationship type.
- Spatial and temporal scope.
- Supporting evidence.
- Method and version.
- Confidence/uncertainty representation.
- Alternative explanations.
- Human review state.

Example: “Land disturbance in an upstream sub-catchment may be associated with increased downstream sediment observations during the same rainfall period.” This is a hypothesis until supported by appropriate measurements and investigation.

## 5. Candidate indicator domains

| Domain | Candidate indicators | Limitations |
|---|---|---|
| Land | Land-cover change, bare soil, disturbed area, erosion features | Imagery may not identify cause or legal status |
| Water | Turbidity, pH, conductivity, dissolved oxygen, selected contaminants, flow | Requires appropriate sampling, units, calibration and quality control |
| Vegetation | Cover, fragmentation, vegetation condition | Seasonal and sensor effects |
| Habitat/biodiversity | Habitat condition, species observations | Specialist survey protocols and taxonomic review |
| Weather/hydrology | Rainfall, temperature, flow, flood context | Contextual variables do not independently establish pollution source |
| Community/livelihood | Reported access, farming/fishing impacts | Reports must not be conflated with ecological measurements |

The pilot must select a small set of indicators with a feasible source and repeatable method.

## 6. Remote sensing principles

For imagery-derived analysis, record:
- Sensor/platform and product.
- Acquisition date and processing level.
- Spatial resolution and coordinate reference system.
- Cloud/shadow and quality masks.
- Algorithm and parameters.
- Seasonal context.
- Known limitations.
- Human review and interpretation.

A visible land-cover change is not automatically evidence of illegal mining, pollution or ecological impact.

## 7. Model validation

Before operational use:
1. Define task and intended decision.
2. Obtain permissioned representative data.
3. Create expert-reviewed reference labels where feasible.
4. Separate training, validation and test data by location/time as appropriate.
5. Measure false positives and false negatives.
6. Test across seasons, sensors, locations and source quality.
7. Record limitations and failure cases.
8. Assess how users interpret outputs.
9. Monitor drift and revalidate after changes.

## 8. Model governance

Record model/method name and version, input identifiers, execution time, parameters, output, uncertainty, limitations, reviewer and resulting decision. Avoid sending restricted personal or evidence data to external AI services without approved assessment.

## 9. Implementation order

1. Data quality and provenance.
2. Deterministic validation and simple descriptive analysis.
3. Evidence correlation with labelled evaluation.
4. Selected geospatial change workflow.
5. Environmental relationship analysis.
6. Prediction only if evidence and validation justify it.

## 10. Non-goals

Do not train a large model from scratch for appearance. Do not use an LLM to invent scientific conclusions. Do not present model-generated summaries as verified findings. Do not equate a confidence score with probability unless calibrated and validated for that exact task.
