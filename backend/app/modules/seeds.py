"""Bootstrap estrutural e massa acadêmica opcional do ClinicAI.

O startup sempre pode executar este módulo com segurança. O modo ``bootstrap``
cria os catálogos indispensáveis e um único Administrador Master inicial:
statuses, roles, permissions, matriz de role-permissions e usuário administrativo.
O modo ``academic_demo`` executa o mesmo bootstrap e, em uma transação separada,
acrescenta somente clínicas, usuários, pacientes, exames e análises fictícios.

Evoluções oficiais do schema pertencem a migrations Alembic. O bootstrap não
sobrescreve configurações administrativas; a massa acadêmica, por sua vez,
reconcilia apenas os registros identificados pelas chaves reservadas do dataset.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal

# Registra todos os models antes de usar relacionamentos e metadata.
from app.modules import models  # noqa: F401
from app.modules.ai_analyses.model import AIAnalysis
from app.modules.ai_analyses.seed import seed_ai_analysis
from app.modules.audit_logs.model import AuditLog
from app.modules.audit_logs.seed import (
    seed_academic_demo_audit_logs,
)
from app.modules.clinics.model import Clinic
from app.modules.clinics.seed import seed_clinics
from app.modules.exams.model import Exam
from app.modules.exams.seed import seed_exams
from app.modules.patients.model import Patient
from app.modules.patients.seed import seed_patients
from app.modules.permissions.model import Permission
from app.modules.permissions.seed import seed_permissions
from app.modules.role_permissions.seed import seed_role_permissions
from app.modules.roles.model import Role
from app.modules.roles.seed import seed_roles
from app.modules.statuses.model import Status
from app.modules.statuses.seed import seed_statuses
from app.modules.users.model import User
from app.modules.users.seed import seed_bootstrap_admin, seed_users

SeedMode = Literal["bootstrap", "academic_demo"]


@dataclass(frozen=True)
class BootstrapResult:
    """Objetos estruturais disponibilizados ao restante do bootstrap."""

    statuses: dict[str, Status]
    roles: dict[str, Role]
    permissions: dict[str, Permission]
    bootstrapped_roles: tuple[str, ...]
    admin_user: User


@dataclass(frozen=True)
class AcademicDemoResult:
    """Objetos fictícios criados pelo dataset acadêmico versionado."""

    clinics: dict[str, Clinic]
    users: dict[str, User]
    patients: dict[str, Patient]
    exams: dict[str, Exam]
    ai_analyses: dict[str, AIAnalysis]
    audit_logs: dict[str, AuditLog]


def bootstrap_reference_data(db: Session) -> BootstrapResult:
    """Cria/valida apenas dados estruturais e não destrutivos.

    A transação é controlada pelo chamador. As funções de cada módulo usam
    ``flush`` para obter IDs sem realizar commits parciais.
    """

    statuses = seed_statuses(db)
    roles = seed_roles(db)
    permissions = seed_permissions(db)
    bootstrapped_roles = tuple(seed_role_permissions(db, roles, permissions))
    admin_user = seed_bootstrap_admin(
        db,
        roles,
        statuses,
        name=settings.bootstrap_admin_name,
        email=settings.bootstrap_admin_email,
        cpf=settings.bootstrap_admin_cpf,
        password=settings.bootstrap_admin_password,
    )

    return BootstrapResult(
        statuses=statuses,
        roles=roles,
        permissions=permissions,
        bootstrapped_roles=bootstrapped_roles,
        admin_user=admin_user,
    )


def seed_academic_demo(
    db: Session,
    bootstrap: BootstrapResult,
) -> AcademicDemoResult:
    """Cria a massa fictícia do ambiente acadêmico de demonstração.

    Os vínculos são resolvidos por chaves semânticas conhecidas, nunca por
    "primeiro registro" do banco. Assim, registros administrativos criados
    antes da massa demo não mudam clínica, médico ou status dos dados fictícios.
    """

    clinics = seed_clinics(db, bootstrap.statuses)
    users = seed_users(
        db,
        bootstrap.roles,
        bootstrap.statuses,
        clinics,
        admin_master=bootstrap.admin_user,
    )
    patients = seed_patients(
        db,
        clinics=clinics,
        users=users,
        statuses=bootstrap.statuses,
    )
    exams = seed_exams(
        db,
        clinics=clinics,
        patients=patients,
        users=users,
        statuses=bootstrap.statuses,
    )
    ai_analyses = seed_ai_analysis(
        db,
        exams,
        statuses=bootstrap.statuses,
    )
    audit_logs = seed_academic_demo_audit_logs(
        db,
        exams=exams,
        ai_analyses=ai_analyses,
        users=users,
        statuses=bootstrap.statuses,
    )

    return AcademicDemoResult(
        clinics=clinics,
        users=users,
        patients=patients,
        exams=exams,
        ai_analyses=ai_analyses,
        audit_logs=audit_logs,
    )


def run_seed(mode: SeedMode | None = None) -> None:
    """Executa o modo solicitado com commits atômicos por fase."""

    selected_mode: SeedMode = mode or settings.seed_mode
    db = SessionLocal()

    try:
        print(f"[seed] Modo selecionado: {selected_mode}.")

        try:
            bootstrap = bootstrap_reference_data(db)
            db.commit()
        except Exception:
            db.rollback()
            raise

        if bootstrap.bootstrapped_roles:
            print(
                "[seed] Role permissions inicializadas para: "
                + ", ".join(bootstrap.bootstrapped_roles)
                + "."
            )
        else:
            print(
                "[seed] Role permissions já configuradas; "
                "customizações administrativas preservadas."
            )
        print(
            "[seed] Bootstrap concluído com Administrador Master disponível em "
            f"{bootstrap.admin_user.email}."
        )

        if selected_mode == "academic_demo":
            try:
                demo = seed_academic_demo(db, bootstrap)
                db.commit()
            except Exception:
                db.rollback()
                raise

            print(
                "[seed] Massa acadêmica demonstrativa pronta: "
                f"{len(demo.clinics)} clínicas, "
                f"{len(demo.users)} usuários, "
                f"{len(demo.patients)} pacientes, "
                f"{len(demo.exams)} exames, "
                f"{len(demo.ai_analyses)} análises e "
                f"{len(demo.audit_logs)} eventos de auditoria."
            )
        else:
            print(
                "[seed] Dados de demonstração não foram criados. "
                "Use SEED_MODE=academic_demo somente em ambiente acadêmico."
            )
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inicializa dados estruturais e, opcionalmente, a massa acadêmica.",
    )
    parser.add_argument(
        "--mode",
        choices=("bootstrap", "academic_demo"),
        default=None,
        help=(
            "Sobrescreve SEED_MODE apenas nesta execução. O padrão seguro é bootstrap."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_seed(mode=arguments.mode)
