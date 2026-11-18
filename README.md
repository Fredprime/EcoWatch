# EcoWatch

Environmental intelligence and response platform: a traceable chain from an observation, through review and investigation, to a justified intervention — and evidence about whether conditions actually improved.

**Status:** Phase 1 backend implemented inside [`backend/`](backend/README.md) (core platform, intake, evidence provenance, jobs, and case management); `frontend/` and backend Phases 2–3 are not started yet. Everything in `docs/` remains the requirements/design baseline unless explicitly marked approved in [docs/20_Technical_Decision_Records.md](docs/20_Technical_Decision_Records.md).

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

## Branches

| Branch | Role |
|---|---|
| `master` | integration, default — PRs land here |
| `main` | release, protected, maintainer-only promotion from `master` |

Branch off `master`, one branch per change, PR into `master`. **Branches are never deleted after merging** unless the maintainer explicitly asks. `main` is sacred: no direct pushes, linear history, rules apply to admins.

## CI

`.github/workflows/ci.yml` — `infra` builds the compose DB image and proves both `postgis` and `vector` extensions load; `backend` runs `ruff check backend` and `pytest backend` against a live database built from the same image; `frontend` activates once `frontend/package.json` exists.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Architectural decisions go in `docs/20_Technical_Decision_Records.md` as an ADR before the code.

## Licence

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
