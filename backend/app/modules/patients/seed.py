"""Pacientes fictícios da massa acadêmica demonstrativa."""

from datetime import date
import unicodedata

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


def _normalize_email_component(
    value: str,
) -> str:
    """Remove acentos e caracteres não alfanuméricos."""

    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    ascii_value = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    return "".join(
        character
        for character in ascii_value.lower()
        if character.isalnum()
    )


def _build_demo_email(name: str) -> str:
    """Gera nome.segundo_nome@example.com."""

    name_parts = [
        part
        for part in name.split()
        if part
    ]

    if len(name_parts) < 2:
        raise RuntimeError(
            "O paciente acadêmico deve possuir "
            "pelo menos dois componentes no nome."
        )

    first_name = _normalize_email_component(
        name_parts[0]
    )
    second_name = _normalize_email_component(
        name_parts[1]
    )

    return (
        f"{first_name}.{second_name}"
        "@example.com"
    )


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


def get_demo_patient_definitions() -> dict[str, dict]:
    """Retorna identidades e campos canônicos dos 30 pacientes demo."""

    definitions: dict[str, dict] = {}
    for clinic_index, (clinic_key, names) in enumerate(
        PATIENT_NAMES.items(),
        start=1,
    ):
        for patient_index, name in enumerate(names, start=1):
            patient_key = f"{clinic_key}_patient_{patient_index:02d}"
            definitions[patient_key] = {
                "clinic_key": clinic_key,
                "doctor_key": (
                    "doctor_primary_secondary"
                    if clinic_key == "clinic_primary" and patient_index >= 6
                    else DOCTOR_BY_CLINIC[clinic_key]
                ),
                "status_key": (
                    "patient_inactive"
                    if patient_index in {9, 10}
                    else "patient_active"
                ),
                "name": name,
                "cpf": _build_demo_cpf(
                    700_000_000 + clinic_index * 100 + patient_index
                ),
                "birth_date": date(
                    1950 + ((clinic_index * 10 + patient_index) * 3) % 51,
                    (patient_index + clinic_index) % 12 + 1,
                    (patient_index * 2 + clinic_index) % 27 + 1,
                ),
                "sex": "female" if patient_index % 2 else "male",
                "email": _build_demo_email(
                    name
                ),
                "phone": f"8898{clinic_index:02d}{patient_index:05d}",
            }
    return definitions


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
    """Reconcilia o paciente demo pela identidade clínica/CPF."""

    patient = (
        db.query(Patient)
        .filter(
            Patient.clinic_id == clinic_id,
            Patient.cpf == cpf,
        )
        .first()
    )

    if patient is None:
        patient = Patient(clinic_id=clinic_id, cpf=cpf)
        db.add(patient)

    patient.doctor_id = doctor_id
    patient.status_id = status_id
    patient.name = name
    patient.birth_date = birth_date
    patient.sex = sex
    patient.email = email
    patient.phone = phone
    patient.city = city
    patient.state = state
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
    """Cria dez pacientes por clínica, incluindo dois inativos em cada uma."""

    expected_patient_keys = {
        definition["patient_key"]
        for definition
        in get_demo_exam_definitions()
    }

    result: dict[str, Patient] = {}

    for patient_key, definition in get_demo_patient_definitions().items():
        clinic = clinics[definition["clinic_key"]]
        doctor = users[definition["doctor_key"]]
        result[patient_key] = get_or_create_patient(
            db,
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            status_id=statuses[definition["status_key"]].id,
            name=definition["name"],
            cpf=definition["cpf"],
            birth_date=definition["birth_date"],
            sex=definition["sex"],
            email=definition["email"],
            phone=definition["phone"],
            city=clinic.city,
            state=clinic.state,
        )

    if set(result) != expected_patient_keys:
        raise RuntimeError(
            "As chaves dos pacientes não correspondem "
            "ao manifesto acadêmico."
        )

    return result
