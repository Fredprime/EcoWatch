# EcoWatch UI & Frontend Bookmarks

**Standard:** `GLOBAL_AGENT_RULES_MERGED.md` §17.1  
**Last Updated:** 2026-11-19

- **React 19 Documentation** — https://react.dev/ (checked 2026-11-19): Component, hooks, `Suspense`/`lazy`, and strict effect rules enforced by `oxlint`.
- **React Router v7** — https://reactrouter.com/ (checked 2026-11-19): Client routing (`PublicLayout`, `StaffLayout`, `RequireAuth`).
- **Vite 6** — https://vite.dev/ (checked 2026-11-19): Dev server same-origin `/api` + `/health` proxy (`frontend/vite.config.ts`) and production Rollup chunking.
- **MapLibre GL JS** — https://maplibre.org/maplibre-gl-js/docs/ (checked 2026-11-19): Offline-safe local blank style GeoJSON rendering for `WktMap.tsx` (`ADR-038`).
- **MDN Service Worker API & Web App Manifest** — https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API (checked 2026-11-19): Static app-shell caching (`frontend/public/sw.js`, `manifest.webmanifest`) paired with native IndexedDB (`frontend/src/api/offlineQueue.ts`).
- **W3C WCAG 2.2 AA** — https://www.w3.org/TR/WCAG22/ (checked 2026-11-19): Contrast, keyboard focus, form labels, and non-colour status indicators.
