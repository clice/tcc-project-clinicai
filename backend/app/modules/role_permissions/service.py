"""
Service do módulo de role_permissions.

Aqui ficam as regras de negócio relacionadas aos vínculos
entre perfis de acesso e permissões.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.common.constants import AuditAction, AuditEntity
from app.common.services import (
    apply_update_data,
    model_dump_update,
)
from app.modules.permissions.model import Permission
from app.modules.roles.model import Role
from app.modules.role_permissions.model import RolePermission
from app.modules.users.model import User
from app.modules.role_permissions.schema import (
    RolePermissionCreate,
    RolePermissionUpdate,
)
from app.modules.audit_logs.service import create_audit_log


def validate_role_exists(db: Session, role_id: int) -> Role:
    """
    Valida se a role informada existe.
    """
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Perfil de acesso não encontrado.",
        )

    return role


def validate_permission_exists(db: Session, permission_id: int) -> Permission:
    """
    Valida se a permission informada existe.
    """
    permission = (
        db.query(Permission)
        .filter(Permission.id == permission_id)
        .first()
    )

    if not permission:
        raise HTTPException(
            status_code=404,
            detail="Permissão não encontrada.",
        )

    return permission


def check_role_permission_duplicate(
    db: Session,
    role_id: int,
    permission_id: int,
    ignore_role_permission_id: int | None = None,
) -> None:
    """
    Verifica se já existe o mesmo vínculo entre role e permission.
    """
    query = db.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id,
    )

    if ignore_role_permission_id is not None:
        query = query.filter(RolePermission.id != ignore_role_permission_id)

    duplicated = query.first()

    if duplicated:
        raise HTTPException(
            status_code=400,
            detail="Essa permissão já está vinculada a esse perfil.",
        )


# ========================================
# MAIN METHODS
# ========================================


def build_role_permission_response(role_permission: RolePermission) -> dict:
    """
    Monta a resposta enriquecida (com nomes de role/permission) a partir
    do objeto ORM.

    Antes, o router devolvia o objeto `RolePermission` cru para
    `RolePermissionResponse` (via `from_attributes`), mas o model só tem
    os relacionamentos `role`/`permission` (objetos aninhados) — não os
    campos escalares `role_name`, `permission_name` etc. que o schema
    declara. O Pydantic simplesmente não encontrava esses atributos e
    devolvia `None` silenciosamente. Esta função busca os valores certos
    dentro dos relacionamentos.
    """
    return {
        "id": role_permission.id,
        "role_id": role_permission.role_id,
        "permission_id": role_permission.permission_id,
        "role_name": role_permission.role.name if role_permission.role else None,
        "role_display_name": (
            role_permission.role.display_name if role_permission.role else None
        ),
        "permission_name": (
            role_permission.permission.name if role_permission.permission else None
        ),
        "permission_display_name": (
            role_permission.permission.display_name if role_permission.permission else None
        ),
        "permission_module": (
            role_permission.permission.module if role_permission.permission else None
        ),
        "created_at": role_permission.created_at,
        "updated_at": role_permission.updated_at,
    }


def get_role_permission_by_id(
    db: Session,
    role_permission_id: int,
) -> RolePermission:
    """
    Busca um vínculo pelo ID.

    Se não existir, retorna erro 404.
    """
    role_permission = (
        db.query(RolePermission)
        .options(
            joinedload(RolePermission.role),
            joinedload(RolePermission.permission),
        )
        .filter(RolePermission.id == role_permission_id)
        .first()
    )

    if not role_permission:
        raise HTTPException(
            status_code=404,
            detail="Vínculo entre perfil e permissão não encontrado.",
        )

    return role_permission


def list_role_permissions(db: Session) -> list[RolePermission]:
    """
    Lista todos os vínculos cadastrados.
    """
    return (
        db.query(RolePermission)
        .options(
            joinedload(RolePermission.role),
            joinedload(RolePermission.permission),
        )
        .order_by(RolePermission.role_id.asc(), RolePermission.permission_id.asc())
        .all()
    )


def create_role_permission(
    db: Session,
    payload: RolePermissionCreate,
    current_user: User,
) -> RolePermission:
    """
    Cria um novo vínculo entre role e permission.
    """
    role = validate_role_exists(db=db, role_id=payload.role_id)
    permission = validate_permission_exists(db=db, permission_id=payload.permission_id)

    check_role_permission_duplicate(
        db=db,
        role_id=payload.role_id,
        permission_id=payload.permission_id,
    )

    role_permission = RolePermission(
        role_id=payload.role_id,
        permission_id=payload.permission_id,
    )

    db.add(role_permission)
    db.flush()

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.CREATE,
        entity=AuditEntity.ROLE_PERMISSION,
        entity_id=role_permission.id,
        description="Permissão vinculada ao perfil de acesso.",
        new_data={
            "id": role_permission.id,
            "role_id": role_permission.role_id,
            "role_name": role.name,
            "permission_id": role_permission.permission_id,
            "permission_name": permission.name,
        },
    )

    db.commit()
    db.refresh(role_permission)

    return role_permission


def update_role_permission(
    db: Session,
    role_permission_id: int,
    payload: RolePermissionUpdate,
    current_user: User,
) -> RolePermission:
    """
    Atualiza parcialmente um vínculo existente.
    """
    role_permission = get_role_permission_by_id(
        db=db,
        role_permission_id=role_permission_id,
    )

    update_data = model_dump_update(payload)

    if not update_data:
        return role_permission

    old_data = {
        "role_id": role_permission.role_id,
        "role_name": role_permission.role.name if role_permission.role else None,
        "permission_id": role_permission.permission_id,
        "permission_name": role_permission.permission.name if role_permission.permission else None,
    }

    new_role_id = update_data.get("role_id", role_permission.role_id)
    new_permission_id = update_data.get(
        "permission_id",
        role_permission.permission_id,
    )

    role = validate_role_exists(db=db, role_id=new_role_id)
    permission = validate_permission_exists(db=db, permission_id=new_permission_id)

    check_role_permission_duplicate(
        db=db,
        role_id=new_role_id,
        permission_id=new_permission_id,
        ignore_role_permission_id=role_permission_id,
    )

    apply_update_data(role_permission, update_data)

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.ROLE_PERMISSION,
        entity_id=role_permission.id,
        description="Vínculo entre perfil e permissão atualizado.",
        old_data=old_data,
        new_data={
            "role_id": new_role_id,
            "role_name": role.name,
            "permission_id": new_permission_id,
            "permission_name": permission.name,
        },
    )

    db.commit()
    db.refresh(role_permission)

    return role_permission


def delete_role_permission(
    db: Session,
    role_permission_id: int,
    current_user: User,
) -> dict[str, str]:
    """
    Remove um vínculo entre role e permission.
    """
    role_permission = get_role_permission_by_id(
        db=db,
        role_permission_id=role_permission_id,
    )

    old_data = {
        "id": role_permission.id,
        "role_id": role_permission.role_id,
        "role_name": role_permission.role.name if role_permission.role else None,
        "permission_id": role_permission.permission_id,
        "permission_name": role_permission.permission.name if role_permission.permission else None,
    }

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=current_user.clinic_id,
        action=AuditAction.DELETE,
        entity=AuditEntity.ROLE_PERMISSION,
        entity_id=role_permission.id,
        description="Vínculo entre perfil e permissão removido.",
        old_data=old_data,
    )

    db.delete(role_permission)
    db.commit()

    return {"detail": "Vínculo removido com sucesso."}


def sync_role_permissions(
    db: Session,
    role_id: int,
    permission_ids: list[int],
    current_user: User,
) -> list[RolePermission]:
    """
    Sincroniza, em uma única transação, todos os vínculos de uma role com
    a lista final de permission_ids desejada.

    Antes, o frontend fazia isso com vários POST/DELETE via Promise.all:
    se uma requisição falhasse no meio, parte das permissões ficava
    aplicada e parte não. Além disso, como as adições aconteciam antes das
    remoções, existia uma janela real (mesmo que curta) em que a role
    tinha MAIS permissões do que a matriz final pretendia — um problema de
    segurança, não só de consistência. Aqui, tudo é calculado e aplicado
    de uma vez, com rollback integral em qualquer erro.
    """
    role = validate_role_exists(db=db, role_id=role_id)

    ids_invalidos = [
        pid for pid in permission_ids
        if db.query(Permission.id).filter(Permission.id == pid).first() is None
    ]
    if ids_invalidos:
        raise HTTPException(
            status_code=400,
            detail=f"Permissões inexistentes: {ids_invalidos}.",
        )

    vinculos_atuais = (
        db.query(RolePermission)
        .options(joinedload(RolePermission.permission))
        .filter(RolePermission.role_id == role_id)
        .all()
    )
    ids_atuais = {rp.permission_id for rp in vinculos_atuais}
    ids_desejados = set(permission_ids)

    ids_para_remover = ids_atuais - ids_desejados
    ids_para_adicionar = ids_desejados - ids_atuais

    if not ids_para_remover and not ids_para_adicionar:
        return vinculos_atuais

    try:
        if ids_para_remover:
            db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id.in_(ids_para_remover),
            ).delete(synchronize_session=False)

        for permission_id in ids_para_adicionar:
            db.add(RolePermission(role_id=role_id, permission_id=permission_id))

        db.flush()

        create_audit_log(
            db=db,
            user_id=current_user.id,
            clinic_id=current_user.clinic_id,
            action=AuditAction.UPDATE,
            entity=AuditEntity.ROLE_PERMISSION,
            entity_id=role_id,
            description=f"Permissões do perfil '{role.name}' sincronizadas.",
            old_data={"permission_ids": sorted(ids_atuais)},
            new_data={"permission_ids": sorted(ids_desejados)},
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return (
        db.query(RolePermission)
        .options(joinedload(RolePermission.role), joinedload(RolePermission.permission))
        .filter(RolePermission.role_id == role_id)
        .all()
    )
    