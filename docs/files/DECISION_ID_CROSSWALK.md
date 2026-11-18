# Decision ID Crosswalk

**Status:** Explanation of a live defect, not a decision record. Read before citing any decision ID.

## 1. The problem in one paragraph

This repository now contains **three different decision-ID schemes that share the same ID range but mean different things**. `docs/files/` (the v0.8 correlation design) cites `DR-001`–`DR-041`. Those IDs resolve to nothing: no `DR-*` register exists anywhere in this repository. Meanwhile two *different* `ADR-` registers exist — the canonical one in `docs/20_Technical_Decision_Records.md` (`ADR-001`–`ADR-027`) and the pre-merge one in `docs/archive/EcoWatch_Full_Project_Documentation_v0.1/EcoWatch_Documentation/16_Technical_Decision_Records.md` (`ADR-001`–`ADR-017`) — and several numbers collide.

| ID | Canonical `docs/20` means | Archived v0.1 means | Same decision? |
|---|---|---|---|
| ADR-005 | PostgreSQL | PostgreSQL | ✅ yes |
| ADR-006 | SignalWeave becomes a subsystem | Evaluate Supabase separately | ❌ no |
| ADR-008 | Bounded pilot geography | Bounded pilot geography | ✅ yes |
| ADR-009 | Multi-role platform | PostGIS | ❌ no |
| ADR-011 | One connected lifecycle | Next.js/React candidate | ❌ no |
| ADR-014 | React + TypeScript | AI is decision support | ❌ no |
| ADR-016 | PostGIS | Documentation before implementation | ❌ no |
| ADR-017 | MapLibre | Do not create build prompts | ❌ no |

## 2. Rules that follow

1. **Only `ADR-*` from `docs/20_Technical_Decision_Records.md` is citable.** Never cite an archived ADR by number.
2. **`DR-*` IDs in `docs/files/` are historical labels, not references.** Do not resolve them, do not extend the sequence, and do not introduce `DR-*` in new documents.
3. **When a `docs/files/` statement matters for the build, restate it in canonical language** with an `ADR-*` reference or with plain text — do not copy the `DR-*` ID forward.
4. Do not rewrite the archived documents to fix their IDs. History is not rewritten; this file is the translation layer.

## 3. What can be resolved from context in `docs/files/`

Only where the subject is unambiguous. Everything else is unresolved and must be treated as a design note, not an approved decision.

| `DR-*` cited | Subject in context | Canonical position | Basis |
|---|---|---|---|
| DR-004 | Four separate times | `ADR-004` | Same subject, same meaning |
| DR-005 | Only PostgreSQL is approved | `ADR-005` | Same subject |
| DR-008 | PostGIS | `ADR-016` | Renumbered in canonical register |
| DR-015 | Stack tools are candidates, not approval | `ADR-014`, `ADR-015`, `ADR-016` | Same subject, split across three records |
| DR-017 | Hackathon MVP becomes phased full system | `ADR-010` (prototype evolves), roadmap `docs/04` §6 | Related, not identical |
| DR-018 | No seeded, sample or demo data | `docs/AGENT_GUIDE.md` §5, `docs/OWNER_RULES.md` §6 | Boundary, not an ADR |
| DR-027, DR-037 | No broker/queue/microservice initially | `ADR-013` | Same subject |
| DR-032, DR-040 | Provisional cluster is not a case | `ADR-022`, `docs/12` §2 | Same subject, human review |
| DR-035 | Merge direction approved | `ADR-006` | Same decision, later date |
| DR-036 | Correlation runs locally, no hosted AI | `ADR-019` (model Proposed), `docs/11` §8 | Related, not identical |
| DR-041 | Live demonstration vs no seed data | Open — `docs/files/23` §6.1 | Owner decision outstanding |
| DR-001–003, 006, 007, 009–014, 016, 019–026 | SignalWeave-era internals (input rules, weights, categories, statuses) | Superseded by `docs/06`, `docs/10`, `docs/12` | Merged baseline wins |
| DR-023, DR-024 | Public has no login; staff submit | **Conflicts** with `ADR-003` (anonymous + registered submissions) | Canonical wins: `ADR-003` |

## 4. Two known contradictions this crosswalk surfaces

1. **Public accounts.** `docs/files/23` §3 says the public has no login and staff submit from a Staff area; canonical `ADR-003` and `FR-001` require anonymous **and registered** contributor submissions. Canonical wins. If the owner actually wants public-only-anonymous, that is a new ADR superseding `ADR-003` — it is not something a v0.8 design note can do quietly.
2. **Requirement numbering.** `docs/files/23` §2 maps SignalWeave requirements onto `FR-015`, `FR-031`–`FR-038`, `FR-048`–`FR-065`, `FR-060`, `FR-063` — numbers from the archived 70-requirement set, which do not exist in canonical `docs/06` (58 requirements). Those mappings cannot be used for traceability. Rebuild any FR mapping from `docs/06` directly.
