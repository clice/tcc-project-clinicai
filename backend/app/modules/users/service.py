"""
Service do módulo de usuários.
"""

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.common.constants import AuditAction, AuditEntity, RoleName, StatusName, StatusScope
from app.common.services import (
    apply_update_data,
    is_admin_master,
    is_clinic_manager,
    model_dump_update,
    normalize_update_data,
)
from app.core.security import get_password_hash, verify_password
from app.modules.auth.service import create_user_tokens
from app.modules.clinics.model import Clinic
from app.modules.patients.model import Patient
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User
from app.modules.users.schema import (
    UserAdminUpdate,
    UserCreate,
    UserPasswordUpdate,
    UserSelfUpdate,
)
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
    """Garante unicidade de e-mail sem diferenciar maiúsculas/minúsculas."""

    normalized_email = email.strip().lower()
    query = db.query(User).filter(func.lower(User.email) == normalized_email)

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



def check_crm_duplicate(
    db: Session,
    crm_number: str | None,
    crm_uf: str | None,
    ignore_user_id: int | None = None,
) -> None:
    """Garante unicidade da inscrição médica dentro da mesma UF."""

    if crm_number is None or crm_uf is None:
        return

    query = db.query(User).filter(
        User.crm_number == crm_number,
        User.crm_uf == crm_uf,
    )

    if ignore_user_id is not None:
        query = query.filter(User.id != ignore_user_id)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="CRM já cadastrado nesta UF.",
        )


def validate_role_crm_rules(
    role: Role,
    crm_number: str | None,
    crm_uf: str | None,
) -> None:
    """Exige CRM completo somente para usuários médicos."""

    is_doctor = role.name == RoleName.DOCTOR.value

    if is_doctor and (crm_number is None or crm_uf is None):
        raise HTTPException(
            status_code=400,
            detail="CRM e UF do CRM são obrigatórios para médicos.",
        )

    if not is_doctor and (crm_number is not None or crm_uf is not None):
        raise HTTPException(
            status_code=400,
            detail="CRM deve ser informado somente para usuários médicos.",
        )


def validate_current_user_can_access_user(
    *,
    current_user: User,
    target_user: User,
    allow_self: bool = False,
) -> None:
    """Autoriza acesso administrativo ao usuário-alvo.

    O administrador master pode acessar qualquer usuário. O gestor da
    clínica pode acessar somente médicos vinculados à própria clínica.
    """

    if allow_self and current_user.id == target_user.id:
        return

    if is_admin_master(current_user):
        return

    if not is_clinic_manager(current_user):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para acessar este usuário.",
        )

    if current_user.clinic_id is None:
        raise HTTPException(
            status_code=403,
            detail="Gestor não está vinculado a uma clínica.",
        )

    target_role_name = (
        target_user.role.name
        if target_user.role
        else None
    )
    if (
        target_role_name != RoleName.DOCTOR.value
        or target_user.clinic_id != current_user.clinic_id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "O gestor só pode acessar médicos da própria clínica."
            ),
        )


def validate_current_user_can_manage_user_data(
    *,
    current_user: User,
    role: Role,
    clinic_id: int | None,
) -> None:
    """Valida o papel e a clínica atribuídos pelo usuário autenticado."""

    if is_admin_master(current_user):
        return

    if not is_clinic_manager(current_user):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para gerenciar usuários.",
        )

    if current_user.clinic_id is None:
        raise HTTPException(
            status_code=403,
            detail="Gestor não está vinculado a uma clínica.",
        )

    if role.name != RoleName.DOCTOR.value:
        raise HTTPException(
            status_code=403,
            detail="O gestor só pode criar ou alterar usuários médicos.",
        )

    if clinic_id != current_user.clinic_id:
        raise HTTPException(
            status_code=403,
            detail=(
                "O gestor só pode gerenciar médicos da própria clínica."
            ),
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


def validate_user_role_clinic_rules(
    db: Session,
    role_id: int,
    clinic_id: int | None,
) -> Role:
    """Valida no backend a invariável entre role e vínculo de clínica."""

    role = get_role_by_id(db, role_id)
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


def ensure_doctor_has_no_active_patients(
    db: Session,
    user: User,
    *,
    changing_role_or_clinic: bool = False,
    inactivating: bool = False,
) -> None:
    """Impede deixar pacientes ativos sem médico responsável válido."""

    if not user.role or user.role.name != RoleName.DOCTOR.value:
        return

    if not changing_role_or_clinic and not inactivating:
        return

    active_patient = (
        db.query(Patient.id)
        .join(Status, Patient.status_id == Status.id)
        .filter(
            Patient.doctor_id == user.id,
            Status.name == StatusName.ACTIVE.value,
            Status.applies_to == StatusScope.PATIENT.value,
        )
        .first()
    )

    if active_patient:
        raise HTTPException(
            status_code=409,
            detail=(
                "O médico possui pacientes ativos. Reatribua ou inative esses "
                "pacientes antes de alterar sua role, clínica ou status."
            ),
        )


def validate_user_business_rules(
    db: Session,
    role_id: int,
    clinic_id: int | None,
) -> Role:
    """Valida a invariável entre perfil de acesso e clínica na criação."""

    return validate_user_role_clinic_rules(db, role_id, clinic_id)


def count_active_admin_masters(db: Session) -> int:
    """Conta administradores master ativos."""

    return (
        db.query(User)
        .join(Role, User.role_id == Role.id)
        .join(Status, User.status_id == Status.id)
        .filter(
            Role.name == RoleName.ADMIN_MASTER.value,
            Status.name == StatusName.ACTIVE.value,
            Status.applies_to == StatusScope.USER.value,
        )
        .count()
    )


def ensure_last_active_admin_is_preserved(
    db: Session,
    user: User,
    *,
    next_role: Role | None = None,
    inactivating: bool = False,
) -> None:
    """Impede inativação ou rebaixamento do último administrador ativo."""

    is_active_admin = (
        user.role is not None
        and user.role.name == RoleName.ADMIN_MASTER.value
        and user.status is not None
        and user.status.name == StatusName.ACTIVE.value
    )
    if not is_active_admin:
        return

    removes_admin_access = inactivating or (
        next_role is not None and next_role.name != RoleName.ADMIN_MASTER.value
    )
    if removes_admin_access and count_active_admin_masters(db) <= 1:
        raise HTTPException(
            status_code=400,
            detail="Não é permitido remover ou inativar o último administrador master ativo.",
        )


def build_user_response(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "phone": user.phone,
        "crm_number": user.crm_number,
        "crm_uf": user.crm_uf,
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
    *,
    allow_self: bool = False,
) -> dict:
    user = get_user_by_id(db, user_id)

    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
        allow_self=allow_self,
    )

    return build_user_response(user)


# ========================================
# MAIN METHODS
# ========================================


def get_doctor_management_options(
    db: Session,
    current_user: User,
) -> dict:
    """Retorna somente os catálogos necessários ao gestor de clínica."""

    if not is_clinic_manager(current_user):
        raise HTTPException(
            status_code=403,
            detail="Opções exclusivas do gestor da clínica.",
        )

    clinic = get_active_clinic_or_none(
        db,
        current_user.clinic_id,
    )
    if clinic is None:
        raise HTTPException(
            status_code=403,
            detail="Gestor não está vinculado a uma clínica ativa.",
        )

    doctor_role = (
        db.query(Role)
        .filter(Role.name == RoleName.DOCTOR.value)
        .first()
    )
    if doctor_role is None:
        raise HTTPException(
            status_code=500,
            detail="Perfil médico não configurado.",
        )

    return {
        "role": {
            "id": doctor_role.id,
            "name": doctor_role.name,
            "display_name": doctor_role.display_name,
        },
        "clinic": {
            "id": clinic.id,
            "name": clinic.name,
            "status_name": StatusName.ACTIVE.value,
        },
    }


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
    if not (
        is_admin_master(current_user)
        or is_clinic_manager(current_user)
    ):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para cadastrar usuários.",
        )

    email = str(payload.email).strip().lower()

    check_email_duplicate(db, email)
    check_cpf_duplicate(db, payload.cpf)

    role = validate_user_business_rules(
        db=db,
        role_id=payload.role_id,
        clinic_id=payload.clinic_id,
    )
    validate_current_user_can_manage_user_data(
        current_user=current_user,
        role=role,
        clinic_id=payload.clinic_id,
    )

    validate_role_crm_rules(
        role=role,
        crm_number=payload.crm_number,
        crm_uf=payload.crm_uf,
    )
    check_crm_duplicate(
        db=db,
        crm_number=payload.crm_number,
        crm_uf=payload.crm_uf,
    )

    active_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.ACTIVE.value,
        applies_to=StatusScope.USER.value,
    )

    user = User(
        name=payload.name,
        email=email,
        cpf=payload.cpf,
        phone=payload.phone,
        crm_number=payload.crm_number,
        crm_uf=payload.crm_uf,
        role_id=payload.role_id,
        status_id=active_status.id,
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
            "crm_number": user.crm_number,
            "crm_uf": user.crm_uf,
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

    if is_admin_master(current_user):
        if clinic_id is not None:
            query = query.filter(User.clinic_id == clinic_id)
    elif is_clinic_manager(current_user):
        if current_user.clinic_id is None:
            raise HTTPException(
                status_code=403,
                detail="Gestor não está vinculado a uma clínica.",
            )

        if clinic_id is not None and clinic_id != current_user.clinic_id:
            raise HTTPException(
                status_code=403,
                detail=(
                    "O gestor não pode listar médicos de outra clínica."
                ),
            )

        if (
            role is not None
            and role.strip().lower() != RoleName.DOCTOR.value
        ):
            raise HTTPException(
                status_code=403,
                detail="O gestor só pode listar usuários médicos.",
            )

        query = query.filter(
            User.clinic_id == current_user.clinic_id,
            Role.name == RoleName.DOCTOR.value,
        )
    elif (
        current_user.role is not None
        and current_user.role.name == RoleName.DOCTOR.value
    ):
        if current_user.clinic_id is None:
            raise HTTPException(
                status_code=403,
                detail="Médico não está vinculado a uma clínica.",
            )

        if clinic_id != current_user.clinic_id:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Você não tem permissão para listar médicos "
                    "de outra clínica."
                ),
            )

        if (
            role is None
            or role.strip().lower() != RoleName.DOCTOR.value
        ):
            raise HTTPException(
                status_code=403,
                detail="Consulta permitida apenas para o seletor de médicos.",
            )

        query = query.filter(
            User.clinic_id == current_user.clinic_id,
            Role.name == RoleName.DOCTOR.value,
        )
    else:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para listar usuários.",
        )

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
    payload: UserAdminUpdate,
    current_user: User,
) -> dict:
    """Atualiza dados administráveis, role e clínica de um usuário."""

    if not (
        is_admin_master(current_user)
        or is_clinic_manager(current_user)
    ):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para gerenciar usuários.",
        )

    user = get_user_by_id(db, user_id)
    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    update_data = normalize_update_data(model_dump_update(payload))
    if not update_data:
        return build_user_response(user)

    if current_user.id == user_id and any(
        field in update_data for field in ("role_id", "clinic_id")
    ):
        raise HTTPException(
            status_code=403,
            detail="O administrador não pode alterar a própria role ou clínica.",
        )

    new_name = update_data.get("name", user.name)
    new_email = update_data.get("email", user.email)
    new_cpf = update_data.get("cpf", user.cpf)
    new_crm_number = update_data.get("crm_number", user.crm_number)
    new_crm_uf = update_data.get("crm_uf", user.crm_uf)
    new_role_id = update_data.get("role_id", user.role_id)
    new_clinic_id = update_data.get("clinic_id", user.clinic_id)

    if new_name is None:
        raise HTTPException(status_code=400, detail="Nome completo é obrigatório.")
    if new_email is None:
        raise HTTPException(status_code=400, detail="E-mail é obrigatório.")
    normalized_email = str(new_email).strip().lower()
    check_email_duplicate(db, normalized_email, ignore_user_id=user_id)

    if new_cpf is None:
        raise HTTPException(status_code=400, detail="CPF é obrigatório.")
    check_cpf_duplicate(db, new_cpf, ignore_user_id=user_id)

    if new_role_id is None:
        raise HTTPException(status_code=400, detail="Perfil de acesso é obrigatório.")

    ensure_doctor_has_no_active_patients(
        db,
        user,
        changing_role_or_clinic=(
            new_role_id != user.role_id or new_clinic_id != user.clinic_id
        ),
    )
    next_role = validate_user_role_clinic_rules(
        db,
        new_role_id,
        new_clinic_id,
    )
    validate_current_user_can_manage_user_data(
        current_user=current_user,
        role=next_role,
        clinic_id=new_clinic_id,
    )
    validate_role_crm_rules(
        role=next_role,
        crm_number=new_crm_number,
        crm_uf=new_crm_uf,
    )
    check_crm_duplicate(
        db=db,
        crm_number=new_crm_number,
        crm_uf=new_crm_uf,
        ignore_user_id=user_id,
    )
    ensure_last_active_admin_is_preserved(
        db,
        user,
        next_role=next_role,
    )

    if "email" in update_data:
        update_data["email"] = normalized_email

    old_data = {
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "phone": user.phone,
        "crm_number": user.crm_number,
        "crm_uf": user.crm_uf,
        "role_id": user.role_id,
        "clinic_id": user.clinic_id,
    }

    security_context_changed = (
        new_role_id != user.role_id or new_clinic_id != user.clinic_id
    )
    apply_update_data(user, update_data)
    if security_context_changed:
        user.token_version += 1

    audit_new_data = dict(update_data)
    if security_context_changed:
        audit_new_data.update(
            {
                "security_context_changed": True,
                "token_version": user.token_version,
            }
        )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.USER,
        entity_id=user.id,
        description="Usuário atualizado.",
        old_data=old_data,
        new_data=audit_new_data,
    )

    db.commit()
    db.refresh(user)
    return build_user_response(get_user_by_id(db=db, user_id=user.id))


def update_current_user_profile(
    db: Session,
    payload: UserSelfUpdate,
    current_user: User,
) -> dict:
    """Atualiza somente os dados cadastrais do usuário autenticado."""

    user = get_user_by_id(db, current_user.id)
    update_data = normalize_update_data(model_dump_update(payload))
    if not update_data:
        return build_user_response(user)

    if "name" in update_data and update_data["name"] is None:
        raise HTTPException(status_code=400, detail="Nome completo é obrigatório.")

    if "email" in update_data:
        if update_data["email"] is None:
            raise HTTPException(status_code=400, detail="E-mail é obrigatório.")
        update_data["email"] = str(update_data["email"]).strip().lower()
        check_email_duplicate(db, update_data["email"], ignore_user_id=user.id)

    if "cpf" in update_data:
        if update_data["cpf"] is None:
            raise HTTPException(status_code=400, detail="CPF é obrigatório.")
        check_cpf_duplicate(db, update_data["cpf"], ignore_user_id=user.id)

    if "crm_number" in update_data or "crm_uf" in update_data:
        new_crm_number = update_data.get("crm_number", user.crm_number)
        new_crm_uf = update_data.get("crm_uf", user.crm_uf)

        validate_role_crm_rules(
            role=user.role,
            crm_number=new_crm_number,
            crm_uf=new_crm_uf,
        )
        check_crm_duplicate(
            db=db,
            crm_number=new_crm_number,
            crm_uf=new_crm_uf,
            ignore_user_id=user.id,
        )

    old_data = {
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "phone": user.phone,
        "crm_number": user.crm_number,
        "crm_uf": user.crm_uf,
    }
    apply_update_data(user, update_data)

    create_audit_log(
        db=db,
        user_id=user.id,
        clinic_id=user.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.USER,
        entity_id=user.id,
        description="Dados cadastrais do próprio usuário atualizados.",
        old_data=old_data,
        new_data=update_data,
    )

    db.commit()
    db.refresh(user)
    return build_user_response(get_user_by_id(db=db, user_id=user.id))


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

    if not (
        is_admin_master(current_user)
        or is_clinic_manager(current_user)
    ):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para redefinir esta senha.",
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
    """Inativa usuário, preservando ao menos um administrador ativo."""

    if not (
        is_admin_master(current_user)
        or is_clinic_manager(current_user)
    ):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para inativar usuários.",
        )

    user = get_user_by_id(db, user_id)
    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    if user.status and user.status.name == StatusName.INACTIVE.value:
        return build_user_response(user)

    ensure_last_active_admin_is_preserved(db, user, inactivating=True)
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Você não pode inativar o próprio usuário.")

    ensure_doctor_has_no_active_patients(db, user, inactivating=True)
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
    return build_user_response(get_user_by_id(db=db, user_id=user.id))


def activate_user(
    db: Session,
    user_id: int,
    current_user: User,
) -> dict:
    """Ativa usuário somente quando sua invariável role/clínica é válida."""

    if not (
        is_admin_master(current_user)
        or is_clinic_manager(current_user)
    ):
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para ativar usuários.",
        )

    user = get_user_by_id(db, user_id)
    validate_current_user_can_access_user(
        current_user=current_user,
        target_user=user,
    )

    if user.status and user.status.name == StatusName.ACTIVE.value:
        return build_user_response(user)

    validate_user_role_clinic_rules(db, user.role_id, user.clinic_id)
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
    return build_user_response(get_user_by_id(db=db, user_id=user.id))
