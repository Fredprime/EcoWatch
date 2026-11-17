# EcoWatch

Environmental intelligence and response platform: a traceable chain from an observation, through review and investigation, to a justified intervention — and evidence about whether conditions actually improved.

**Status:** design baseline, no application code yet. Everything in `docs/` is a requirements/design baseline, not evidence of implementation.

## Documentation first

Read `docs/START_HERE.md`, then at minimum `docs/01`, `docs/06` (requirements), `docs/07` (architecture), `docs/08` (data model).

## Local development

Python 3.14 · Postgres 16 + PostGIS 3.4 · **podman** for containers (Docker in CI only)

```bash
cp .env.example .env
make venv
make up          # Postgres/PostGIS
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

`.github/workflows/ci.yml` — `infra` validates the compose file and proves PostGIS responds; `backend` and `frontend` activate automatically when those folders appear.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Architectural decisions go in `docs/20_Technical_Decision_Records.md` as an ADR before the code.

## Licence

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
