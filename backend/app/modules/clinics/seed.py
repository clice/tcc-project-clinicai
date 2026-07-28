"""Clínicas fictícias da demonstração acadêmica."""

from sqlalchemy.orm import Session

from app.modules.clinics.model import Clinic
from app.modules.statuses.model import Status


ACADEMIC_DEMO_CLINICS = {
    "clinic_primary": {
        "status": "clinic_active",
        "name": "ClinicAI Endoscopia Especializada",
        "cnpj": "11222333000181",
        "email": "contato@clinicai.com",
        "phone": "8833334444",
        "mobile_phone": "88999998888",
        "zip_code": "63000000",
        "address": "Rua Exemplo",
        "number": "100",
        "complement": None,
        "neighborhood": "Centro",
        "city": "Juazeiro do Norte",
        "state": "CE",
    },
    "clinic_large": {
        "status": "clinic_active",
        "name": "Hospital Regional do Cariri",
        "cnpj": "11666555000122",
        "email": "contato@hospitalcariri.com",
        "phone": "8833338888",
        "mobile_phone": "88999995555",
        "zip_code": "63000000",
        "address": "Av. Leão Sampaio",
        "number": "1500",
        "complement": None,
        "neighborhood": "Triângulo",
        "city": "Juazeiro do Norte",
        "state": "CE",
    },
    "clinic_specialized": {
        "status": "clinic_active",
        "name": "Centro Endoscópico Cariri",
        "cnpj": "11555444000111",
        "email": "endoscopia@cariri.com",
        "phone": "8833339999",
        "mobile_phone": "88999994444",
        "zip_code": "63000000",
        "address": "Rua Saúde",
        "number": "50",
        "complement": "Clínica 3",
        "neighborhood": "Centro",
        "city": "Juazeiro do Norte",
        "state": "CE",
    },
    "clinic_inactive": {
        "status": "clinic_inactive",
        "name": "Clínica Arquivo Cariri",
        "cnpj": "45997418000153",
        "email": "arquivo@clinicai.com",
        "phone": "8833337777",
        "mobile_phone": "88999993333",
        "zip_code": "63000000",
        "address": "Rua Histórica",
        "number": "25",
        "complement": None,
        "neighborhood": "Centro",
        "city": "Juazeiro do Norte",
        "state": "CE",
    },
}


def get_or_create_clinic(
    db: Session,
    name: str,
    cnpj: str,
    email: str | None,
    status_id: int,
    phone: str | None = None,
    mobile_phone: str | None = None,
    zip_code: str | None = None,
    address: str | None = None,
    number: str | None = None,
    complement: str | None = None,
    neighborhood: str | None = None,
    city: str | None = None,
    state: str | None = None,
) -> Clinic:
    """Reconcilia a clínica demo identificada pelo CNPJ reservado."""

    email_collision = None
    if email is not None:
        email_collision = (
            db.query(Clinic)
            .filter(
                Clinic.email == email,
                Clinic.cnpj != cnpj,
            )
            .first()
        )
    if email_collision is not None:
        raise RuntimeError(
            "Colisão da massa acadêmica: o e-mail de clínica "
            f"{email!r} já pertence ao CNPJ {email_collision.cnpj}."
        )

    clinic = (
        db.query(Clinic)
        .filter(Clinic.cnpj == cnpj)
        .first()
    )

    if clinic is None:
        clinic = Clinic(cnpj=cnpj)
        db.add(clinic)

    clinic.name = name
    clinic.email = email
    clinic.phone = phone
    clinic.mobile_phone = mobile_phone
    clinic.zip_code = zip_code
    clinic.address = address
    clinic.number = number
    clinic.complement = complement
    clinic.neighborhood = neighborhood
    clinic.city = city
    clinic.state = state
    clinic.status_id = status_id
    db.flush()
    db.refresh(clinic)

    return clinic


def seed_clinics(
    db: Session,
    statuses: dict[str, Status],
) -> dict[str, Clinic]:
    """Cria três clínicas ativas e uma clínica inativa para demonstração."""

    result: dict[str, Clinic] = {}

    for key, definition in ACADEMIC_DEMO_CLINICS.items():
        clinic_data = dict(definition)
        status_key = clinic_data.pop("status")

        result[key] = get_or_create_clinic(
            db=db,
            status_id=statuses[status_key].id,
            **clinic_data,
        )

    return result
