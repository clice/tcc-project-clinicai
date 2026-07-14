"""Verificador executável do CHK-03 para PostgreSQL.

Este módulo não altera o schema. Ele inspeciona a revisão Alembic ativa,
restrições, FKs, ações referenciais, índices e dados semânticos. Também produz
snapshots estáveis que ignoram IDs, timestamps e hashes salteados.
"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
from typing import Any, Iterable

import sqlalchemy as sa
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.modules import models  # noqa: F401 - registra toda a metadata
from app.modules.permissions.catalog import OFFICIAL_PERMISSION_NAMES
from app.modules.role_permissions.seed import (
    CLINIC_STAFF_PERMISSIONS,
    DOCTOR_PERMISSIONS,
)

APP_TABLES = tuple(sorted(Base.metadata.tables))
DEMO_TABLES = ("clinics", "users", "patients", "exams", "ai_analysis")

EXPECTED_UNIQUES: dict[str, set[tuple[str, ...]]] = {
    "statuses": {("name", "applies_to")},
    "roles": {("name",)},
    "permissions": {("name",)},
    "role_permissions": {("role_id", "permission_id")},
    "clinics": {("cnpj",), ("email",)},
    "users": {("email",), ("cpf",)},
    "patients": {("clinic_id", "cpf")},
    "ai_analysis": {("exam_id",)},
}

EXPECTED_FOREIGN_KEYS: dict[
    str,
    set[tuple[tuple[str, ...], str, tuple[str, ...], str | None]],
] = {
    "role_permissions": {
        (("role_id",), "roles", ("id",), "CASCADE"),
        (("permission_id",), "permissions", ("id",), "CASCADE"),
    },
    "clinics": {
        (("status_id",), "statuses", ("id",), None),
    },
    "users": {
        (("role_id",), "roles", ("id",), None),
        (("status_id",), "statuses", ("id",), None),
        (("clinic_id",), "clinics", ("id",), None),
    },
    "patients": {
        (("clinic_id",), "clinics", ("id",), None),
        (("doctor_id",), "users", ("id",), None),
        (("status_id",), "statuses", ("id",), None),
    },
    "exams": {
        (("clinic_id",), "clinics", ("id",), None),
        (("patient_id",), "patients", ("id",), None),
        (("doctor_id",), "users", ("id",), None),
        (("status_id",), "statuses", ("id",), None),
        (("reviewed_by_id",), "users", ("id",), None),
    },
    "ai_analysis": {
        (("exam_id",), "exams", ("id",), None),
        (("status_id",), "statuses", ("id",), None),
    },
    "audit_logs": {
        (("user_id",), "users", ("id",), None),
        (("clinic_id",), "clinics", ("id",), None),
    },
}

EXPECTED_INDEXES: dict[str, set[tuple[str, ...]]] = {
    "statuses": {("name",), ("applies_to",)},
    "roles": {("name",)},
    "permissions": {("name",), ("module",)},
    "role_permissions": {("role_id",), ("permission_id",)},
    "clinics": {("name",), ("cnpj",), ("email",), ("status_id",)},
    "users": {
        ("email",),
        ("cpf",),
        ("role_id",),
        ("status_id",),
        ("clinic_id",),
    },
    "patients": {
        ("name",),
        ("cpf",),
        ("clinic_id",),
        ("doctor_id",),
        ("status_id",),
    },
    "exams": {
        ("exam_type",),
        ("clinic_id",),
        ("patient_id",),
        ("doctor_id",),
        ("status_id",),
        ("reviewed_by_id",),
    },
    "ai_analysis": {("exam_id",), ("status_id",)},
    "audit_logs": {
        ("action",),
        ("entity",),
        ("entity_id",),
        ("user_id",),
        ("clinic_id",),
    },
}

EXPECTED_BOOTSTRAP_COUNTS = {
    "statuses": 17,
    "roles": 3,
    "permissions": len(OFFICIAL_PERMISSION_NAMES),
    "role_permissions": (
        len(OFFICIAL_PERMISSION_NAMES)
        + len(DOCTOR_PERMISSIONS)
        + len(CLINIC_STAFF_PERMISSIONS)
    ),
}

EXPECTED_DEMO_COUNTS = {
    **EXPECTED_BOOTSTRAP_COUNTS,
    "clinics": 8,
    "users": 5,
    "patients": 8,
    "exams": 3,
    "ai_analysis": 2,
    "audit_logs": 0,
}


def _json_dump(data: Any) -> str:
    return (
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        + "\n"
    )


def _write_json(path: str | None, data: Any) -> None:
    rendered = _json_dump(data)
    if path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def _normalize_ondelete(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.upper().replace("_", " ")
    if normalized in {"NO ACTION", "RESTRICT"}:
        return None
    return normalized


def _unique_sets(inspector: sa.Inspector, table: str) -> set[tuple[str, ...]]:
    uniques = {
        tuple(item["column_names"])
        for item in inspector.get_unique_constraints(table)
        if item.get("column_names")
    }
    uniques.update(
        tuple(item["column_names"])
        for item in inspector.get_indexes(table)
        if item.get("unique") and item.get("column_names")
    )
    return uniques


def _foreign_key_sets(
    inspector: sa.Inspector,
    table: str,
) -> set[tuple[tuple[str, ...], str, tuple[str, ...], str | None]]:
    result = set()
    for item in inspector.get_foreign_keys(table):
        options = item.get("options") or {}
        result.add(
            (
                tuple(item["constrained_columns"]),
                item["referred_table"],
                tuple(item["referred_columns"]),
                _normalize_ondelete(options.get("ondelete")),
            )
        )
    return result


def _index_sets(inspector: sa.Inspector, table: str) -> set[tuple[str, ...]]:
    return {
        tuple(item["column_names"])
        for item in inspector.get_indexes(table)
        if item.get("column_names")
    }


def _alembic_revisions(connection: sa.Connection) -> tuple[str | None, tuple[str, ...]]:
    migration_context = MigrationContext.configure(connection)
    current = migration_context.get_current_revision()

    backend_root = Path(__file__).resolve().parents[2]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    script = ScriptDirectory.from_config(config)
    heads = tuple(script.get_heads())
    return current, heads


def assert_empty_database() -> None:
    """Confirma que não há tabelas da aplicação antes das migrations."""

    actual = set(inspect(engine).get_table_names(schema="public"))
    forbidden = actual.intersection(set(APP_TABLES) | {"alembic_version"})
    if forbidden:
        raise AssertionError(
            "O banco não está vazio antes do alembic upgrade head: "
            + ", ".join(sorted(forbidden))
        )
    print("CHK-03: banco público vazio antes das migrations.")


def verify_schema(output: str | None = None) -> None:
    """Valida revisão, tabelas, uniques, FKs, cascatas e índices."""

    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names(schema="public"))
    missing_tables = set(APP_TABLES) - actual_tables
    if missing_tables:
        raise AssertionError(
            "Tabelas ausentes após migrations: " + ", ".join(sorted(missing_tables))
        )

    with engine.connect() as connection:
        current, heads = _alembic_revisions(connection)
    if len(heads) != 1:
        raise AssertionError(f"A árvore Alembic possui {len(heads)} heads: {heads}")
    if current != heads[0]:
        raise AssertionError(
            f"Revisão ativa {current!r} difere do head único {heads[0]!r}."
        )

    inventory: dict[str, Any] = {
        "alembic": {"current": current, "heads": list(heads)},
        "tables": {},
    }

    for table in APP_TABLES:
        actual_uniques = _unique_sets(inspector, table)
        expected_uniques = EXPECTED_UNIQUES.get(table, set())
        missing_uniques = expected_uniques - actual_uniques
        if missing_uniques:
            raise AssertionError(
                f"Unique constraints ausentes em {table}: {sorted(missing_uniques)}"
            )

        actual_fks = _foreign_key_sets(inspector, table)
        expected_fks = EXPECTED_FOREIGN_KEYS.get(table, set())
        missing_fks = expected_fks - actual_fks
        if missing_fks:
            raise AssertionError(
                f"FKs/cascatas ausentes em {table}: {sorted(missing_fks)}"
            )

        actual_indexes = _index_sets(inspector, table)
        expected_indexes = EXPECTED_INDEXES.get(table, set())
        missing_indexes = expected_indexes - actual_indexes
        if missing_indexes:
            raise AssertionError(
                f"Índices ausentes em {table}: {sorted(missing_indexes)}"
            )

        inventory["tables"][table] = {
            "columns": [column["name"] for column in inspector.get_columns(table)],
            "unique_columns": [list(value) for value in sorted(actual_uniques)],
            "foreign_keys": [
                {
                    "columns": list(columns),
                    "references": f"{referred_table}({', '.join(referred_columns)})",
                    "on_delete": ondelete or "RESTRICT/NO ACTION",
                }
                for columns, referred_table, referred_columns, ondelete in sorted(
                    actual_fks
                )
            ],
            "indexes": [list(value) for value in sorted(actual_indexes)],
        }

    _write_json(output, inventory)
    print("CHK-03: schema, uniques, FKs, cascatas e índices aprovados.")


def table_counts(db: Session) -> dict[str, int]:
    return {
        table_name: int(
            db.execute(sa.text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()
        )
        for table_name in APP_TABLES
    }


def assert_no_demo_data() -> None:
    db = SessionLocal()
    try:
        counts = table_counts(db)
        for table, expected in EXPECTED_BOOTSTRAP_COUNTS.items():
            if counts[table] != expected:
                raise AssertionError(
                    f"Contagem bootstrap de {table}: {counts[table]} != {expected}."
                )
        unexpected = {table: counts[table] for table in DEMO_TABLES if counts[table]}
        if unexpected:
            raise AssertionError(f"O modo bootstrap criou dados demo: {unexpected}")
    finally:
        db.close()
    print("CHK-03: bootstrap estrutural sem dados de demonstração.")


def assert_demo_data() -> None:
    from app.core.security import verify_password
    from app.modules.users.seed import (
        ACADEMIC_DEMO_EMAILS,
        ACADEMIC_DEMO_PASSWORD,
    )

    db = SessionLocal()
    try:
        counts = table_counts(db)
        mismatches = {
            table: {"actual": counts[table], "expected": expected}
            for table, expected in EXPECTED_DEMO_COUNTS.items()
            if counts[table] != expected
        }
        if mismatches:
            raise AssertionError(f"Contagens acadêmicas divergentes: {mismatches}")

        from app.modules.users.model import User

        rows = (
            db.query(User)
            .filter(User.email.in_(ACADEMIC_DEMO_EMAILS))
            .order_by(User.email)
            .all()
        )
        if {row.email for row in rows} != set(ACADEMIC_DEMO_EMAILS):
            raise AssertionError(
                "As cinco contas acadêmicas esperadas não foram criadas."
            )
        for row in rows:
            if not verify_password(ACADEMIC_DEMO_PASSWORD, row.password_hash):
                raise AssertionError(f"Senha acadêmica inesperada para {row.email}.")

        inconsistent_patients = (
            db.execute(
                sa.text(
                    """
                SELECT patients.id
                FROM patients
                JOIN users ON users.id = patients.doctor_id
                WHERE patients.clinic_id <> users.clinic_id
                """
                )
            )
            .scalars()
            .all()
        )
        if inconsistent_patients:
            raise AssertionError(
                f"Pacientes demo vinculados a médico de outra clínica: {inconsistent_patients}"
            )

        inconsistent_exams = (
            db.execute(
                sa.text(
                    """
                SELECT exams.id
                FROM exams
                JOIN patients ON patients.id = exams.patient_id
                JOIN users ON users.id = exams.doctor_id
                WHERE exams.clinic_id <> patients.clinic_id
                   OR exams.clinic_id <> users.clinic_id
                """
                )
            )
            .scalars()
            .all()
        )
        if inconsistent_exams:
            raise AssertionError(
                f"Exames demo com vínculos cruzados: {inconsistent_exams}"
            )
    finally:
        db.close()
    print("CHK-03: massa acadêmica fictícia, credenciais e vínculos aprovados.")


def apply_test_customization() -> None:
    """Aplica mudanças administrativas no banco descartável do CHK-03."""

    db = SessionLocal()
    try:
        doctor_id = db.execute(
            sa.text("SELECT id FROM roles WHERE name = 'doctor'")
        ).scalar_one()
        download_id = db.execute(
            sa.text("SELECT id FROM permissions WHERE name = 'exams:download'")
        ).scalar_one()
        audit_read_id = db.execute(
            sa.text("SELECT id FROM permissions WHERE name = 'audit_logs:read'")
        ).scalar_one()

        db.execute(
            sa.text("UPDATE roles SET display_name = :value WHERE id = :role_id"),
            {
                "value": "Médico — configuração preservada CHK-03",
                "role_id": doctor_id,
            },
        )
        db.execute(
            sa.text(
                """
                UPDATE statuses
                SET display_name = :value
                WHERE name = 'pending' AND applies_to = 'exam'
                """
            ),
            {"value": "Pendente — configuração preservada CHK-03"},
        )
        db.execute(
            sa.text(
                """
                DELETE FROM role_permissions
                WHERE role_id = :role_id AND permission_id = :permission_id
                """
            ),
            {"role_id": doctor_id, "permission_id": download_id},
        )
        db.execute(
            sa.text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT :role_id, :permission_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM role_permissions
                    WHERE role_id = :role_id AND permission_id = :permission_id
                )
                """
            ),
            {"role_id": doctor_id, "permission_id": audit_read_id},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print("CHK-03: customização administrativa de teste aplicada.")


def _rows(db: Session, query: str) -> list[dict[str, Any]]:
    return [dict(row._mapping) for row in db.execute(sa.text(query)).all()]


def semantic_snapshot() -> dict[str, Any]:
    """Captura apenas valores estáveis e relevantes à idempotência."""

    db = SessionLocal()
    try:
        snapshot = {
            "counts": table_counts(db),
            "roles": _rows(
                db,
                """
                SELECT name, display_name, description, permissions_initialized
                FROM roles ORDER BY name
                """,
            ),
            "statuses": _rows(
                db,
                """
                SELECT name, applies_to, display_name, description
                FROM statuses ORDER BY applies_to, name
                """,
            ),
            "permissions": _rows(
                db,
                """
                SELECT name, module, display_name, description
                FROM permissions ORDER BY name
                """,
            ),
            "role_permissions": _rows(
                db,
                """
                SELECT roles.name AS role_name,
                       permissions.name AS permission_name
                FROM role_permissions
                JOIN roles ON roles.id = role_permissions.role_id
                JOIN permissions ON permissions.id = role_permissions.permission_id
                ORDER BY roles.name, permissions.name
                """,
            ),
            "clinics": _rows(
                db,
                """
                SELECT clinics.cnpj, clinics.name, clinics.email,
                       statuses.name AS status_name
                FROM clinics
                JOIN statuses ON statuses.id = clinics.status_id
                ORDER BY clinics.cnpj
                """,
            ),
            "users": _rows(
                db,
                """
                SELECT users.email, users.cpf, users.name,
                       roles.name AS role_name,
                       statuses.name AS status_name,
                       clinics.cnpj AS clinic_cnpj
                FROM users
                JOIN roles ON roles.id = users.role_id
                JOIN statuses ON statuses.id = users.status_id
                LEFT JOIN clinics ON clinics.id = users.clinic_id
                ORDER BY users.email
                """,
            ),
            "patients": _rows(
                db,
                """
                SELECT patients.cpf, patients.name,
                       clinics.cnpj AS clinic_cnpj,
                       users.email AS doctor_email,
                       statuses.name AS status_name
                FROM patients
                JOIN clinics ON clinics.id = patients.clinic_id
                JOIN users ON users.id = patients.doctor_id
                JOIN statuses ON statuses.id = patients.status_id
                ORDER BY clinics.cnpj, patients.cpf
                """,
            ),
            "exams": _rows(
                db,
                """
                SELECT exams.title, exams.exam_type, exams.exam_date,
                       patients.cpf AS patient_cpf,
                       users.email AS doctor_email,
                       clinics.cnpj AS clinic_cnpj,
                       statuses.name AS status_name,
                       exams.file_path, exams.file_name, exams.file_mime_type
                FROM exams
                JOIN patients ON patients.id = exams.patient_id
                JOIN users ON users.id = exams.doctor_id
                JOIN clinics ON clinics.id = exams.clinic_id
                JOIN statuses ON statuses.id = exams.status_id
                ORDER BY exams.title
                """,
            ),
            "ai_analysis": _rows(
                db,
                """
                SELECT exams.title AS exam_title,
                       ai_analysis.prediction_label,
                       ai_analysis.prediction_class,
                       ai_analysis.confidence,
                       ai_analysis.model_name,
                       ai_analysis.model_version,
                       statuses.name AS status_name
                FROM ai_analysis
                JOIN exams ON exams.id = ai_analysis.exam_id
                JOIN statuses ON statuses.id = ai_analysis.status_id
                ORDER BY exams.title
                """,
            ),
        }
        return snapshot
    finally:
        db.close()


def write_snapshot(output: str) -> None:
    _write_json(output, semantic_snapshot())
    print(f"CHK-03: snapshot semântico salvo em {output}.")


def compare_snapshots(expected_path: str, actual_path: str) -> None:
    expected = Path(expected_path).read_text(encoding="utf-8").splitlines()
    actual = Path(actual_path).read_text(encoding="utf-8").splitlines()
    if expected != actual:
        diff = "\n".join(
            difflib.unified_diff(
                expected,
                actual,
                fromfile=expected_path,
                tofile=actual_path,
                lineterm="",
            )
        )
        raise AssertionError("Snapshots divergentes:\n" + diff)
    print(f"CHK-03: snapshots idênticos: {expected_path} == {actual_path}.")


def assert_index(table: str, columns: Iterable[str], present: bool) -> None:
    wanted = tuple(columns)
    actual = _index_sets(inspect(engine), table)
    exists = wanted in actual
    if exists != present:
        expectation = "presente" if present else "ausente"
        raise AssertionError(
            f"Índice {table}{wanted} deveria estar {expectation}; índices: {sorted(actual)}"
        )
    print(f"CHK-03: índice {table}{wanted} no estado esperado ({present=}).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verificações do CHK-03.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("assert-empty")

    schema_parser = subparsers.add_parser("verify-schema")
    schema_parser.add_argument("--output")

    subparsers.add_parser("assert-no-demo")
    subparsers.add_parser("assert-demo")
    subparsers.add_parser("customize")

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("--output", required=True)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--expected", required=True)
    compare_parser.add_argument("--actual", required=True)

    index_parser = subparsers.add_parser("assert-index")
    index_parser.add_argument("--table", required=True)
    index_parser.add_argument("--columns", nargs="+", required=True)
    index_parser.add_argument(
        "--present",
        choices=("true", "false"),
        required=True,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "assert-empty":
        assert_empty_database()
    elif args.command == "verify-schema":
        verify_schema(args.output)
    elif args.command == "assert-no-demo":
        assert_no_demo_data()
    elif args.command == "assert-demo":
        assert_demo_data()
    elif args.command == "customize":
        apply_test_customization()
    elif args.command == "snapshot":
        write_snapshot(args.output)
    elif args.command == "compare":
        compare_snapshots(args.expected, args.actual)
    elif args.command == "assert-index":
        assert_index(
            table=args.table,
            columns=args.columns,
            present=args.present == "true",
        )
    else:  # pragma: no cover - argparse impede este caminho.
        raise AssertionError(f"Comando desconhecido: {args.command}")


if __name__ == "__main__":
    main()
