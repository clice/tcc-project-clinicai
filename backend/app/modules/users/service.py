"""
Service do módulo de usuários.
"""

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.common.constants import AuditAction, AuditEntity, RoleName, StatusName, StatusScope
from app.common.services import (
    apply_update_data,
    is_admin_master, 
    model_dump_update,
    normalize_update_data,
)
from app.core.security import get_password_hash, verify_password
from app.modules.auth.service import create_user_tokens
from app.modules.clinics.model import Clinic
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User
from app.modules.users.schema import UserCreate, UserPasswordUpdate, UserUpdate
from app.modules.audit_logs.service import create_audit_log
from app.modules.roles.service import get_role_by_id
from app.modules.statuses.service import (
    get_status_by_id_and_applies_to,
    get_status_by_name_and_applies_to,
)


def check_email_duplicate(
    db: Session,
    email: str,
    ignore_user_id: int | None = None,
) -> None:
    query = db.query(User).filter(User.email == email)

    if ignore_user_id is not None:
        query = query.filter(User.id != ignore_user_id)

    if query.first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")


def check_cpf_duplicate(
    db: Session,
    cpf: str,
    ignore_user_id: int | None = None,
) -> None:
    query = db.query(User).filter(User.cpf == cpf)

    if ignore_user_id is not None:
        query = query.filter(User.id != ignore_user_id)

    if query.first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado.")


def validate_current_user_can_access_user(
    *,
    current_user: User,
    target_user: User,
) -> None:
    if is_admin_master(current_user):
        return

    if current_user.clinic_id is None:
        raise HTTPException(
            status_code=403,
            detail="Usuário autenticado não está vinculado a uma clínica.",
        )

    if target_user.clinic_id != current_user.clinic_id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para acessar este usuário.",
        )


def validate_current_user_can_manage_user_data(
    *,
    current_user: User,
    role: Role,
    clinic_id: int | None,
) -> None:
    if is_admin_master(current_user):
        return

    if role.name == RoleName.ADMIN_MASTER.value:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para criar ou alterar administrador master.",
        )

    if current_user.clinic_id is None:
        raise HTTPException(
            status_code=403,
            detail="Usuário autenticado não está vinculado a uma clínica.",
        )

    if clinic_id != current_user.clinic_id:
        raise HTTPException(
            status_code=403,
            detail="Você só pode gerenciar usuários da sua própria clínica.",
        )


def get_active_clinic_or_none(db: Session, clinic_id: int | None) -> Clinic | None:
    if clinic_id is None:
        return None

    clinic = (
        db.query(Clinic)
        .join(Status, Clinic.status_id == Status.id)
        .filter(
            Clinic.id == clinic_id,
            Status.name == StatusName.ACTIVE.value,
            Status.applies_to == StatusScope.CLINIC.value,
        )
        .first()
    )

    if not clinic:
        raise HTTPException(
            status_code=400,
            detail="Clínica não encontrada ou não está ativa.",
        )

    return clinic


def validate_user_business_rules(
    db: Session,
    role_id: int,
    status_id: int,
    clinic_id: int | None,
) -> Role:
    role = get_role_by_id(db, role_id)

    get_status_by_id_and_applies_to(
        db=db,
        status_id=status_id,
        applies_to=StatusScope.USER.value,
    )

    role_name = role.name.strip().lower()

    if role_name == RoleName.ADMIN_MASTER.value:
        if clinic_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Administrador master não deve estar vinculado a uma clínica.",
            )
        return role

    if clinic_id is None:
        raise HTTPException(
            status_code=400,
            detail="Usuários que não são admin_master devem estar vinculados a uma clínica.",
        )

    get_active_clinic_or_none(db, clinic_id)

    return role


def build_user_response(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "phone": user.phone,
        "role_id": user.role_id,
        "status_id": user.status_id,
        "clinic_id": user.clinic_id,
        "last_access_at": user.last_access_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "role_name": user.role.name if user.role else None,
        "role_display_name": user.role.display_name if user.role else None,
        "status_name": user.status.name if user.status else None,
        "status_display_name": user.status.display_name if user.status else None,
        "clinic_name": user.clinic.name if user.clinic else None,
    }


def get_user_response(
    db: Session,
    user_id: int,
    current_user: User,
) -> dict:
    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    return build_user_response(user)


# ========================================
# MAIN METHODS
# ========================================


def get_user_by_id(db: Session, user_id: int) -> User:
    user = (
        db.query(User)
        .options(
            joinedload(User.role),
            joinedload(User.status),
            joinedload(User.clinic),
        )
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    return user


def create_user(
    db: Session,
    payload: UserCreate,
    current_user: User,
) -> dict:
    email = payload.email if isinstance(payload.email, str) else str(payload.email)

    check_email_duplicate(db, email)
    check_cpf_duplicate(db, payload.cpf)

    role = validate_user_business_rules(
        db=db,
        role_id=payload.role_id,
        status_id=payload.status_id,
        clinic_id=payload.clinic_id,
    )

    validate_current_user_can_manage_user_data(
        current_user=current_user,
        role=role,
        clinic_id=payload.clinic_id,
    )

    user = User(
        name=payload.name,
        email=email,
        cpf=payload.cpf,
        phone=payload.phone,
        role_id=payload.role_id,
        status_id=payload.status_id,
        clinic_id=payload.clinic_id,
        password_hash=get_password_hash(payload.password),
    )

    db.add(user)
    db.flush()
    
    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.CREATE,
        entity=AuditEntity.USER,
        entity_id=user.id,
        description="Usuário cadastrado.",
        new_data={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "cpf": user.cpf,
            "phone": user.phone,
            "role_id": user.role_id,
            "status_id": user.status_id,
            "clinic_id": user.clinic_id,
        },
    )
    
    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_response(user)


def list_users(
    db: Session,
    current_user: User,
    search: str | None = None,
    clinic_id: int | None = None,
    role: str | None = None,
    status: str | None = None,
) -> list[dict]:
    query = (
        db.query(User)
        .options(
            joinedload(User.role),
            joinedload(User.status),
            joinedload(User.clinic),
        )
        .join(Role, User.role_id == Role.id)
        .join(Status, User.status_id == Status.id)
    )

    if not is_admin_master(current_user):
        if current_user.clinic_id is None:
            raise HTTPException(
                status_code=403,
                detail="Usuário autenticado não está vinculado a uma clínica.",
            )

        query = query.filter(User.clinic_id == current_user.clinic_id)

        if clinic_id is not None and clinic_id != current_user.clinic_id:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para listar usuários de outra clínica.",
            )

    elif clinic_id is not None:
        query = query.filter(User.clinic_id == clinic_id)

    if search:
        search_value = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                User.name.ilike(search_value),
                User.email.ilike(search_value),
                User.cpf.ilike(search_value),
            )
        )

    if role:
        query = query.filter(Role.name == role.strip().lower())

    if status:
        query = query.filter(
            Status.name == status.strip().lower(),
            Status.applies_to == StatusScope.USER.value,
        )

    users = query.order_by(User.name.asc()).all()

    return [build_user_response(user) for user in users]


def update_user(
    db: Session,
    user_id: int,
    payload: UserUpdate,
    current_user: User,
) -> dict:
    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    update_data = model_dump_update(payload)
    update_data = normalize_update_data(update_data)

    if not update_data:
        return build_user_response(user)

    # Autoedição de perfil (rota /users/me): ninguém — nem o próprio
    # admin_master — pode alterar perfil de acesso, status ou clínica
    # da própria conta por essa rota. Essas mudanças só acontecem via
    # /users/{id} (gestão de outros usuários), que já exige users:update
    # (exclusivo de admin_master).
    is_self_edit = current_user.id == user_id

    if is_self_edit and any(
        field in update_data for field in ("role_id", "status_id", "clinic_id")
    ):
        raise HTTPException(
            status_code=403,
            detail="Alteração de perfil de acesso, status ou clínica não é permitida na autoedição de perfil.",
        )

    new_email = update_data.get("email", user.email)
    new_cpf = update_data.get("cpf", user.cpf)
    new_role_id = update_data.get("role_id", user.role_id)
    new_status_id = update_data.get("status_id", user.status_id)
    new_clinic_id = update_data.get("clinic_id", user.clinic_id)

    if new_email is not None:
        check_email_duplicate(db, str(new_email), ignore_user_id=user_id)

    if new_cpf is None:
        raise HTTPException(
            status_code=400,
            detail="CPF é obrigatório.",
        )

    check_cpf_duplicate(db, new_cpf, ignore_user_id=user_id)

    role = validate_user_business_rules(
        db=db,
        role_id=new_role_id,
        status_id=new_status_id,
        clinic_id=new_clinic_id,
    )

    validate_current_user_can_manage_user_data(
        current_user=current_user,
        role=role,
        clinic_id=new_clinic_id,
    )

    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = str(update_data["email"])

    old_data = {
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "phone": user.phone,
        "role_id": user.role_id,
        "status_id": user.status_id,
        "clinic_id": user.clinic_id,
    }
    
    apply_update_data(user, update_data)

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.USER,
        entity_id=user.id,
        description="Usuário atualizado.",
        old_data=old_data,
        new_data=update_data,
    )
    
    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_response(user)


def update_user_password(
    db: Session,
    user_id: int,
    payload: UserPasswordUpdate,
    current_user: User,
) -> dict:
    """Permite ao administrador resetar a senha de outro usuário."""

    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    if not is_admin_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Apenas o administrador master pode redefinir senhas de outros usuários.",
        )

    if current_user.id == user.id:
        raise HTTPException(
            status_code=400,
            detail="Para alterar a própria senha, utilize a rota /users/me/password.",
        )

    user.password_hash = get_password_hash(payload.password)
    user.token_version += 1

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.UPDATE_PASSWORD,
        entity=AuditEntity.USER,
        entity_id=user.id,
        description="Senha do usuário redefinida pelo administrador.",
        new_data={
            "password_updated": True,
            "token_version": user.token_version,
        },
    )

    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_response(user)


def change_current_user_password(
    db: Session,
    payload: UserPasswordUpdate,
    current_user: User,
) -> dict[str, str]:
    """Troca a senha do usuário autenticado e preserva somente esta sessão."""

    user = get_user_by_id(db, current_user.id)

    if not payload.current_password:
        raise HTTPException(
            status_code=400,
            detail="Informe a senha atual para definir uma nova senha.",
        )

    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Senha atual incorreta.",
        )

    if verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="A nova senha deve ser diferente da senha atual.",
        )

    user.password_hash = get_password_hash(payload.password)

    # Encerra tokens emitidos antes da troca. Um novo par é devolvido ao
    # navegador que comprovou a senha atual, preservando apenas esta sessão.
    user.token_version += 1

    create_audit_log(
        db=db,
        user_id=user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.UPDATE_PASSWORD,
        entity=AuditEntity.USER,
        entity_id=user.id,
        description="Senha do próprio usuário atualizada.",
        new_data={
            "password_updated": True,
            "token_version": user.token_version,
        },
    )

    db.commit()
    db.refresh(user)

    return create_user_tokens(user)

def inactivate_user(
    db: Session,
    user_id: int,
    current_user: User,
) -> dict:
    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Você não pode inativar o próprio usuário.",
        )

    if user.role and user.role.name == RoleName.ADMIN_MASTER.value and not is_admin_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para inativar administrador master.",
        )

    inactive_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.INACTIVE.value,
        applies_to=StatusScope.USER.value,
    )

    old_data = {
        "status_id": user.status_id,
        "status_name": user.status.name if user.status else None,
    }

    user.status_id = inactive_status.id
    user.token_version += 1

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.CHANGE_STATUS_INACTIVATE,
        entity=AuditEntity.USER,
        entity_id=user.id,
        description="Usuário inativado.",
        old_data=old_data,
        new_data={
            "status_id": inactive_status.id,
            "status_name": StatusName.INACTIVE.value,
            "token_version": user.token_version,
        },
    )

    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_response(user)


def activate_user(
    db: Session,
    user_id: int,
    current_user: User,
) -> dict:
    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    if user.role and user.role.name == RoleName.ADMIN_MASTER.value and not is_admin_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para ativar administrador master.",
        )

    active_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.ACTIVE.value,
        applies_to=StatusScope.USER.value,
    )

    old_data = {
        "status_id": user.status_id,
        "status_name": user.status.name if user.status else None,
    }

    user.status_id = active_status.id

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.CHANGE_STATUS_ACTIVATE,
        entity=AuditEntity.USER,
        entity_id=user.id,
        description="Usuário ativado.",
        old_data=old_data,
        new_data={
            "status_id": active_status.id,
            "status_name": StatusName.ACTIVE.value,
        },
    )

    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_response(user)
