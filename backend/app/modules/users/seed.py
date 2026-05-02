"""
Seed do módulo de usuários.

Este arquivo cria o usuário administrador inicial do sistema.
"""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.clinics.model import Clinic
from app.modules.users.model import User


def get_or_create_user(
    db: Session,
    email: str,
    name: str,
    role_id: int,
    status_id: int,
    password: str,
    clinic_id: int | None = None,
    cpf: str | None = None,
    phone: str | None = None,
) -> User:
    """
    Evita duplicação de usuários no seed.
    """
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
    db.commit()
    db.refresh(user)

    return user


def seed_users(
    db: Session,
    roles: dict[str, Role],
    statuses: dict[str, Status],
    clinics: dict[str, Clinic],
) -> dict[str, User]:
    """
    Seed completo de usuários do sistema.
    """

    return {
        "admin_master": get_or_create_user(
            db,
            name="Administrador Master",
            email="admin@clinicai.com",
            password="123456",
            role_id=roles["admin_master"].id,
            status_id=statuses["user_active"].id,
            clinic_id=None,
        ),
        "admin_clinic_primary": get_or_create_user(
            db,
            name="Admin Clínica Primária",
            email="admin.primaria@clinicai.com",
            password="123456",
            role_id=roles["admin"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
        "doctor_primary": get_or_create_user(
            db,
            name="Dr. João Silva",
            email="doctor@clinicai.com",
            password="123456",
            role_id=roles["doctor"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
        "doctor_secondary": get_or_create_user(
            db,
            name="Dra. Maria Souza",
            email="doctor2@clinicai.com",
            password="123456",
            role_id=roles["doctor"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_secondary"].id,
        ),
        "staff_primary": get_or_create_user(
            db,
            name="Recepção Clínica",
            email="staff@clinicai.com",
            password="123456",
            role_id=roles["staff"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
        "user_inactive": get_or_create_user(
            db,
            name="Usuário Inativo",
            email="inactive@clinicai.com",
            password="123456",
            role_id=roles["staff"].id,
            status_id=statuses["user_inactive"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
        "user_blocked": get_or_create_user(
            db,
            name="Usuário Bloqueado",
            email="blocked@clinicai.com",
            password="123456",
            role_id=roles["staff"].id,
            status_id=statuses.get("user_blocked", statuses["user_inactive"]).id,
            clinic_id=clinics["clinic_primary"].id,
        ),
        "user_no_clinic": get_or_create_user(
            db,
            name="Usuário Sem Clínica",
            email="noclinic@clinicai.com",
            password="123456",
            role_id=roles["staff"].id,
            status_id=statuses["user_active"].id,
            clinic_id=None,
        ),
    }