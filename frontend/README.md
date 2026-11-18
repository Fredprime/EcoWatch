# EcoWatch Frontend

Prototype frontend aligned to the EcoWatch documentation baseline in `../docs/`. It is integrated with the local backend for core read and intake flows only. **No production claims: nothing here is validated, certified or live, and there is no seeded, sample or demo data in product source.**

## What this includes

- React + TypeScript + Vite app shell (`src/App.tsx`, router-based workspace navigation).
- Hand-written typed DTOs (`src/api/types.ts`) and a single `fetch` wrapper (`src/api/client.ts`) — no React Query, Axios or Zod. The Vite dev server proxies `/api` and `/health` to `127.0.0.1:8000` (`vite.config.ts`); no backend CORS middleware was added.
- **Auth:** sign-in against `login` and `auth/me`. The bearer token is held in memory only, so a page reload requires signing in again; a 401 clears auth locally. Logout and 401 clearing are client-only: the stateless HMAC token is not server-side revocable and stays valid until expiry (default 12h), although deactivated users are rejected on every request. Immediate server-side revocation is deferred, not implemented.
- **Overview / Report:** health and observation list reads, and observation intake with real server receipts. Submission states are draft / submitting / received / error only; nothing is shown as "queued locally" or as received before a server receipt.
- **Cases / Evidence intelligence:** case list, detail and timeline reads, plus correlation suggestion listing and human accept/reject/ambiguous decisions. A suggestion is ranked decision support with a stated method and reasons, never a source, causation, illegality or harm finding.
- **Shells:** Analysis, Monitoring, Prioritisation, Interventions, Verification and Administration remain honest shells with no API integration. Offline-first PWA collection is not implemented.
- Baseline tokens and styles in `src/index.css` and `src/App.css` (see `../design-system/ecowatch/MASTER.md`).

## Proposed stack (not yet approved)

Consistent with ADR candidates in `docs/20_Technical_Decision_Records.md`: React + TypeScript (ADR-014), MapLibre later (ADR-017), IndexedDB offline queue later (ADR-018). React + TypeScript + Vite are in use for the built slice; MapLibre and the IndexedDB offline queue remain future work. Confirm/record decisions via ADR before treating as final.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Lint, build/typecheck:

```bash
npm run lint
npm run build
```

Vite was upgraded from 6.2.7 to 6.4.6 in the lockfile only to clear a high-severity dev-server advisory; `npm audit` reports 0 vulnerabilities. No new runtime dependencies were added.

## Notes

- Permissions must be enforced by the backend; UI role-scoping shown here is illustrative only.
- Maps must have non-map alternatives; sensitive locations may be restricted/generalised.
- Keep observations/evidence distinct from interpretations and model outputs; label machine-generated content.
- Do not claim data acquisition, model validation, legal compliance, or recovery outcomes from this frontend. A correlation score is a ranking signal, not a probability or severity.
