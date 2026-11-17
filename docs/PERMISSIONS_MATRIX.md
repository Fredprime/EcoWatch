# Permission Matrix and Status Authority

**Status:** Proposed. Requires owner approval before `backend/` Phase 1 RBAC is written.
**Addresses:** `FR-053`, `FR-054`, `FR-055`, `NFR-005`, `docs/05` §2, `docs/16` §3, `AGENT_GUIDE` §19 (role permission matrix, listed as open).
**Decision record:** ADR-027.

## 1. Rules that hold everywhere

1. **Deny by default.** A role with no explicit grant has no access. No wildcard roles, no "staff can do everything".
2. **Enforced server-side** in a FastAPI dependency, never in the UI. The UI hides affordances; the server refuses them (`FR-053`).
3. **Organisation scoping.** Every aggregate row carries `organisation_id`. An `organisation_admin` sees only their own organisation unless a case is explicitly shared. A missing `organisation_id` is a defect, not a default of "everyone".
4. **Anonymous is not a role with data access.** `anonymous_contributor` is the unauthenticated intake boundary. It may submit and may read its own receipt via tracking code. It reads nothing else, ever.
5. **Identity is a separate grant.** Reading `observation_sources` (contributor identity/contact) is its own permission, not implied by reading observations (`FR-054`).
6. **No self-review.** A reviewer may never accept a relationship, verify a finding or approve an intervention they submitted or authored.
7. **Two-key conclusions.** `field_verified` and `recovery_verified` need a specialist plus an organisation authority, and neither may be the intervention owner (`FR-043`, `docs/14`).
8. **`system_admin` is not a scientist.** It may operate the platform; it may not set scientific or verification conclusions.
9. **Every consequential action writes an `audit_event`** in the same transaction (`FR-055`).

## 2. Roles

| Code | Role | Scope |
|---|---|---|
| `AC` | anonymous_contributor | unauthenticated, own submission only |
| `RC` | registered_contributor | own submissions |
| `RV` | reviewer | triage, correlation review, quality flags |
| `IV` | investigator | assigned cases, evidence, findings |
| `ES` | environmental_specialist | methods, analysis, scientific conclusions |
| `IM` | intervention_manager | interventions, milestones, outcome evidence |
| `OA` | organisation_admin | own organisation's users, approvals, publications |
| `SA` | system_admin | platform configuration, audit, no scientific authority |

A person may hold several roles. Grants are additive except where §3 forbids it.

## 3. Resource permissions

Legend: **C** create, **R** read, **U** update, **D** delete/redact, **X** export.

### 3.1 Observations

| Action | Allowed |
|---|---|
| Create via public intake (anonymous or registered) | `AC`, `RC`, and all staff |
| Read own submission + receipt | `AC` (tracking code only), `RC` (own) |
| Read public-safe fields (redacted) | `RV`, `IV`, `ES`, `IM`, `OA`, `SA` |
| Read restricted fields (identity, exact sensitive location, original media) | `IV`, `ES`, `OA` (own org), `SA` |
| Send clarification request to contributor | `RV`, `IV`, `OA`, `SA` |
| Correct → creates `observation_versions` row | `RC` (own, before review), `RV`, `IV`, `SA` |
| Set quality flag | `RV`, `ES`, `SA` |
| Hide from view (never delete evidence) | `SA` |
| Export | `OA` (own org), `SA` |

### 3.2 Contributor identity (`observation_sources`)

| Action | Allowed |
|---|---|
| Read identity/contact | `OA` (own org), `SA` |
| Contact a contributor through the platform | `RV`, `IV`, `OA`, `SA` — sends a message; does not disclose identity |
| Delete/anonymise identity record | `SA`, via the approved policy workflow only |

### 3.3 Evidence assets

| Action | Allowed |
|---|---|
| Upload | `AC`, `RC`, all staff |
| Read preview/derivative | `RV`, `IV`, `ES`, `IM`, `OA` (own org), `SA` |
| Read original file | `IV` (case-linked), `ES` (case-linked), `OA` (own org), `SA` |
| Read scan/quarantine status | `RV`, `SA` |
| Delete or redact | `SA` — policy workflow, audit event, never a silent delete |
| Export | `OA` (own org), `SA` |

### 3.4 Cases

| Action | Allowed |
|---|---|
| Create a case | `RV`, `IV`, `OA`, `SA` — never automated (`docs/12` §2) |
| Read | `RV`, `IV`, `ES`, `IM`, `OA` (own org), `SA` |
| Update summary, findings, hypotheses, evidence gaps | `IV` (assigned), `RV`, `ES` (technical note only) |
| Assign investigator | `OA` (own org), `SA` |
| Link/unlink observation | `RV`, `IV`, `SA` |
| Merge / split cases | `IV`, `OA`, `SA` — audit event, history preserved |
| Refer to an authority (external reference record) | `IV`, `OA` |
| Change status | §4 |
| Close | §4 |

### 3.5 Evidence relationships (ECII)

| Action | Allowed |
|---|---|
| View suggestions, component scores, reasons | `RV`, `IV`, `ES`, `OA`, `SA` |
| Accept / reject / mark ambiguous | `RV`, `IV` — not on own submission |
| Promote provisional cluster to case | `IV`, `OA`, `SA` |
| Merge / split clusters | `IV`, `OA`, `SA` |
| Change weights, bands, model version | `SA`, with `ES` approval recorded — configuration change is audited |

### 3.6 Prioritisation

| Action | Allowed |
|---|---|
| View factor view and missing inputs | all staff |
| Record factor values | `ES`, `IV` |
| Set human priority + rationale | `IV`, `IM`, `OA` |

### 3.7 Interventions

| Action | Allowed |
|---|---|
| Propose intervention | `IM`, `IV` |
| Approve intervention | `OA` — never the proposer |
| Record milestones and supporting evidence | `IM`, `IV` |
| Record activity completed / output delivered | `IM` |
| Cancel | `IM`, `OA` |

### 3.8 Verification

| Action | Allowed |
|---|---|
| Define indicators and baseline | `ES` |
| Record measurements | `ES`, `IM` |
| Assess outcome (`improvement`, `no_improvement`, `deterioration`, `inconclusive`) | `ES` |
| Set `recovery_verified` | `ES` **and** `OA` — two-key, neither the intervention owner |

### 3.9 Datasets and analysis

| Action | Allowed |
|---|---|
| Register dataset / import with provenance | `ES`, `OA`, `SA` |
| Approve licence and permitted use | `OA`, `SA` |
| Run analysis | `ES` |
| Read analysis runs and outputs | `RV`, `IV`, `ES`, `IM`, `OA`, `SA` |
| Add interpretation note (a separate reviewed record) | `ES` |

### 3.10 Governance

| Action | Allowed |
|---|---|
| Read audit events | `OA` (own org), `SA` (all) |
| Write audit event | system only; append-only, no human role |
| Invite/manage users in own organisation | `OA` |
| Assign `system_admin` | `SA` only — cannot be self-granted |
| Read/change configuration (vocabularies, thresholds) | read: all staff; change: `SA` with audit |
| Draft public summary | `IV`, `ES` |
| Approve and publish public summary | `OA` **and** `ES` — publication is a governance decision (`docs/05` §9) |
| Unpublish / retract | `OA`, `SA` |

## 4. Case and intervention status authority

Statuses exist (`docs/12` §6, `docs/14` §6) but no transition rules did. Proposed authority:

| Status | Who may set it | Requires |
|---|---|---|
| New / unreviewed, Initial review | `RV`, `IV`, `OA`, `SA` | — |
| Evidence gathering | `IV`, `OA`, `SA` | rationale |
| Corroborated evidence available | `IV`, `OA`, `SA` | rationale + at least one reviewed relationship |
| Field verification required | `IV`, `OA`, `SA` | rationale |
| Field verified | `ES` + `OA` | field record reference; never AI, never `SA` alone |
| Referred to responsible authority | `IV`, `OA` | external reference record |
| Under intervention | `IM`, `OA` | linked approved intervention |
| Monitoring outcomes | `IM`, `ES`, `OA` | baseline defined |
| Recovery verified | `ES` + `OA` | approved criteria + comparable follow-up measurements |
| Not substantiated | `IV`, `OA` | rationale; alternative explanations recorded |
| Closed | `IV`, `OA`, `SA` | rationale |
| Merged into another case | `IV`, `OA`, `SA` | target case + audit; source case is retained, never erased |

Intervention statuses follow the same pattern: `IM` drives delivery states, `OA` approves, `ES` comments, `SA` corrects errors only, with audit.

## 5. Consequences for the data model

This matrix cannot be implemented against the current 26-table model. Four additions are required in Phase 1:

1. `organisation_id` on `observations`, `cases`, `evidence_assets`, `evidence_relationships`, `interventions`, `prioritisation_assessments`, `verification_assessments`. Without it, §1.3 is unimplementable.
2. A permission/role assignment model (`memberships` exists but carries no explicit grant set) — either roles-as-enum plus a code-level policy table, or a `role_grants` table. The enum version is smaller and enough for Phase 1.
3. `clarification_requests` — `docs/05` Workflow B promises clarification requests and no entity exists. `AC`/`RC` have no inbox, so a request must have an addressable record plus a delivery channel.
4. `publications` — an approval record for public summaries with approver, approvers' roles, timestamp, and the exact published text (see §3.10).

Also required and still missing from the plan: `methods`/`protocols` (referenced as `method_id` in `docs/08` §4) and a controlled-vocabulary table.

## 6. What is deliberately not decided here

- Authentication mechanism (session vs JWT vs OIDC) — provider choices remain open (`docs/18`).
- Whether grants are per-organisation or per-case teams. Start per-organisation; add case teams only when a real partner requires it.
- Retention and deletion schedules — still Open, and they constrain §3.2's anonymisation rule.

Owner approval of this matrix, or corrections to it, unblocks Phase 1 RBAC. Until then, `FR-053` cannot be implemented and the backend plan's "server-side RBAC dependencies" has no rule set behind it.
