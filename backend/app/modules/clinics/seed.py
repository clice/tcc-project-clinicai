"""Clínicas fictícias da demonstração acadêmica."""

from sqlalchemy.orm import Session

from app.modules.clinics.model import Clinic
from app.modules.statuses.model import Status


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
    """Busca a clínica pelo CNPJ ou cria uma nova."""

    clinic = (
        db.query(Clinic)
        .filter(Clinic.cnpj == cnpj)
        .first()
    )

    if clinic:
        return clinic

    clinic = Clinic(
        name=name,
        cnpj=cnpj,
        email=email,
        phone=phone,
        mobile_phone=mobile_phone,
        zip_code=zip_code,
        address=address,
        number=number,
        complement=complement,
        neighborhood=neighborhood,
        city=city,
        state=state,
        status_id=status_id,
    )

    db.add(clinic)
    db.flush()
    db.refresh(clinic)

    return clinic


def seed_clinics(
    db: Session,
    statuses: dict[str, Status],
) -> dict[str, Clinic]:
    """Cria as três clínicas oficiais da demonstração."""

    active_status = statuses["clinic_active"]

    definitions = {
        "clinic_primary": {
            "name": "Clínica Primária",
            "cnpj": "11222333000181",
            "email": "contato@clinicaprimaria.com",
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
            "name": "Hospital Regional Cariri",
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
    }

    return {
        key: get_or_create_clinic(
            db=db,
            status_id=active_status.id,
            **definition,
        )
        for key, definition in definitions.items()
    }
