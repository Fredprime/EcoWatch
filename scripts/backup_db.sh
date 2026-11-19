#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${1:-./data/backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${BACKUP_DIR}"
OUT_FILE="${BACKUP_DIR}/ecowatch_${TIMESTAMP}.dump"

if [[ -n "${DATABASE_URL:-}" ]]; then
    pg_dump --format=custom --no-owner --no-acl --file="${OUT_FILE}" "${DATABASE_URL}"
else
    CONTAINER="${ECOWATCH_DB_CONTAINER:-ecowatch-db}"
    DB_USER="${POSTGRES_USER:-ecowatch}"
    DB_NAME="${POSTGRES_DB:-ecowatch}"
    docker exec "${CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --format=custom --no-owner --no-acl > "${OUT_FILE}"
fi

echo "Backup written to ${OUT_FILE}"
