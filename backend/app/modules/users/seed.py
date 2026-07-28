"""Administrador inicial e usuários fictícios da demonstração."""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.modules.clinics.model import Clinic
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


ACADEMIC_DEMO_PASSWORD = "clinicai123"

ACADEMIC_DEMO_EMAILS = (
    "dr.joao@clinicai.com",
    "gestor.clinicai@clinicai.com",
    "dr.lucas@clinicai.com",
    "dr.marcos@hospitalcariri.com",
    "gestor.hospital@hospitalcariri.com",
    "dra.helena@cariri.com",
    "gestor.centro@cariri.com",
    "dr.renato@clinicai.com",
    "dra.paula@clinicai.com",
    "gestor.inativo@hospitalcariri.com",
    "gestor.inativo@cariri.com",
    "admin.inativo@clinicai.com",
)


def _build_demo_cpf(base: int) -> str:
    """Gera CPF fictício válido para usuários acadêmicos."""

    digits = f"{base:09d}"

    for initial_weight in (10, 11):
        total = sum(
            int(character) * (initial_weight - index)
            for index, character in enumerate(digits)
        )
        remainder = (total * 10) % 11
        digits += str(0 if remainder == 10 else remainder)

    return digits


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
    crm_number: str | None = None,
    crm_uf: str | None = None,
    reconcile: bool = False,
) -> User:
    user_by_email = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not reconcile:
        if user_by_email:
            return user_by_email
        user = None
    else:
        user_by_cpf = (
            db.query(User)
            .filter(User.cpf == cpf)
            .first()
        )
        if (
            user_by_email is not None
            and user_by_cpf is not None
            and user_by_email.id != user_by_cpf.id
        ):
            raise RuntimeError(
                "Colisão da massa acadêmica: e-mail e CPF pertencem "
                "a usuários diferentes."
            )
        if user_by_email is not None and user_by_cpf is None:
            raise RuntimeError(
                "Colisão da massa acadêmica: o e-mail reservado "
                f"{email!r} pertence a outro CPF."
            )
        user = user_by_cpf

    if user is None:
        user = User(
            email=email,
            cpf=cpf,
            password_hash=get_password_hash(password),
        )
        db.add(user)

    user.name = name
    user.email = email
    user.cpf = cpf
    user.phone = phone
    user.crm_number = crm_number
    user.crm_uf = crm_uf
    user.role_id = role_id
    user.status_id = status_id
    user.clinic_id = clinic_id
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
    """Cria o único Administrador Master do bootstrap."""

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
    """Cria usuários ativos e inativos da demonstração acadêmica."""

    definitions = {
        "doctor_primary": {
            "name": "Dr. João Silva",
            "email": "dr.joao@clinicai.com",
            "cpf": "11144477735",
            "role": "doctor",
            "clinic": "clinic_primary",
            "crm_number": "12345",
            "crm_uf": "CE",
        },
        "doctor_primary_secondary": {
            "name": "Dr. Lucas Andrade",
            "email": "dr.lucas@clinicai.com",
            "cpf": _build_demo_cpf(810_000_001),
            "role": "doctor",
            "clinic": "clinic_primary",
            "crm_number": "45678",
            "crm_uf": "CE",
        },
        "manager_primary": {
            "name": "Gestor ClinicAI Endoscopia Especializada",
            "email": "gestor.clinicai@clinicai.com",
            "cpf": "15350946056",
            "role": "clinic_manager",
            "clinic": "clinic_primary",
        },
        "doctor_large": {
            "name": "Dr. Marcos Lima",
            "email": "dr.marcos@hospitalcariri.com",
            "cpf": "31415926590",
            "role": "doctor",
            "clinic": "clinic_large",
            "crm_number": "23456",
            "crm_uf": "CE",
        },
        "manager_large": {
            "name": "Gestor Hospital Cariri",
            "email": "gestor.hospital@hospitalcariri.com",
            "cpf": "27182818205",
            "role": "clinic_manager",
            "clinic": "clinic_large",
        },
        "doctor_specialized": {
            "name": "Dra. Helena Costa",
            "email": "dra.helena@cariri.com",
            "cpf": "16180339805",
            "role": "doctor",
            "clinic": "clinic_specialized",
            "crm_number": "34567",
            "crm_uf": "CE",
        },
        "manager_specialized": {
            "name": "Gestão Centro Endoscópico",
            "email": "gestor.centro@cariri.com",
            "cpf": "14142135651",
            "role": "clinic_manager",
            "clinic": "clinic_specialized",
        },
        "doctor_inactive_archive": {
            "name": "Dr. Renato Moura",
            "email": "dr.renato@clinicai.com",
            "cpf": _build_demo_cpf(810_000_002),
            "role": "doctor",
            "clinic": "clinic_inactive",
            "status": "user_inactive",
            "crm_number": "56789",
            "crm_uf": "CE",
        },
        "doctor_inactive_primary": {
            "name": "Dra. Paula Freire",
            "email": "dra.paula@clinicai.com",
            "cpf": _build_demo_cpf(810_000_003),
            "role": "doctor",
            "clinic": "clinic_primary",
            "status": "user_inactive",
            "crm_number": "67890",
            "crm_uf": "CE",
        },
        "manager_inactive_large": {
            "name": "Gestor Inativo Hospital Cariri",
            "email": "gestor.inativo@hospitalcariri.com",
            "cpf": _build_demo_cpf(810_000_004),
            "role": "clinic_manager",
            "clinic": "clinic_large",
            "status": "user_inactive",
        },
        "manager_inactive_specialized": {
            "name": "Gestor Inativo Centro Endoscópico",
            "email": "gestor.inativo@cariri.com",
            "cpf": _build_demo_cpf(810_000_005),
            "role": "clinic_manager",
            "clinic": "clinic_specialized",
            "status": "user_inactive",
        },
        "admin_master_inactive": {
            "name": "Administrador Master Inativo",
            "email": "admin.inativo@clinicai.com",
            "cpf": _build_demo_cpf(810_000_006),
            "role": "admin_master",
            "clinic": None,
            "status": "user_inactive",
        },
    }

    users = {
        "admin_master": admin_master,
    }

    for key, definition in definitions.items():
        clinic_key = definition.get("clinic")
        clinic = clinics.get(clinic_key) if clinic_key else None

        users[key] = get_or_create_user(
            db=db,
            name=definition["name"],
            email=definition["email"],
            password=ACADEMIC_DEMO_PASSWORD,
            cpf=definition["cpf"],
            role_id=roles[
                definition["role"]
            ].id,
            status_id=statuses[
                definition.get("status", "user_active")
            ].id,
            clinic_id=clinic.id if clinic else None,
            crm_number=definition.get("crm_number"),
            crm_uf=definition.get("crm_uf"),
            reconcile=True,
        )

    return users
