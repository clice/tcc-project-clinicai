"""
Seed do módulo de usuários.

Este arquivo cria usuários iniciais do sistema.
"""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.modules.clinics.model import Clinic
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


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
    db.commit()
    db.refresh(user)

    return user


def seed_users(
    db: Session,
    roles: dict[str, Role],
    statuses: dict[str, Status],
    clinics: dict[str, Clinic],
) -> dict[str, User]:
    return {
        "admin_master": get_or_create_user(
            db=db,
            name="Administrador Master",
            email="admin@clinicai.com",
            password="123456",
            cpf="39053344705",
            role_id=roles["admin_master"].id,
            status_id=statuses["user_active"].id,
            clinic_id=None,
        ),
        "doctor_primary": get_or_create_user(
            db=db,
            name="Dr. João Silva",
            email="doctor@clinicai.com",
            password="123456",
            cpf="11144477735",
            role_id=roles["doctor"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
        "doctor_secondary": get_or_create_user(
            db=db,
            name="Dra. Maria Souza",
            email="doctor2@clinicai.com",
            password="123456",
            cpf="52998224725",
            role_id=roles["doctor"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_secondary"].id,
        ),
        "staff_primary": get_or_create_user(
            db=db,
            name="Recepção Clínica",
            email="staff@clinicai.com",
            password="123456",
            cpf="15350946056",
            role_id=roles["clinic_staff"].id,
            status_id=statuses["user_active"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
        "user_inactive": get_or_create_user(
            db=db,
            name="Usuário Inativo",
            email="inactive@clinicai.com",
            password="123456",
            cpf="98765432100",
            role_id=roles["clinic_staff"].id,
            status_id=statuses["user_inactive"].id,
            clinic_id=clinics["clinic_primary"].id,
        ),
    }
