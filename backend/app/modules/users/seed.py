"""Administrador inicial e usuários fictícios da demonstração."""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.modules.clinics.model import Clinic
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


ACADEMIC_DEMO_PASSWORD = "clinicai123"

ACADEMIC_DEMO_EMAILS = (
    "doctor@clinicai.com",
    "staff@clinicai.com",
    "doctor.cariri@clinicai.com",
    "staff.cariri@clinicai.com",
    "doctor.endoscopia@clinicai.com",
    "staff.endoscopia@clinicai.com",
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
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

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
        password_hash=get_password_hash(
            password
        ),
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
    """Cria um médico e um funcionário por clínica."""

    definitions = {
        "doctor_primary": {
            "name": "Dr. João Silva",
            "email": "doctor@clinicai.com",
            "cpf": "11144477735",
            "role": "doctor",
            "clinic": "clinic_primary",
        },
        "staff_primary": {
            "name": "Recepção Clínica Primária",
            "email": "staff@clinicai.com",
            "cpf": "15350946056",
            "role": "clinic_staff",
            "clinic": "clinic_primary",
        },
        "doctor_large": {
            "name": "Dr. Marcos Lima",
            "email": "doctor.cariri@clinicai.com",
            "cpf": "31415926590",
            "role": "doctor",
            "clinic": "clinic_large",
        },
        "staff_large": {
            "name": "Recepção Hospital Cariri",
            "email": "staff.cariri@clinicai.com",
            "cpf": "27182818205",
            "role": "clinic_staff",
            "clinic": "clinic_large",
        },
        "doctor_specialized": {
            "name": "Dra. Helena Costa",
            "email": "doctor.endoscopia@clinicai.com",
            "cpf": "16180339805",
            "role": "doctor",
            "clinic": "clinic_specialized",
        },
        "staff_specialized": {
            "name": "Recepção Centro Endoscópico",
            "email": "staff.endoscopia@clinicai.com",
            "cpf": "14142135651",
            "role": "clinic_staff",
            "clinic": "clinic_specialized",
        },
    }

    users = {
        "admin_master": admin_master,
    }

    for key, definition in definitions.items():
        clinic = clinics[
            definition["clinic"]
        ]

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
                "user_active"
            ].id,
            clinic_id=clinic.id,
        )

    return users
