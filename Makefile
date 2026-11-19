.PHONY: help dev up down reset psql logs venv lint test

help:
	@echo "dev     one command: DB + migrations + API/worker + frontend"
	@echo "up      build and start local PostgreSQL + PostGIS + pgvector (podman)"
	@echo "down    stop it (keeps data)"
	@echo "reset   stop and DELETE local data"
	@echo "psql    open a psql shell"
	@echo "logs    follow db logs"
	@echo "venv    create .venv (python3.14)"
	@echo "lint    ruff (needs backend/)"
	@echo "test    pytest (needs backend/)"

dev:
	scripts/dev.sh

up:
	scripts/compose.sh up -d --wait --build

down:
	scripts/compose.sh down

reset:
	scripts/compose.sh down -v

psql:
	scripts/compose.sh exec db psql -U $${POSTGRES_USER:-ecowatch} -d $${POSTGRES_DB:-ecowatch}

logs:
	scripts/compose.sh logs -f db

venv:
	/usr/bin/python3 -m venv .venv
	.venv/bin/pip install -q --upgrade pip

lint:
	.venv/bin/ruff check backend

test:
	.venv/bin/pytest backend
