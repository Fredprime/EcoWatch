# Archive — superseded documentation

Nothing in this folder is a current instruction. Everything here predates the merged baseline in `docs/00`–`24` and is kept only so decisions can be traced.

## What is here, and why it is here

| Folder | What it is | Why it is not canonical |
|---|---|---|
| `EcoWatch_Full_Project_Documentation_v0.1/` | The original EcoWatch baseline (20 documents, `00`–`19`, prepared 9 Nov 2026), written before SignalWeave was merged in. | Pre-merge. Different document titles, different requirement IDs (its `04_Requirements_Specification.md` runs to FR-070 against the canonical 58), and its own `ADR-001`–`ADR-017` register whose IDs *collide with different meanings* in the canonical `docs/20` (its ADR-009 is PostGIS; canonical ADR-009 is multi-role platform). |
| `SignalWeave_Documentation/` | `PRD.md` and `TECHNICAL.md` v1.0 — the original separate-project specification. | SignalWeave is no longer a separate product. Its capabilities were merged as Evidence Correlation and Incident Intelligence (ADR-006). It also contains the seeded demo data, demo script and build prompts that EcoWatch explicitly excludes. |

## Rules for anything in this folder

1. **Never cite these as authority.** Canonical source is `docs/00`–`24`, indexed by `docs/START_HERE.md`; decisions are `docs/20_Technical_Decision_Records.md`.
2. **Never copy a requirement ID out of here.** Old FR numbers and old ADR numbers do not mean what the canonical numbers mean.
3. **No agents read this folder by default.** `AGENTS.md` at the repo root sends them to the canonical set.
4. History is not rewritten. If one of these documents was wrong, the correction belongs in the canonical set with its own record.

The still-useful material from `docs/files/` (the v0.8 correlation engine design) is *not* archived: it carries implementation detail the merged baseline lacks, and is cited as a secondary source. It has its own decision-ID problem, documented in `docs/files/DECISION_ID_CROSSWALK.md`.
