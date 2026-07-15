"""Administrador inicial do bootstrap e usuários fictícios da demonstração."""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.modules.clinics.model import Clinic
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


# Credencial padronizada apenas para as contas adicionais da massa fictícia.
# O Administrador Master pertence ao bootstrap e usa as variáveis
# BOOTSTRAP_ADMIN_* da configuração.
ACADEMIC_DEMO_PASSWORD = "clinicai123"
ACADEMIC_DEMO_EMAILS = (
    "doctor@clinicai.com",
    "doctor2@clinicai.com",
    "staff@clinicai.com",
    "inactive@clinicai.com",
)


def get_or_create_user(
    db: Session,
    email: str,
    name: str,
    role_id: int,
    status_id: int,
    password: str,
    cpf: str,
    clinic_id: int | None = None,
    phone: str | None = None,
) -> User:
    user = db.query(User).filter(User.email == email).first()

    if user:
        return user

    user = User(
        name=name,
        email=email,
        cpf=cpf,
        phone=phone,
        role_id=role_id,
        status_id=status_id,
        clinic_id=clinic_id,
        password_hash=get_password_hash(password),
    )

    db.add(user)
    db.flush()
    db.refresh(user)

    return user




def seed_bootstrap_admin(
    db: Session,
    roles: dict[str, Role],
    statuses: dict[str, Status],
    *,
    name: str,
    email: str,
    cpf: str,
    password: str,
) -> User:
    """Cria o único usuário inicial do modo bootstrap.

    A busca é feita pelo e-mail configurado. Quando o usuário já existe, seus
    dados e sua senha são preservados para que reinícios não sobrescrevam
    alterações administrativas.
    """

    return get_or_create_user(
        db=db,
        name=name,
        email=email,
        password=password,
        cpf=cpf,
        role_id=roles["admin_master"].id,
        status_id=statuses["user_active"].id,
        clinic_id=None,
    )

def seed_users(
    db: Session,
    roles: dict[str, Role],
    statuses: dict[str, Status],
    clinics: dict[str, Clinic],
    *,
    admin_master: User,
) -> dict[str, User]:
    return {
        "admin_master": admin_master,
        "doctor_primary": get_or_create_user(
            db=db,
            name="Dr. João Silva",
            email="doctor@clinicai.com",
            password=ACADEMIC_DEMO_PASSWORD,
            cpf="11144477735",
            role_id=roles["doctor"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
        "doctor_secondary": get_or_create_user(
            db=db,
            name="Dra. Maria Souza",
            email="doctor2@clinicai.com",
            password=ACADEMIC_DEMO_PASSWORD,
            cpf="52998224725",
            role_id=roles["doctor"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_secondary"].id,
        ),
        "staff_primary": get_or_create_user(
            db=db,
            name="Recepção Clínica",
            email="staff@clinicai.com",
            password=ACADEMIC_DEMO_PASSWORD,
            cpf="15350946056",
            role_id=roles["clinic_staff"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
        "user_inactive": get_or_create_user(
            db=db,
            name="Usuário Inativo",
            email="inactive@clinicai.com",
            password=ACADEMIC_DEMO_PASSWORD,
            cpf="98765432100",
            role_id=roles["clinic_staff"].id,
            status_id=statuses["user_inactive"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
    }
