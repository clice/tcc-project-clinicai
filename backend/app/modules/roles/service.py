"""
Service do módulo de roles.

Aqui ficam as regras de negócio e operações com o banco.
O router deve ficar mais limpo e apenas chamar essas funções.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.roles.model import Role
from app.modules.roles.schema import RoleCreate, RoleUpdate


def get_role_by_id(db: Session, role_id: int) -> Role:
    """
    Busca uma role pelo ID.

    Se não existir, retorna erro 404.
    """
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")

    return role


def check_role_duplicate(
    db: Session,
    name: str,
    ignore_role_id: int | None = None,
) -> None:
    """
    Verifica se já existe outra role com o mesmo name.
    O campo name deve ser único porque será usado internamente
    para regras de autenticação e autorização.
    """
    query = db.query(Role).filter(Role.name == name)

    # Usado no update para ignorar o próprio registro.
    if ignore_role_id is not None:
        query = query.filter(Role.id != ignore_role_id)

    duplicated = query.first()

    if duplicated:
        raise HTTPException(
            status_code=400,
            detail="Já existe um perfil com esse nome.",
        )


def list_roles(db: Session) -> list[Role]:
    """
    Lista todos os perfis cadastrados.
    """
    return (
        db.query(Role)
        .order_by(Role.display_name.asc())
        .all()
    )


def create_role(db: Session, payload: RoleCreate) -> Role:
    """
    Cria um novo perfil de acesso.
    """
    check_role_duplicate(db=db, name=payload.name)

    role = Role(
        name=payload.name,
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
    """
    Atualiza parcialmente um perfil de acesso.
    Usa exclude_unset=True para alterar apenas os campos enviados.
    """
    role = get_role_by_id(db, role_id)

    update_data = payload.model_dump(exclude_unset=True)

    # Se nenhum campo foi enviado, apenas retorna a role atual.
    if not update_data:
        return role

    new_name = update_data.get("name", role.name)

    check_role_duplicate(
        db=db,
        name=new_name,
        ignore_role_id=role_id,
    )

    # Atualiza apenas os campos enviados.
    for field, value in update_data.items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)

    return role