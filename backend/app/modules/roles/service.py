"""
Service do módulo de roles.

Aqui ficam as regras de negócio e operações com o banco.
O router deve ficar mais limpo e apenas chamar essas funções.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.roles.model import Role
from app.modules.roles.schema import RoleCreate, RoleUpdate


def check_role_duplicate(
    db: Session,
    name: str,
    ignore_role_id: int | None = None,
) -> None:
    query = db.query(Role).filter(Role.name == name)

    if ignore_role_id is not None:
        query = query.filter(Role.id != ignore_role_id)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="Já existe um perfil com esse nome.",
        )


def get_role_by_id(db: Session, role_id: int) -> Role:
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")

    return role


def list_roles(db: Session) -> list[Role]:
    return db.query(Role).order_by(Role.display_name.asc()).all()


def create_role(db: Session, payload: RoleCreate) -> Role:
    name = payload.name.value

    check_role_duplicate(db=db, name=name)

    role = Role(
        name=name,
        display_name=payload.display_name,
        description=payload.description,
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


def update_role(
    db: Session,
    role_id: int,
    payload: RoleUpdate,
) -> Role:
    role = get_role_by_id(db, role_id)

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return role

    if "name" in update_data and update_data["name"] is not None:
        update_data["name"] = update_data["name"].value

    new_name = update_data.get("name", role.name)

    check_role_duplicate(
        db=db,
        name=new_name,
        ignore_role_id=role_id,
    )

    for field, value in update_data.items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)

    return role
