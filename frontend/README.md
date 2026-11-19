# EcoWatch Frontend

Prototype frontend aligned to the EcoWatch documentation baseline in `../docs/`. It is integrated with the local backend for core read and intake flows only. **No production claims: nothing here is validated, certified or live, and there is no seeded, sample or demo data in product source.**

## What this includes

- React + TypeScript + Vite app shell (`src/App.tsx`, router-based workspace navigation).
- Hand-written typed DTOs (`src/api/types.ts`) and a single `fetch` wrapper (`src/api/client.ts`) — no React Query, Axios or Zod. The Vite dev server proxies `/api` and `/health` to `127.0.0.1:8000` (`vite.config.ts`); no backend CORS middleware was added.
- **Auth:** sign-in against `login` and `auth/me`. The bearer token is held in memory only, so a page reload requires signing in again; a 401 clears auth locally. Logout and 401 clearing are client-only: the stateless HMAC token is not server-side revocable and stays valid until expiry (default 12h), although deactivated users are rejected on every request. Immediate server-side revocation is deferred, not implemented.
- **Overview / Report:** health and observation list reads, and observation intake with real server receipts. Submission states are draft / submitting / received / error only; nothing is shown as "queued locally" or as received before a server receipt.
- **Cases / Evidence intelligence:** case list, detail and timeline reads, plus correlation suggestion listing and human accept/reject/ambiguous decisions. A suggestion is ranked decision support with a stated method and reasons, never a source, causation, illegality or harm finding.
- **Shells:** Analysis, Monitoring, Prioritisation, Interventions, Verification and Administration remain honest staff shells with no API integration. Offline-first PWA collection is not implemented.
- **Public site vs staff workspace:** `PublicLayout` + `public.css` render the no-login pages with no staff sidebar or record-management actions. Anonymous visitors are **not** offered a staff sign-in link or told where `/login` is; only an already-authenticated user sees a "Staff workspace" link. Everything else sits behind `RequireAuth` in `StaffLayout` (staff overview moved from `/` to `/workspace`). UI gating is convenience only — the backend enforces permissions.
- **Public endpoints:** anonymous intake (`POST /observations`), throttled `POST /observations/receipt-lookup` (returns only a PII-free server receipt), and approved redacted `GET /public/cases` list/detail. The report form keeps all existing fields; only wrapper, copy and spacing changed.
- **Optional photos:** the report form has a native multi-file picker (`image/jpeg`, `image/png`, `image/webp`, 15 MB each) with local previews that are never uploaded themselves. Photos upload only after intake succeeds, through `uploadEvidence` (`POST /observations/{id}/evidence`) using the returned tracking code as `X-Tracking-Code` and `accessClass=restricted`. Uploads are sequential; each photo shows ready / uploading / uploaded / failed, with a retry for failures. "Uploaded" is shown only when the server returns an `EvidenceAssetResponse`; scan status is never presented as a finding. `client.ts` sets the JSON content type only for string bodies so multipart boundaries survive.
- **Full-width public layout:** the public shell and page wrappers have no hard max-width; narrow-content pages use `.public-split` (intro beside form) and the report form uses `.public-report-form` (fields beside the photo panel), collapsing to one column under 1000px. Cards and text keep their own readable widths.
- **Public FAQ and safe 404:** the home page's "How the process works" section and the output disclaimer moved to `/faq`, reachable from a fixed question-mark button at the bottom right (hidden on the FAQ page itself so it cannot self-link). The footer keeps only the faded "Share only what is safe to share" line. An unmatched route renders a generic 404 with no paths, errors, request IDs or diagnostics — those belong in administrator logs. The header tabs are centred on desktop and wrap to a centred row on smaller screens; the brand subtitle is reduced in size.
- **Sign-in layout:** `/login` stacks its intro and form in a centred column (max 460 px) instead of the two-column split used by other narrow public pages.
- Baseline tokens and styles in `src/index.css` and `src/App.css`, with the lighter public theme in `src/public.css` (see `../design-system/ecowatch/MASTER.md`).

## Route map

| Route | Shell | Access | Data shown |
|---|---|---|---|
| `/` | public | no login | what you can do here |
| `/faq` | public | no login | process steps, correlation score caveats and output caveats |
| `/report` | public | no login | anonymous observation intake, with optional photos |
| `/track` | public | no login | tracking-code receipt lookup |
| `/updates`, `/updates/:caseId` | public | no login | approved redacted case summaries |
| `/login` | public | no login | staff sign-in (kept off public navigation; reached from a saved link or the workspace guard) |
| `/workspace`, `/cases`, `/evidence`, `/monitoring`, `/analysis`, `/prioritisation`, `/interventions`, `/verification`, `/admin` | staff | sign-in required | records within the permitted scope |

Public pages never show contributor identity, exact locations or automated findings. A receipt confirms durable storage only; a published status is a human-reviewed record, not an automated finding.

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
