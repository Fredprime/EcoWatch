#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <backup_file.dump>" >&2
    exit 1
fi

DUMP_FILE="$1"
if [[ ! -f "${DUMP_FILE}" ]]; then
    echo "Backup file not found: ${DUMP_FILE}" >&2
    exit 1
fi

if [[ -n "${DATABASE_URL:-}" ]]; then
    pg_restore --clean --if-exists --no-owner --no-acl --dbname="${DATABASE_URL}" "${DUMP_FILE}"
else
    CONTAINER="${ECOWATCH_DB_CONTAINER:-ecowatch-db}"
    DB_USER="${POSTGRES_USER:-ecowatch}"
    DB_NAME="${POSTGRES_DB:-ecowatch}"
    docker exec -i "${CONTAINER}" pg_restore -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists --no-owner --no-acl < "${DUMP_FILE}"
fi

echo "Restore completed from ${DUMP_FILE}"
