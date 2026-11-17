# EcoWatch Owner Rules

**Version:** 1.0  
**Last Updated:** 2026-11-17  
**Maintainer / Owner:** Fredprime  
**Scope:** Explicit working rules given by the project owner for all agents and contributors working on EcoWatch.

---

## 1. Purpose and Precedence

This document records the explicit rules given by the project owner across sessions. When working on this repository, follow this order of precedence:

1. Explicit instructions from the owner for the current task (recorded here as they are given).
2. Canonical merged documentation in `docs/00`–`docs/24` (`docs/START_HERE.md`) and approved records in `docs/20_Technical_Decision_Records.md`.
3. `docs/EcoWatch Agent Guide.md` and `CONTRIBUTING.md`.
4. General engineering defaults (YAGNI, minimal structured code paths, native platform capabilities first).

---

## 2. Project Scope and Build Rules

1. **Merged project:** Work on the merged EcoWatch project (`docs/00`–`24` canonical baseline, where SignalWeave is integrated as EcoWatch's Evidence Correlation and Incident Intelligence subsystem). Historical packages (`docs/EcoWatch_Full_Project_Documentation_v0.1/`, `docs/SignalWeave_Documentation/`) are reference only.
2. **Build from scratch:** Nothing in the application (`backend/`, `frontend/`) has been built yet; build cleanly from scratch against the merged documentation and repository infrastructure baseline.
3. **Three-phase backend structure:** Structure the backend build into 3 phases (`Phase 1: Core/Intake/Cases`, `Phase 2: ECII Correlation/Worker/Offline Sync`, `Phase 3: Environmental Intelligence/Prioritisation/Interventions/Verification`) and document the architecture in `docs/` before writing code.
4. **Documentation-before-code discipline:** Do not write application code until documentation review and explicit go-ahead are given; when tasked with docs-only work, modify and push only `docs/` files.
5. **Architectural decisions first:** Record significant architectural/stack decisions as ADRs in `docs/20_Technical_Decision_Records.md` before landing code.

---

## 3. Repository, Git, and Branching Rules

1. **Work inside the cloned repository:** All ongoing project work lives in `Fredprime/EcoWatch`.
2. **Exclude archive zips:** Do not commit `.zip` documentation archives (`docs.zip`, `EcoWatch_Documentation.zip`) into the repository.
3. **Never push directly to `main` or `master`:**
   - `main` is the protected release branch (sacred; linear history; PR + approval + CI required).
   - `master` is the integration branch (PR target; `infra / compose + postgis` CI + approval required).
   - Keep the GitHub protections applied via `scripts/protect-branches.sh` active.
4. **Work on branch `prime`:** Make changes on branch `prime` (branched from `master`), review, and push to `prime` (then PR into `master` when ready for integration).
5. **Preserve branches:** Do not delete branches after merging unless the owner explicitly asks (`delete_branch_on_merge=false`).
6. **Commit format:** Use conventional commits `type(scope): summary` (imperative, <= 72 chars) per `CONTRIBUTING.md`.

---

## 4. Documentation, Tracking, and Review Rules

1. **Single review document (`docs/REVIEW_SUMMARY.md`):** Maintain one concise, single-stop review document summarizing current status, changes made, and decisions awaiting owner review.
2. **Separate owner rules document (`docs/OWNER_RULES.md`):** Record every new rule given by the owner in this file as the project progresses.
3. **Project tracking (`docs/PROJECT_TRACKING.md`):** Maintain an up-to-date record of what has been done, what is in progress, and what is left to be done.
4. **Document every change:** Document all meaningful actions, structural changes, and implementation changes as they occur.

---

## 5. Agent Execution and Engineering Rules

1. **Dispatch work to subagents:** Delegate bounded research, implementation, verification, and documentation tasks to subagents where parallel or isolated execution helps.
2. **Lazy senior developer / YAGNI discipline:**
   - Never overengineer; apply YAGNI strictly.
   - Prioritize native platform capabilities before importing external libraries.
   - Reuse existing repository utilities, conventions, and modules instead of duplicating logic.
   - Write minimal, highly structured code paths.
3. **Formatting and style:**
   - No emojis in code, documents, or interfaces unless explicitly required by project documentation.
   - Follow `docs/EcoWatch Agent Guide.md` naming and interface conventions (confirming DB-to-API boundary rules before coding).

---

## 6. Non-Negotiable Product Safety and Integrity Rules

1. **No seeded, sample, or demo data** in the product; tests create temporary records and remove them afterwards.
2. **Decision support only:** Automated correlation and AI outputs never declare pollution sources, illegal activity, legal responsibility, causation, harm, `"field verified"`, or `"recovery verified"`.
3. **Original evidence immutability:** Original observations and uploaded evidence files remain untouched; corrections create versions and derivatives are separate files.
4. **Identity and location privacy:** Contributor identity is stored separately from public views; precise sensitive locations are restricted or generalised publicly.
5. **Four separate timestamps:** Keep `event_start_at`, `observed_at`, `submitted_at`, and authoritative server `received_at` distinct; never invent missing times or locations.
6. **Server-side enforcement:** Enforce permissions, validation, and separation of duties on the backend, never only in the UI.

---

## 7. Rule Change Log

| Date | Rule / Update | Source |
|---|---|---|
| 2026-11-17 | Initial compilation of owner rules: merged project scope, build from scratch, no `.zip` files in repo, work on `prime` branch (never push to `main`), maintain `docs/PROJECT_TRACKING.md`, `docs/REVIEW_SUMMARY.md`, and `docs/OWNER_RULES.md`, document every change, follow agent rules, dispatch work to subagents. | Owner conversation instructions |
| 2026-11-17 | Added 3-phase backend architecture documentation rule: structure backend into 3 phases in `docs/` with no code created yet, push docs only to `prime`, merge docs to `master` and `main` (via PR/branch rules), and never delete any branch. | Owner conversation instructions |
