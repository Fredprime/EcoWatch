# 19 — Operations and Maintenance

**Status:** Operational principles defined; owners and funding open.

## 1. Ownership required before live pilot

Identify:
- Product owner.
- Technical maintainer.
- Data steward.
- Environmental/scientific reviewer.
- Case-review lead.
- Security/privacy contact.
- Field/intervention partner where applicable.

A small team may combine roles, but accountability must remain explicit.

## 2. Routine operations

- Monitor API, database and storage health.
- Review failed processing jobs and imports.
- Check backup completion and restore capability.
- Patch dependencies and operating systems.
- Review user access and privileged accounts.
- Respond to correction and deletion requests.
- Check external data availability and licence changes.
- Review correlation errors and model drift.
- Track storage, bandwidth and compute costs.
- Update documentation after material changes.

## 3. Data stewardship

Maintain source metadata, versions, access rights, quality notes, retention and correction history. Imported datasets must remain traceable after refreshes or transformations.

## 4. Model and method maintenance

Monitor sensor/product changes, seasonal effects, geographic performance, source coverage, thresholds and failure patterns. Revalidate before expanding to a new geography or environmental problem.

## 5. Incident response

Define who receives reports, disables compromised accounts, contains exposed data, preserves logs/evidence, notifies affected parties where required and tracks corrective action.

## 6. Portability and exit

Maintain schema documentation, database exports, media references, source metadata and reproducible analysis records. Avoid dependence on one provider or individual without a migration plan.

## 7. Sustainability

Potential models include institutional partnerships, research collaboration, grants or public-sector support. No funding or partnership is assumed. The pilot must identify who will operate the system after the prototype phase.
