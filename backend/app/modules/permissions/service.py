"""
Service do módulo de permissions.

Aqui ficam as regras de negócio e operações com o banco.
O router deve ficar mais limpo e apenas chamar essas funções.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.permissions.model import Permission
from app.modules.permissions.schema import PermissionCreate, PermissionUpdate


def check_permission_duplicate(
    db: Session,
    name: str,
    ignore_permission_id: int | None = None,
) -> None:
    """
    Verifica se já existe outra permission com o mesmo name.
    O campo name deve ser único porque será usado internamente
    para autorização.
    """
    query = db.query(Permission).filter(Permission.name == name)

    # Usado no update para ignorar o próprio registro.
    if ignore_permission_id is not None:
        query = query.filter(Permission.id != ignore_permission_id)

    duplicated = query.first()

    if duplicated:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma permissão com esse nome.",
        )


def get_permission_by_id(db: Session, permission_id: int) -> Permission:
    """
    Busca uma permission pelo ID.
    Se não existir, retorna erro 404.
    """
    permission = (
        db.query(Permission)
        .filter(Permission.id == permission_id)
        .first()
    )

    if not permission:
        raise HTTPException(status_code=404, detail="Permissão não encontrada.")

    return permission


def list_permissions(db: Session) -> list[Permission]:
    """
    Lista todas as permissões cadastradas.
    """
    return (
        db.query(Permission)
        .order_by(Permission.module.asc(), Permission.display_name.asc())
        .all()
    )


def create_permission(db: Session, payload: PermissionCreate) -> Permission:
    """
    Cria uma nova permissão.
    """
    module = payload.module.value

    check_permission_duplicate(db=db, name=payload.name)

    permission = Permission(
        name=payload.name,
        display_name=payload.display_name,
        description=payload.description,
        module=module,
    )

    db.add(permission)
    db.commit()
    db.refresh(permission)

    return permission


def update_permission(
    db: Session,
    permission_id: int,
    payload: PermissionUpdate,
) -> Permission:
    """
    Atualiza parcialmente uma permissão.
    """
    permission = get_permission_by_id(db, permission_id)

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return permission

    if "module" in update_data and update_data["module"] is not None:
        update_data["module"] = update_data["module"].value

    new_name = update_data.get("name", permission.name)

    check_permission_duplicate(
        db=db,
        name=new_name,
        ignore_permission_id=permission_id,
    )

    for field, value in update_data.items():
        setattr(permission, field, value)

    db.commit()
    db.refresh(permission)

    return permission
