"""Pacientes fictícios da massa acadêmica demonstrativa."""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.academic_demo_assets import (
    get_demo_exam_definitions,
)
from app.modules.clinics.model import Clinic
from app.modules.patients.model import Patient
from app.modules.statuses.model import Status
from app.modules.users.model import User


PATIENT_NAMES = {
    "clinic_primary": (
        "Maria Oliveira",
        "João Santos",
        "José Ferreira",
        "Ana Clara Souza",
        "Carlos Eduardo Lima",
        "Francisca Alves",
        "Paulo Henrique Melo",
        "Luciana Ribeiro",
        "Rafael Nogueira",
        "Beatriz Martins",
    ),
    "clinic_large": (
        "Antônio Rodrigues",
        "Camila Fernandes",
        "Eduardo Barbosa",
        "Fernanda Araújo",
        "Geraldo Monteiro",
        "Isabela Correia",
        "Leandro Cardoso",
        "Márcia Teixeira",
        "Ricardo Almeida",
        "Sônia Carvalho",
    ),
    "clinic_specialized": (
        "Adriana Moreira",
        "Bruno Cavalcante",
        "Cláudia Mendes",
        "Daniel Pinheiro",
        "Eliane Gonçalves",
        "Fábio Freitas",
        "Gabriela Rocha",
        "Hugo Tavares",
        "Irene Castro",
        "Júlio Peixoto",
    ),
}

DOCTOR_BY_CLINIC = {
    "clinic_primary": "doctor_primary",
    "clinic_large": "doctor_large",
    "clinic_specialized": "doctor_specialized",
}


def _build_demo_cpf(base: int) -> str:
    """Gera CPF fictício com dígitos verificadores válidos."""

    digits = f"{base:09d}"

    for initial_weight in (10, 11):
        total = sum(
            int(character)
            * (initial_weight - index)
            for index, character in enumerate(
                digits
            )
        )
        remainder = (total * 10) % 11
        digits += str(
            0
            if remainder == 10
            else remainder
        )

    return digits


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
    city: str | None = None,
    state: str | None = None,
) -> Patient:
    """Busca pelo CPF na clínica ou cria o paciente."""

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
    """Cria dez pacientes ativos em cada clínica."""

    expected_patient_keys = {
        definition["patient_key"]
        for definition
        in get_demo_exam_definitions()
    }

    result: dict[str, Patient] = {}

    for clinic_index, (
        clinic_key,
        names,
    ) in enumerate(
        PATIENT_NAMES.items(),
        start=1,
    ):
        clinic = clinics[clinic_key]
        doctor = users[
            DOCTOR_BY_CLINIC[clinic_key]
        ]

        for patient_index, name in enumerate(
            names,
            start=1,
        ):
            patient_key = (
                f"{clinic_key}_patient_"
                f"{patient_index:02d}"
            )

            result[patient_key] = (
                get_or_create_patient(
                    db,
                    clinic_id=clinic.id,
                    doctor_id=doctor.id,
                    status_id=statuses[
                        "patient_active"
                    ].id,
                    name=name,
                    cpf=_build_demo_cpf(
                        700_000_000
                        + clinic_index * 100
                        + patient_index
                    ),
                    birth_date=date(
                        1950
                        + (
                            (
                                clinic_index * 10
                                + patient_index
                            )
                            * 3
                        )
                        % 51,
                        (
                            patient_index
                            + clinic_index
                        )
                        % 12
                        + 1,
                        (
                            patient_index * 2
                            + clinic_index
                        )
                        % 27
                        + 1,
                    ),
                    sex=(
                        "female"
                        if patient_index % 2
                        else "male"
                    ),
                    email=(
                        f"paciente.{clinic_index}."
                        f"{patient_index:02d}"
                        "@example.com"
                    ),
                    phone=(
                        "8898"
                        f"{clinic_index:02d}"
                        f"{patient_index:05d}"
                    ),
                    city=clinic.city,
                    state=clinic.state,
                )
            )

    if set(result) != expected_patient_keys:
        raise RuntimeError(
            "As chaves dos pacientes não correspondem "
            "ao manifesto acadêmico."
        )

    return result
