# EcoWatch

Environmental intelligence and response platform: a traceable chain from an observation, through review and investigation, to a justified intervention — and evidence about whether conditions actually improved.

**Status:** Phase 1 backend (core platform, intake, evidence provenance, jobs and case management), a Phase 2 evidence-correlation slice, and Phase 3 backend modules are present in [`backend/`](backend/README.md). [`frontend/`](frontend/README.md) is integrated with the backend for auth, health, observation intake and tracking, cases, correlation review, read-only Phase 3 workspaces, and system-admin organisation/user lifecycle with copyable tracking references and a post-submission receipt dialog. Scientific conclusions use two role-qualified human approvals (ADR-041); platform admins operate the system but are not scientific approvers. Nothing is validated, certified or live; correlation scores are ranking signals only. Everything in `docs/` remains the requirements/design baseline unless explicitly marked approved in [docs/20_Technical_Decision_Records.md](docs/20_Technical_Decision_Records.md).

## Documentation first

Read `docs/START_HERE.md`, then at minimum `docs/01`, `docs/06` (requirements), `docs/07` (architecture), `docs/08` (data model).

## Local development

Python 3.14 · PostgreSQL 16 + PostGIS 3.7 + pgvector · **podman** for containers (Docker in CI only)

The database image is built locally from the root `Dockerfile` (pgvector base + PostGIS). Both extensions are created by the migrations/CI check.

```bash
cp .env.example .env
make venv
.venv/bin/pip install -e "backend[dev]"
make up          # builds the DB image on first run, then starts it
make lint        # ruff check backend
make test        # pytest backend
make psql        # psql shell
make down        # stop, keep data
make reset       # stop, delete local data
```

No compose provider? `pipx install podman-compose`. Same `compose.yaml` works with `podman-compose`, `podman compose`, or `docker compose`.

### Run the whole system

Once the venv and frontend dependencies are installed (`.venv/bin/pip install -e "backend[dev]"` and `cd frontend && npm ci`):

```bash
make dev
```

This starts the database, applies Alembic migrations, then runs the API with its job worker enabled and the Vite frontend. The API serves on `127.0.0.1:8000` and the frontend on `127.0.0.1:5173`; a phone-check tunnel can keep pointing at 5173. Ctrl-C stops the API and frontend but leaves the database up (`make down`). The worker is enabled through `ECOWATCH_WORKER_ENABLED=true` in `.env` and exported by `scripts/dev.sh`; without it, jobs queue but never run. A separate worker process can be used instead by disabling it in `.env`.

## Branches

| Branch | Role |
|---|---|
| `master` | integration, default — PRs land here |
| `main` | release, protected, maintainer-only promotion from `master` |

Branch off `master`, one branch per change, PR into `master`. **Branches are never deleted after merging** unless the maintainer explicitly asks. `main` is sacred: no direct pushes, linear history, rules apply to admins.

## CI

`.github/workflows/ci.yml` — `infra` builds the compose DB image and proves both `postgis` and `vector` extensions load; `backend` runs `ruff check backend` and `pytest backend` against a live database built from the same image; `frontend` runs `npm ci`, `npm run lint` and `npm run build` from `frontend/` (a presence check still guards the job if `frontend/package.json` is absent).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Architectural decisions go in `docs/20_Technical_Decision_Records.md` as an ADR before the code.

## Licence

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
