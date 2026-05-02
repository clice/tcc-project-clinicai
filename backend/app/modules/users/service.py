"""
Service do módulo de usuários.

Aqui ficam as regras de negócio e operações com o banco.
O router deve apenas receber a requisição e chamar essas funções.
"""

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_password_hash
from app.modules.clinics.model import Clinic
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.statuses.service import (
    get_status_by_id_and_applies_to,
    get_status_by_name_and_applies_to,
)
from app.modules.users.model import User
from app.modules.users.schema import UserCreate, UserPasswordUpdate, UserUpdate


def is_admin_master(user: User) -> bool:
    return bool(user.role and user.role.name == "admin_master")


def get_user_role_name(user: User) -> str | None:
    return user.role.name if user.role else None


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

    if role.name == "admin_master":
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


def get_user_by_id(db: Session, user_id: int) -> User:
    """
    Busca usuário pelo ID.

    Se não existir, retorna erro 404.
    """
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


def get_role_by_id(db: Session, role_id: int) -> Role:
    """
    Busca role existente.
    """
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(status_code=400, detail="Perfil de acesso não encontrado.")

    return role


def get_active_clinic_or_none(db: Session, clinic_id: int | None) -> Clinic | None:
    """
    Busca clínica ativa, quando clinic_id for informado.
    """
    if clinic_id is None:
        return None

    clinic = (
        db.query(Clinic)
        .join(Status, Clinic.status_id == Status.id)
        .filter(
            Clinic.id == clinic_id,
            Status.name == "active",
            Status.applies_to == "clinic",
        )
        .first()
    )

    if not clinic:
        raise HTTPException(
            status_code=400,
            detail="Clínica não encontrada ou não está ativa.",
        )

    return clinic


def check_email_duplicate(
    db: Session,
    email: str,
    ignore_user_id: int | None = None,
) -> None:
    """
    Verifica duplicidade de e-mail.
    """
    query = db.query(User).filter(User.email == email)

    if ignore_user_id is not None:
        query = query.filter(User.id != ignore_user_id)

    if query.first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")


def check_cpf_duplicate(
    db: Session,
    cpf: str | None,
    ignore_user_id: int | None = None,
) -> None:
    """
    Verifica duplicidade de CPF, quando CPF for informado.
    """
    if cpf is None:
        return

    query = db.query(User).filter(User.cpf == cpf)

    if ignore_user_id is not None:
        query = query.filter(User.id != ignore_user_id)

    if query.first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado.")


def validate_user_business_rules(
    db: Session,
    role_id: int,
    status_id: int,
    clinic_id: int | None,
) -> Role:
    """
    Valida regras de negócio do usuário.

    - role deve existir
    - status deve ser de user
    - admin_master pode ficar sem clínica
    - médico e funcionário precisam de clínica ativa
    """
    role = get_role_by_id(db, role_id)

    get_status_by_id_and_applies_to(
        db=db,
        status_id=status_id,
        applies_to="user",
    )

    role_name = role.name.strip().lower()

    if role_name == "admin_master":
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


def build_user_list_item(user: User) -> dict:
    """
    Monta resposta enriquecida para listagem e detalhe.

    Evita depender do frontend para resolver nomes de role, status e clínica.
    """
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
        "status_name": user.status.name if user.status else None,
        "status_display_name": user.status.display_name if user.status else None,
        "clinic_name": user.clinic.name if user.clinic else None,
    }


def create_user(
    db: Session,
    payload: UserCreate,
    current_user: User,
) -> dict:
    """
    Cria um novo usuário.
    """
    check_email_duplicate(db, payload.email)
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
        email=str(payload.email),
        cpf=payload.cpf,
        phone=payload.phone,
        role_id=payload.role_id,
        status_id=payload.status_id,
        clinic_id=payload.clinic_id,
        password_hash=get_password_hash(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_list_item(user)


def list_users(
    db: Session,
    current_user: User,
    search: str | None = None,
    clinic_id: int | None = None,
    role: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """
    Lista usuários com filtros opcionais.

    Filtros disponíveis:
    - search: busca por nome, e-mail ou CPF;
    - clinic_id: filtra usuários por clínica;
    - role: filtra pelo nome do perfil, ex: doctor;
    - status: filtra pelo nome do status, ex: active.

    Esse filtro é usado pelo módulo Patients para listar apenas
    médicos ativos da clínica selecionada.
    """
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
            Status.applies_to == "user",
        )

    users = query.order_by(User.name.asc()).all()

    return [build_user_list_item(user) for user in users]


def get_user_response(
    db: Session,
    user_id: int,
    current_user: User,
) -> dict:
    """
    Busca usuário por ID e devolve resposta enriquecida.
    """
    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    return build_user_list_item(user)


def update_user(
    db: Session,
    user_id: int,
    payload: UserUpdate,
    current_user: User,
) -> dict:
    """
    Atualiza parcialmente um usuário.
    """
    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return build_user_list_item(user)

    new_email = update_data.get("email", user.email)
    new_cpf = update_data.get("cpf", user.cpf)
    new_role_id = update_data.get("role_id", user.role_id)
    new_status_id = update_data.get("status_id", user.status_id)
    new_clinic_id = update_data.get("clinic_id", user.clinic_id)

    if new_email is not None:
        check_email_duplicate(db, str(new_email), ignore_user_id=user_id)

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

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_list_item(user)


def update_user_password(
    db: Session,
    user_id: int,
    payload: UserPasswordUpdate,
    current_user: User,
) -> dict:
    """
    Atualiza somente a senha do usuário.
    """
    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    if not is_admin_master(current_user) and current_user.id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para alterar a senha deste usuário.",
        )

    user.password_hash = get_password_hash(payload.password)

    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_list_item(user)


def inactivate_user(
    db: Session,
    user_id: int,
    current_user: User,
) -> dict:
    """
    Inativa usuário por status.

    Não faz delete físico.
    """
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

    if user.role and user.role.name == "admin_master" and not is_admin_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para inativar administrador master.",
        )

    inactive_status = get_status_by_name_and_applies_to(
        db=db,
        name="inactive",
        applies_to="user",
    )

    user.status_id = inactive_status.id

    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_list_item(user)


def activate_user(
    db: Session,
    user_id: int,
    current_user: User,
) -> dict:
    """
    Ativa usuário por status.
    """
    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    if user.role and user.role.name == "admin_master" and not is_admin_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para ativar administrador master.",
        )

    active_status = get_status_by_name_and_applies_to(
        db=db,
        name="active",
        applies_to="user",
    )

    user.status_id = active_status.id

    db.commit()
    db.refresh(user)

    user = get_user_by_id(db=db, user_id=user.id)

    return build_user_list_item(user)