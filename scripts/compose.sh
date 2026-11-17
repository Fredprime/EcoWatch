#!/usr/bin/env sh
# One compose file, any engine: podman-compose, "podman compose", or docker compose.
set -e
if command -v podman-compose >/dev/null 2>&1; then exec podman-compose "$@"; fi
if podman compose version >/dev/null 2>&1; then exec podman compose "$@"; fi
if docker compose version >/dev/null 2>&1; then exec docker compose "$@"; fi
echo "No compose provider found. Install one: pipx install podman-compose  (or use docker compose)." >&2
exit 1
