# Contributing to EcoWatch

Hackathon project, real review rules. Three things are non-negotiable:

1. **Every change goes through a pull request.** Nobody pushes to `master` or `main` directly.
2. **Every change gets its own branch.** One branch = one piece of work.
3. **Merged branches are kept.** Do not delete a branch after merging. Branches are removed only when the maintainer explicitly asks for it.

---

## 1. Branch model (blue–green)

| Branch | Role | Who writes to it |
|---|---|---|
| `master` | Integration. Default branch. Everything lands here first. | PRs only, 1 approval + green CI |
| `main` | Release / live ("sacred"). Always deployable. | Maintainer only, promoted from `master` |

```
feat/your-thing ──PR──> master ──release PR──> main
```

- `master` takes the churn. Break it briefly if you must; fix it fast.
- `main` is sacred: no experiments, no "just a small hotfix", no direct commits. It only receives reviewed, passing code from `master`.
- Branch protection on both: no force-push, no direct push, review + CI required. `main` additionally enforces linear history and applies the rules to admins too.

## 2. Start work

```bash
git switch master
git pull --ff-only
git switch -c feat/short-slug        # or fix/…, docs/…, chore/…
```

Branch naming:

| Prefix | Use |
|---|---|
| `feat/` | new capability |
| `fix/` | bug fix |
| `docs/` | documentation only |
| `chore/` | tooling, deps, CI |
| `exp/` | spike you may throw away (never merge into `main`) |

Keep the slug short and specific: `feat/observation-intake`, not `feat/work`.

Your working branch stays **local**. Do not push personal, scratch or integration branches to `origin` — it goes to `origin` only when you open a PR from it.

## 3. Commit messages

`type(scope): summary` — imperative, ≤ 72 chars.

```
feat(api): accept anonymous observations with idempotency key
fix(db): stop duplicate rows on client retry
docs(adr): record postgis decision
```

## 4. Open the pull request

- Base branch is **`master`**. Never open a PR into `main`.
- Fill in the PR template: what changed, why, how you checked it, what you did not do.
- Keep PRs small. A PR nobody can review in ten minutes is a PR nobody reviews.
- CI must be green: `infra` is required, `backend`/`frontend` run once those folders exist.
- One approval from the maintainer. Resolve all conversations before merging.
- Squash-merge. The PR title becomes the commit message, so make it a good one.

### After merge

**Leave the branch alone.** Do not delete it, locally or on GitHub. The repo is configured with "delete branch on merge" **off**, and that setting stays off unless the maintainer says otherwise. If you want a branch removed, ask — do not do it yourself.

## 5. Local development

Python 3.14, PostgreSQL 16 + PostGIS 3.7 + pgvector, **podman** for containers (Docker is used only in CI). The DB image is built locally from the root `Dockerfile` (pgvector base + PostGIS) on first `make up`.

```bash
cp .env.example .env          # never commit .env
make venv                     # creates .venv
.venv/bin/pip install -e "backend[dev]"   # once backend/ exists
make up                       # build (first run) and start PostgreSQL + PostGIS + pgvector
make psql                     # psql shell
make down                     # stop, keep data
make reset                    # stop and delete local data
```

`scripts/compose.sh` picks whatever compose provider you have (`podman-compose`, `podman compose`, or `docker compose`), so the same `compose.yaml` works everywhere.

Podman notes:

- The database uses a **named volume**, not a bind mount — rootless podman maps bind-mount ownership badly and Postgres will refuse to start.
- If you have no compose provider: `pipx install podman-compose`.
- Never commit `.env`, `data/`, or uploaded files.

## 6. Project layout

```
backend/    FastAPI app            (not created yet)
frontend/   React + TypeScript     (not created yet)
docs/       design + requirements baseline — read before building
scripts/    local tooling
```

## 7. House rules from the documentation

These come from `docs/`, and code that ignores them will be sent back:

- Observations, evidence and cases are separate records. A correlation score is never a severity or truth score.
- Event, observed, submitted and received times stay separate.
- AI output is a suggestion with a stated method and reason, never a finding. Consequential decisions need a human.
- Originals are preserved; derivatives are new files.
- Permissions are enforced server-side, not hidden in the UI.
- Activity completed ≠ environmental outcome ≠ verified recovery.

Architectural choices get an ADR in `docs/20_Technical_Decision_Records.md` before the code lands, not after.

## 8. Reporting problems

Use GitHub Issues. Include what you expected, what happened, and how to reproduce it. Security or privacy problems: report privately to the maintainer, not in a public issue.
