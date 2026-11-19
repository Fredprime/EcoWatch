# syntax=docker/dockerfile:1
FROM docker.io/pgvector/pgvector:pg16

# The base image already provides pgvector. Add PostGIS from the same PGDG
# repository; extensions are created per database by migrations/CI, not here.
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get \
      -o Acquire::Retries=5 -o Acquire::http::Timeout=60 \
      install -y --no-install-recommends postgresql-16-postgis-3 \
 && rm -rf /var/lib/apt/lists/*
