"""
Seed do módulo de roles.

Este arquivo cadastra apenas os perfis oficiais definidos em constants.py.
"""

from sqlalchemy.orm import Session

from app.common.constants import RoleName
from app.modules.roles.model import Role


def get_or_create_role(
    db: Session,
    name: RoleName,
    display_name: str,
    description: str | None = None,
) -> Role:
    role = db.query(Role).filter(Role.name == name.value).first()

    if role:
        return role

    role = Role(
        name=name.value,
        display_name=display_name,
        description=description,
    )

    db.add(role)
    db.flush()
    db.refresh(role)

    return role


def seed_roles(db: Session) -> dict[str, Role]:
    return {
        "admin_master": get_or_create_role(
            db,
            name=RoleName.ADMIN_MASTER,
            display_name="Administrador Master",
            description="Administrador com acesso total ao sistema.",
        ),
        "doctor": get_or_create_role(
            db,
            name=RoleName.DOCTOR,
            display_name="Médico",
            description="Profissional médico vinculado a uma clínica.",
        ),
        "clinic_manager": get_or_create_role(
            db,
            name=RoleName.CLINIC_MANAGER,
            display_name="Gestor da Clínica",
            description="Gestor responsável pela operação e pelos médicos da própria clínica.",
        ),
    }
