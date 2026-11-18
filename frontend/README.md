# EcoWatch Frontend (Scaffold)

Prototype frontend scaffold aligned to the EcoWatch documentation baseline in `../docs/`. **No backend integration, no live data, and no production claims.**

## What this includes

- React + TypeScript + Vite app shell (`src/App.tsx`, router-based workspace navigation).
- Workspace placeholders reflecting `docs/15_User_Interface_and_Experience.md`: Overview, Report/Collect, Evidence Intelligence, Monitoring, Cases, Analysis, Prioritisation, Interventions, Verification, Administration.
- **Report/Collect** demo form with accessibility basics (labels, hints, keyboard focus) and explicit submission states: local draft / queued locally / submitted / received by server (demo only; queued is never shown as received).
- **Cases** demo timeline distinguishing event/observed/submitted/received/acquisition/processing/intervention dates, plus map/list/evidence placeholders.
- Baseline tokens and styles in `src/index.css` and `src/App.css` (see `../design-system/ecowatch/MASTER.md`).

## Proposed stack (not yet approved)

Consistent with ADR candidates in `docs/20_Technical_Decision_Records.md`: React + TypeScript (ADR-014), MapLibre later (ADR-017), IndexedDB offline queue later (ADR-018). Confirm/record decisions via ADR before treating as final.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Build/typecheck:

```bash
npm run build
```

## Notes

- Permissions must be enforced by the backend; UI role-scoping shown here is illustrative only.
- Maps must have non-map alternatives; sensitive locations may be restricted/generalised.
- Keep observations/evidence distinct from interpretations and model outputs; label machine-generated content.
- Do not claim implementation, data acquisition, model validation, or recovery outcomes from this scaffold.
