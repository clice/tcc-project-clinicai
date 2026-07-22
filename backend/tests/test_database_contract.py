"""Contrato estático de schema e migrations do CHK-03."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.database import Base
from app.modules import models  # noqa: F401 - registra todos os models
from app.modules.clinics.model import Clinic
from app.modules.role_permissions.model import RolePermission


BACKEND_ROOT = Path(__file__).parents[1]


def test_application_never_calls_create_all() -> None:
    """A criação do schema deve pertencer exclusivamente ao Alembic."""

    offenders = []
    for source_file in (BACKEND_ROOT / "app").rglob("*.py"):
        source = source_file.read_text(encoding="utf-8")
        if ".create_all(" in source:
            offenders.append(str(source_file.relative_to(BACKEND_ROOT)))

    assert offenders == []


def test_alembic_has_a_single_expected_head() -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["0003patientrequired"]


def test_fk_cascade_policy_is_explicit() -> None:
    """Somente a tabela associativa RBAC usa CASCADE no banco."""

    role_permission_fks = {
        fk.parent.name: fk.ondelete for fk in RolePermission.__table__.foreign_keys
    }
    assert role_permission_fks == {
        "role_id": "CASCADE",
        "permission_id": "CASCADE",
    }

    clinical_tables = {
        "clinics",
        "users",
        "patients",
        "exams",
        "ai_analyses",
        "audit_logs",
    }
    for table_name in clinical_tables:
        table = Base.metadata.tables[table_name]
        assert all(fk.ondelete is None for fk in table.foreign_keys)


def test_every_foreign_key_column_has_an_index() -> None:
    """Evita a FK de clínica sem índice que motivou a nova migration."""

    missing = []
    for table in Base.metadata.sorted_tables:
        indexed_columns = {
            column_name
            for index in table.indexes
            for column_name in index.columns.keys()
        }
        indexed_columns.update(column.name for column in table.columns if column.unique)
        for fk in table.foreign_keys:
            if fk.parent.name not in indexed_columns:
                missing.append(f"{table.name}.{fk.parent.name}")

    assert missing == []
    assert Clinic.__table__.c.status_id.index is True
