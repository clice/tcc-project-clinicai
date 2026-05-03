"""
Seed do módulo de pacientes.

Este arquivo cadastra pacientes iniciais usados em desenvolvimento.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.common.constants import RoleName, StatusName, StatusScope
from app.modules.clinics.model import Clinic
from app.modules.patients.model import Patient
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


def get_active_patient_status(db: Session) -> Status | None:
    """
    Busca o status active para pacientes.
    """
    return (
        db.query(Status)
        .filter(
            Status.name == StatusName.ACTIVE.value,
            Status.applies_to == StatusScope.PATIENT.value,
        )
        .first()
    )


def get_first_active_clinic(db: Session) -> Clinic | None:
    """
    Busca uma clínica ativa para vincular pacientes de exemplo.
    """
    return (
        db.query(Clinic)
        .join(Status, Clinic.status_id == Status.id)
        .filter(
            Status.name == StatusName.ACTIVE.value,
            Status.applies_to == StatusScope.CLINIC.value,
        )
        .order_by(Clinic.id.asc())
        .first()
    )


def get_first_active_doctor_from_clinic(
    db: Session,
    clinic_id: int,
) -> User | None:
    """
    Busca um médico ativo da clínica para vincular pacientes.
    """
    return (
        db.query(User)
        .join(Role, User.role_id == Role.id)
        .join(Status, User.status_id == Status.id)
        .filter(
            User.clinic_id == clinic_id,
            Role.name == RoleName.DOCTOR.value,
            Status.name == StatusName.ACTIVE.value,
            Status.applies_to == StatusScope.USER.value,
        )
        .order_by(User.id.asc())
        .first()
    )


def get_or_create_patient(
    db: Session,
    *,
    clinic_id: int,
    doctor_id: int,
    status_id: int,
    name: str,
    cpf: str,
    birth_date: date | None = None,
    sex: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    zip_code: str | None = None,
    address: str | None = None,
    number: str | None = None,
    complement: str | None = None,
    neighborhood: str | None = None,
    city: str | None = None,
    state: str | None = None,
) -> Patient:
    """
    Busca um paciente existente ou cria um novo.
    """
    patient = (
        db.query(Patient)
        .filter(
            Patient.clinic_id == clinic_id,
            Patient.cpf == cpf,
        )
        .first()
    )

    if patient:
        return patient

    patient = Patient(
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        status_id=status_id,
        name=name,
        cpf=cpf,
        birth_date=birth_date,
        sex=sex,
        email=email,
        phone=phone,
        zip_code=zip_code,
        address=address,
        number=number,
        complement=complement,
        neighborhood=neighborhood,
        city=city,
        state=state,
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient


def seed_patients(db: Session) -> dict[str, Patient]:
    """
    Cria pacientes iniciais para desenvolvimento.

    Depende de clinics, roles, users e statuses já terem sido criados.
    """
    active_status = get_active_patient_status(db)
    clinic = get_first_active_clinic(db)

    if not active_status or not clinic:
        return {}

    doctor = get_first_active_doctor_from_clinic(db=db, clinic_id=clinic.id)

    if not doctor:
        return {}

    return {
        "patient_example_1": get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=active_status.id,
            name="Maria Oliveira",
            cpf="52998224725",
            birth_date=date(1988, 5, 14),
            sex="female",
            email="maria.oliveira@example.com",
            phone="88999990000",
            zip_code="63000000",
            address="Rua Exemplo",
            number="100",
            neighborhood="Centro",
            city="Barbalha",
            state="CE",
        ),
        "patient_example_2": get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=active_status.id,
            name="João Santos",
            cpf="11144477735",
            birth_date=date(1979, 9, 22),
            sex="male",
            email="joao.santos@example.com",
            zip_code="63000000",
            address="Avenida Teste",
            number="200",
            neighborhood="Centro",
            city="Barbalha",
            state="CE",
        ),
        "patient_elderly": get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=active_status.id,
            name="José Ferreira",
            cpf="39053344705",
            birth_date=date(1945, 3, 10),
            sex="male",
            phone="88988887777",
            city="Barbalha",
            state="CE",
        ),
        "patient_young": get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=active_status.id,
            name="Ana Clara Souza",
            cpf="22233344450",
            birth_date=date(2005, 7, 2),
            sex="female",
            email="ana.clara@example.com",
            city="Juazeiro do Norte",
            state="CE",
        ),
        "patient_no_cpf": get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=active_status.id,
            name="Paciente Sem CPF",
            cpf="00000000000",
            birth_date=None,
            sex=None,
        ),
        "patient_minimal": get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=active_status.id,
            name="Paciente Minimalista",
            cpf="12312312387",
        ),
        "patient_complete": get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=active_status.id,
            name="Carlos Eduardo Lima",
            cpf="98765432100",
            birth_date=date(1990, 1, 1),
            sex="male",
            email="carlos.lima@example.com",
            phone="88977776666",
            zip_code="63000000",
            address="Rua Completa",
            number="321",
            complement="Casa",
            neighborhood="Centro",
            city="Juazeiro do Norte",
            state="CE",
        ),
        "patient_female_elderly": get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=active_status.id,
            name="Dona Francisca Alves",
            cpf="32165498700",
            birth_date=date(1952, 11, 8),
            sex="female",
            phone="88966665555",
            city="Crato",
            state="CE",
        ),
    }
