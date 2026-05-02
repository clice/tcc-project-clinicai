"""
Seed do módulo de roles.

Este arquivo cadastra os perfis iniciais usados pelo sistema.
"""

from sqlalchemy.orm import Session

from app.modules.roles.model import Role


def get_or_create_role(
    db: Session,
    name: str,
    display_name: str,
    description: str | None = None,
) -> Role:
    """
    Busca uma role existente ou cria uma nova.
    Evita duplicação nos seeds.
    """
    role = db.query(Role).filter(Role.name == name).first()

    if role:
        return role

    role = Role(
        name=name,
        display_name=display_name,
        description=description,
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


def seed_roles(db: Session) -> dict[str, Role]:
    """
    Cria os perfis iniciais do sistema.
    Retorna um dicionário para que outros seeds possam reutilizar
    esses registros, por exemplo no seed de usuários.
    """

    return {
        "admin_master": get_or_create_role(
            db,
            name="admin_master",
            display_name="Administrador Master",
            description="Administrador com acesso total ao sistema.",
        ),
        "doctor": get_or_create_role(
            db,
            name="doctor",
            display_name="Médico",
            description="Profissional médico vinculado a uma clínica.",
        ),
        "clinic_staff": get_or_create_role(
            db,
            name="clinic_staff",
            display_name="Funcionário da clínica",
            description="Funcionário da clínica com acesso operacional ao sistema.",
        ),
    }