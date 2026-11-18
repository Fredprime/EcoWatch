# EcoWatch Design System (Frontend Scaffold Baseline)

> Derived from `docs/15_User_Interface_and_Experience.md`, product vision, and current scaffold implementation. This is a working baseline for implementation, not a final approved visual identity.

## Product fit

- **Domain:** Environmental intelligence and response (Collect → Analyse → Prioritise → Intervene → Verify).
- **Users:** Community reporters, field contributors, reviewers, investigators, environmental specialists, intervention managers, administrators (role-scoped).
- **Core UX needs:** Trustworthy evidence handling, provenance/uncertainty clarity, plain-language reporting, mobile-first and low-connectivity tolerance, accessible data-dense review workspaces, non-map alternatives to maps.

## Direction

- **Tone:** Clear, grounded, institutional-but-approachable. Prioritise legibility and evidence clarity over decoration.
- **Layout:** Responsive workspace shell (sidebar navigation on wide screens, stacked on small screens), content-first cards/tables/timelines/forms. Avoid marketing-landing patterns for product surfaces.
- **Accessibility:** WCAG-minded baseline — visible focus, 4.5:1 text contrast targets, semantic labels/structure, keyboard support, 44px touch targets, `prefers-reduced-motion` respected, no emoji icons.

## Tokens (current scaffold)

| Token | Value | Use |
|---|---|---|
| `--color-bg` | `#f4f6f3` | App background |
| `--color-surface` | `#ffffff` | Cards/panels |
| `--color-surface-alt` | `#e9eee8` | Muted surfaces/notices |
| `--color-text` | `#18211d` | Primary text |
| `--color-text-muted` | `#4b5b54` | Secondary/supporting text |
| `--color-border` | `#c9d3cc` | Dividers/borders |
| `--color-primary` | `#0f5c4d` | Primary actions/brand emphasis (deep teal) |
| `--color-accent` | `#1f6f8b` | Links/informational accent |
| `--color-focus` | `#0b6aa8` | Focus ring |
| `--color-warning(-bg)` | `#8a5a00` / `#fff4db` | Caution, queued/pending states |
| `--color-success(-bg)` | `#1f6b3a` / `#e3f3e8` | Received/positive states |
| `--color-danger(-bg)` | `#a1260d` / `#fde8e2` | Errors/destructive/risk |
| `--radius-sm/md` | `6px` / `10px` | Controls, cards |
| `--font-sans` | IBM Plex Sans (+ system fallbacks) | UI, body, forms, data |
| `--font-serif` | IBM Plex Serif (+ Georgia fallback) | Page/section headings |

Defined in `frontend/src/index.css`; component/layout styles in `frontend/src/App.css`.

## UI principles (must follow)

- **State honesty:** Distinguish local draft / queued locally / submitted / received by server. Never present a queued local item as received; show server reference only after durable receipt.
- **Provenance & uncertainty:** Represent time/location precision and unknowns; distinguish event-start, observed, submitted, received, acquisition, sampling, processing, intervention dates on timelines.
- **Evidence distinctions:** Keep claims, measurements, interpretations, and model outputs distinct; label machine-generated content.
- **Not-only-map:** Every map-centric view needs list/detail alternatives; allow restricted/generalised sensitive locations.
- **Plain language & safety:** Short explanations, no specialist knowledge required to report, clear privacy/safety notices, avoid unnecessary sensitive disclosure.
- **Role-scoped UI:** Expose workspaces/actions by role in production; backend enforces permissions (UI hiding is insufficient).
- **Forms:** Visible labels, helper text, appropriate input modes, near-field validation/errors (to implement), loading/success/error feedback on submit.

## Implemented scaffold surfaces

- App shell + workspace navigation (`frontend/src/App.tsx`)
- Overview, Report/Collect (state demo + accessible form), Monitoring (map/list placeholder), Cases (summary/map/timeline/evidence placeholders), and workspace stubs for Evidence Intelligence, Analysis, Prioritisation, Interventions, Verification, Administration.

## Next design/implementation steps

1. Confirm approved visual identity/stack decisions via ADRs (current stack choices are proposed unless stated otherwise).
2. Add real routing guards/role-based navigation once auth/permissions model is implemented.
3. Integrate MapLibre for map workspaces with uncertainty/quality affordances and accessible alternatives.
4. Implement offline queue persistence (IndexedDB, proposed) with explicit sync states and idempotent retries.
5. Expand component library (status badges, data tables, timeline, evidence cards, notices) with tests and accessibility checks.
