# Remaining Work TODO

**Status:** Living document. Code is the source of truth; this list tracks gaps found by reading the
current `master` tree, not older planning documents.
**Branch:** `feat/remaining-gaps-and-report-ux`
**Last updated:** 2026-11-20

## How to use this file

- `[x]` done on this branch and verified.
- `[ ]` still open.
- Each item names the code it touches so a future session can resume without re-discovery.

## 1. Report submission UX (owner-reported bugs)

- [x] Copy control for the tracking code after a report is accepted (`CopyButton.tsx`, report receipt card).
- [x] Post-submission dialog that confirms receipt, shows the tracking code, and offers copy (`ReceiptDialog.tsx`).
- [x] Copy control on the tracking lookup page for the code the contributor entered (`TrackPage.tsx`).
- [x] Accessible dialog behaviour: labelled heading, Done button, Escape/backdrop close via native `<dialog>`, focus target, no colour-only state.
- [x] Frontend test coverage for the copy control and receipt dialog markup (`frontend_core.test.ts`).

## 2. Scientific authority (two-key gates)

- [x] Recovery verification requires an environmental specialist **and** an organisation authority,
      two distinct users, and neither may be the intervention owner (`verification/rules.py`).
- [x] Publication requires an environmental specialist **and** an organisation authority, two distinct
      users, and the acting caller must be one of them (`verification/rules.py`).
- [x] `system_admin` loses scientific write/approve/publication grants (`identity/permissions.py`).
- [x] Intervention approval requires `organisation_admin` and is refused for the proposer/lead (`interventions/service.py`).
- [x] Recovery transition on an intervention only accepts a final, two-key `recovery_verified`
      assessment from the same organisation (`interventions/service.py`).
- [x] Migration for the new approval columns (`0008_two_key_governance.py`).
- [x] Unit and integration tests for every deny path (`test_phase3Rules.py`, `test_two_key_and_admin.py`).

## 3. Administration lifecycle

- [x] `GET /api/v1/users` for `system_admin` (cursor-paginated, no password hashes).
- [x] `PATCH /api/v1/users/{userId}` to change display name, system role, or active state.
- [x] `PATCH /api/v1/organisations/{orgId}` to edit name/type or deactivate an organisation.
- [x] Self-deactivation guard and audit events for every change.
- [x] Admin UI: users table with activate/deactivate, organisation activate/deactivate.
- [x] Integration tests for list, update, deactivate, and self-deactivation refusal (`test_two_key_and_admin.py`).

## 4. Known gaps deliberately left for later

These are real gaps, but each is a larger design or infrastructure decision than this branch should
smuggle in. They stay open and are not claimed as done.

- [ ] `analysis.run` currently marks a queued job as running; no analytical execution engine exists.
- [ ] Evidence scanning is structural only (type/size/signature); no malware scanner integration.
- [ ] Embeddings are deterministic `hashed-words-v1`, not a trained semantic model (ADR-019 open).
- [ ] Audit events are append-only at the application layer only; no database trigger or WORM store.
- [ ] Controlled-vocabulary / configuration admin API and UI.
- [ ] Case `field_verified` two-key enforcement (recovery and publication are covered here).
- [ ] Token revocation table has no scheduled purge job; purge runs on logout only.
- [ ] Real-device offline/PWA validation and release-gate end-to-end testing.

## 5. Documentation to keep honest

- [x] `docs/20_Technical_Decision_Records.md`: ADR-041 (two-key enforcement) and ADR-042
      (admin lifecycle), plus the missing ADR-039/040 register rows.
- [x] `docs/PHASE3_PROGRESS_LOG.md`: branch state, verification commands, remaining items.
- [x] `docs/PROJECT_TRACKING.md`: change-log row and open-item corrections.
- [x] `docs/REVIEW_SUMMARY.md`: remove claims that are now implemented.
- [x] `README.md` / `frontend/README.md`: only where they contradict the current code.
