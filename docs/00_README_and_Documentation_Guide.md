# 00 — README and Documentation Guide

**Version:** 1.0 | **Status:** Merged design baseline

## 1. Purpose

This package combines the original EcoWatch documentation with the product and technical design of SignalWeave. SignalWeave is no longer a separate top-level product in the approved direction. Its useful capabilities are incorporated as EcoWatch's Evidence Correlation and Incident Intelligence subsystem.

The package describes product intent, workflows, requirements, architecture, data, scientific safeguards, governance, testing and staged implementation. It is not a build prompt, master prompt or claim of implementation.

## 2. Source documents reviewed

- SignalWeave `PRD.md`, version 1.0, hackathon MVP specification.
- SignalWeave `TECHNICAL.md`, version 1.0.
- EcoWatch documentation baseline v0.1, documents 00–19.

The merged baseline preserves key source principles:
- EcoWatch's five-stage lifecycle: Collect → Analyse → Prioritise → Intervene → Verify.
- Hybrid collection and anonymous as well as registered submissions.
- Distinct event, observation, submission and receipt times.
- PostgreSQL as the approved database technology.
- Observation/evidence records remain distinct from incidents/cases.
- Human review for consequential decisions.
- Evidence provenance and preservation.
- SignalWeave's explainable semantic, spatial, temporal and contextual correlation, offline-first reporting and analyst review.

## 3. Status vocabulary

- **Approved:** explicitly selected by the project owner.
- **Proposed:** recommended design awaiting explicit approval.
- **Assumption:** temporary planning premise that must be checked.
- **Open:** information or a decision is missing.
- **Deferred:** intentionally postponed.
- **Out of scope:** excluded from the current prototype/pilot unless scope changes.
- **Source-derived:** present in one of the supplied source packages.
- **Merged recommendation:** new synthesis or recommendation introduced by this package.

## 4. Approved product direction from 16 November 2026

1. SignalWeave becomes a core EcoWatch subsystem.
2. Long-term environmental scope covers land, water and interconnected ecosystems.
3. Evidence correlation, geospatial environmental analysis and environmental relationship/impact assessment are all strategic capabilities, developed in separate phases.
4. EcoWatch serves multiple roles: communities/reporters, researchers/investigators and organisations/institutions.
5. The prototype must be designed to evolve into a long-term product.
6. Monitoring, investigation/referral, intervention/restoration and verification form one connected lifecycle.

These decisions approve direction, not every detailed implementation choice.

## 5. Existing EcoWatch decisions retained

- Five-stage operating model.
- Hybrid data collection.
- Anonymous and registered submissions.
- Separate temporal fields.
- PostgreSQL.
- AI as decision support, not autonomous authority.
- Observations remain distinct from cases.
- Documentation-first development.
- No build/master prompts in this documentation package.
- Supabase and Firebase remain unselected and separately evaluated.

## 6. Document maintenance

When a requirement, scientific method, technology or product boundary changes:
1. Record the reason and decision owner.
2. Update the decision register.
3. Identify affected requirements, data definitions, architecture and tests.
4. Update diagrams and implementation backlog.
5. Record version and date.
6. Reassess security, privacy, scientific validity, cost and operational impact.

## 7. Limitations

The pilot geography, environmental indicators, thresholds, datasets, partners, retention schedule, legal controls, hosting provider and detailed technical stack remain open unless explicitly marked otherwise. Qualified Ghanaian environmental, legal, security and community stakeholders must review relevant parts before live operation.
