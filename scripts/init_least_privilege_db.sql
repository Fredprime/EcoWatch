-- Least-privilege runtime database role for EcoWatch API/worker processes.
-- Run as the database owner/superuser after Alembic migrations are applied.
-- Replace 'CHANGE_ME_APP_PASSWORD' before executing in production.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ecowatch_app') THEN
        CREATE ROLE ecowatch_app WITH LOGIN PASSWORD 'CHANGE_ME_APP_PASSWORD'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE ecowatch TO ecowatch_app;
GRANT USAGE ON SCHEMA public TO ecowatch_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ecowatch_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ecowatch_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ecowatch_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO ecowatch_app;
