"""Targeted tests for the PostgreSQL-only append-only audit migration."""

import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "alembic" / "versions"


def _load_migration(filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        filename.removesuffix(".py"), MIGRATIONS_DIR / filename
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_revision_chain() -> None:
    purge = _load_migration("0010_token_revocation_purge.py")
    appendOnly = _load_migration("0011_audit_append_only.py")
    assert purge.revision == "0010_token_revocation_purge"
    assert purge.down_revision == "0009_case_two_key_governance"
    assert appendOnly.revision == "0011_audit_append_only"
    assert appendOnly.down_revision == "0010_token_revocation_purge"


@pytest.mark.parametrize("dialectName", ["postgresql", "sqlite"])
def test_append_only_ddl_is_postgresql_only(
    monkeypatch: pytest.MonkeyPatch, dialectName: str
) -> None:
    statements: list[str] = []
    module = _load_migration("0011_audit_append_only.py")
    monkeypatch.setattr(
        module,
        "op",
        SimpleNamespace(
            get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name=dialectName)),
            execute=statements.append,
        ),
    )

    module.upgrade()
    module.downgrade()

    joined = "\n".join(statements)
    if dialectName == "postgresql":
        assert "CREATE OR REPLACE FUNCTION audit_events_reject_mutation()" in joined
        assert "BEFORE UPDATE OR DELETE ON audit_events" in joined
        assert "CREATE TRIGGER audit_events_append_only" in joined
        assert "DROP TRIGGER IF EXISTS audit_events_append_only ON audit_events" in joined
        assert "DROP FUNCTION IF EXISTS audit_events_reject_mutation" in joined
    else:
        assert statements == []
