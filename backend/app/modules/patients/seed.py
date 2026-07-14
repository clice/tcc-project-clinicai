"""Massa acadêmica fictícia do módulo de pacientes."""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.clinics.model import Clinic
from app.modules.patients.model import Patient
from app.modules.statuses.model import Status
from app.modules.users.model import User


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
    """Busca pelo identificador natural da massa demo ou cria o paciente."""

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
    db.flush()
    db.refresh(patient)

    return patient


def seed_patients(
    db: Session,
    *,
    clinics: dict[str, Clinic],
    users: dict[str, User],
    statuses: dict[str, Status],
) -> dict[str, Patient]:
    """Cria pacientes fictícios com vínculos determinísticos.

    Não é feita busca pelo "primeiro" médico ou clínica do banco. Todos os
    registros usam explicitamente a clínica e o médico do dataset acadêmico,
    evitando que dados administrativos preexistentes mudem os vínculos demo.
    """

    clinic = clinics.get("clinic_primary")
    doctor = users.get("doctor_primary")
    active_status = statuses.get("patient_active")

    if not clinic or not doctor or not active_status:
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
        "patient_fictitious_cpf": get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=active_status.id,
            name="Paciente com CPF Fictício",
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
