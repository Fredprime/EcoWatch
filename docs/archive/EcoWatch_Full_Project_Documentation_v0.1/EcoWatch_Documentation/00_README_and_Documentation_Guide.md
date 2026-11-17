# EcoWatch — Project Documentation Package

**Package version:** 0.1  
**Document status:** Initial consolidated design baseline  
**Prepared:** 9 November 2026  
**Project name:** EcoWatch (working name)  
**Development approach:** Design and documentation before implementation or deployment  
**Audience:** Project owner, future developers, environmental specialists, community partners, reviewers and potential institutional partners

## 1. Purpose of this package

This package records the current EcoWatch concept, its environmental purpose, the five-stage operating model, approved decisions, proposed architecture, requirements, data principles, AI responsibilities, safeguards, and the work that remains undecided.

It is intended to be a usable project baseline, not a claim that the system has already been built, tested, scientifically validated, deployed, or adopted by any institution.

## 2. Important status convention

Every significant statement should be interpreted using the following statuses:

- **Approved:** explicitly selected or confirmed by the project owner.
- **Proposed:** a recommendation that still needs review and approval.
- **Assumption:** temporarily used for planning but not yet verified.
- **Open:** requires an answer or evidence before the relevant design can be finalised.
- **Deferred:** intentionally postponed to a separate document or later phase.
- **Out of scope:** deliberately excluded from the current pilot.

Do not silently turn a proposed technology, pilot location, feature, partnership, or scientific method into an approved decision.

## 3. Current confirmed decisions

1. EcoWatch is intended to address real environmental problems and remain useful beyond a hackathon.
2. The foundational operating process is **Collect → Analyse → Prioritise → Intervene → Verify**.
3. The concept should consider connected environmental effects rather than treating land, water, ecosystems and livelihoods as unrelated subjects.
4. The proposed data collection model is **hybrid**: automated sources and direct human submissions feed a shared collection process.
5. Both anonymous and registered submissions are to be supported.
6. Reports and uploaded evidence must preserve separate event/observation/submission/receipt times where known.
7. **PostgreSQL is approved** as the database technology.
8. Supabase and Firebase are not selected for the pilot. Their evaluation belongs in a separate future document.
9. The user has chosen a design-first approach and identifies as a beginner in programming.
10. No build prompts, master prompts or coding-agent prompt packages are to be produced as part of this documentation work.
11. Deployment and implementation are not to begin merely because this documentation package exists.

## 4. What is not yet approved

- The first pilot watershed or district.
- A final list of pilot indicators and scientific thresholds.
- Whether PostGIS is included in the first implementation (recommended, but still to be explicitly approved).
- The frontend, backend, hosting provider, object-storage provider and authentication provider.
- Whether Supabase, Firebase or another managed platform should be used.
- Specific satellite-processing workflows, AI models or model providers.
- Exact user roles, partner organisations, data-sharing agreements and retention periods.
- The pilot budget, operational owner and long-term funding model.

## 5. Package contents

| File | Purpose |
|---|---|
| 00 README and Documentation Guide | How to read and maintain the package |
| 01 Project Overview and Vision | What EcoWatch is and why it exists |
| 02 Environmental Problem Analysis | Environmental problem framing and evidence needs |
| 03 Scope and Objectives | Pilot boundaries, objectives and exclusions |
| 04 Requirements Specification | Functional and non-functional requirements |
| 05 System Architecture | Logical components and information flow |
| 06 Database and Data Architecture | PostgreSQL data principles and conceptual entities |
| 07 Data Collection and Evidence Management | Submission, ingestion, provenance and timestamps |
| 08 Environmental Intelligence and AI | Responsible analytical and AI capabilities |
| 09 Incident Investigation and Historical Reconstruction | Observation-to-case workflow and timelines |
| 10 Intervention and Recovery Management | Response planning and restoration tracking |
| 11 User Interface and User Experience | User journeys and interface principles |
| 12 Security, Privacy and Governance | Data protection, access, safety and accountability |
| 13 Testing and Quality Assurance | Verification strategy and acceptance criteria |
| 14 Deployment and Infrastructure | Deployment design considerations, not deployment instructions |
| 15 Maintenance and Future Expansion | Operations, sustainability and growth |
| 16 Technical Decision Records | Decisions, rationale and alternatives |
| 17 Change History and References | Document governance and research register |
| 18 Deferred Platform Evaluation Brief | Separate future evaluation of Supabase, Firebase and alternatives |

## 6. How to use the documents

Read documents 01–03 first to understand the purpose and boundaries. Documents 04–12 describe what the system should do and the principles behind its design. Documents 13–15 explain how quality, deployment and long-term operation should be approached. Documents 16–18 record decisions and future evaluations.

The documents are connected. A change to scope may affect requirements, architecture, data structures, testing and cost. Update the affected documents together and record the reason in the change history.

## 7. Important limitation

This is a design baseline based on the decisions and ideas discussed so far. It is not a completed environmental impact assessment, legal opinion, security audit, scientific protocol, procurement specification or operational agreement. Environmental indicators, thresholds, data licences, legal obligations and partner arrangements must be reviewed with qualified local experts before field use.

## 8. Documentation rule

For every important decision, record:
- What is being decided.
- Why it is needed.
- How it is expected to work.
- Alternatives considered.
- Benefits and trade-offs.
- Dependencies and risks.
- What evidence would verify that it works.
- Its approval status and the person authorised to approve it.
