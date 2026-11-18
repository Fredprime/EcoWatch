# 22 — Change History and References

**Status:** Initial merged record.

## 1. Document control

Package version 1.0. Stable document identifiers are used. Each material revision should record date, owner, status and summary.

## 2. Change history

| Version | Date | Change |
|---|---|---|
| 0.1 | 9 Nov 2026 | Initial EcoWatch documentation baseline. |
| 1.0 | 16 Nov 2026 | Merged SignalWeave PRD and technical design into EcoWatch; incorporated six owner decisions; added subsystem boundaries, revised evidence model, phased roadmap and merged requirements. |
| 1.1 | 18 Nov 2026 | Implemented Phase 1 backend (`backend/` core platform, intake, provenance, jobs, and case foundation) per `ADR-026`–`ADR-029`, added `PERMISSIONS_MATRIX.md`, `BACKEND_ARCHITECTURE_AND_3_PHASE_PLAN.md`, and updated `docs/08` for Phase 1. |

## 3. Source packages reviewed

- SignalWeave Documentation ZIP: `PRD.md` and `TECHNICAL.md`, version 1.0.
- EcoWatch Full Project Documentation v0.1: documents 00–19 and `START_HERE.md`.

## 4. Candidate external references to investigate

These are research starting points, not confirmation that a dataset is suitable, available, free or licensed for the intended use:
- USGS Landsat mission and product documentation.
- Copernicus Sentinel data and product documentation.
- Ghanaian environmental, water, forestry, mining and hydrological agencies' published datasets and reports.
- Global Forest Watch data and methodology.
- Peer-reviewed work on Ghanaian watersheds, mining impacts, water quality, land-use change, ecology and restoration.
- Official PostgreSQL and PostGIS documentation.
- Official documentation for any selected hosting, storage, mapping and authentication provider.

## 5. Source register requirements

For each source, record title, organisation, URL/document reference, access date, licence/terms, geographic and temporal coverage, resolution, method, known limitations and the EcoWatch feature/analysis using it.

## 6. Scientific reference quality

Prefer primary datasets, official technical documentation, peer-reviewed research and qualified local expertise. News and social media may identify leads but should not substitute for scientific measurements or authoritative records.

## 7. Verification note

Canonical docs `00`–`24` describe the overall design baseline; Phase 1 backend code in `backend/` implements the Phase 1 foundation per `ADR-029`, while Phases 2–3, `frontend/`, legal/privacy governance sign-off, and live pilot deployment remain unimplemented.
