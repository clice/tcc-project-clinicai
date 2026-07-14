"""
Seed do módulo de clínicas.

Este arquivo cadastra clínicas iniciais para testes e desenvolvimento.
"""

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
    """
    Busca uma clínica pelo CNPJ ou cria uma nova.
    Evita duplicidade quando o seed for executado mais de uma vez.
    """
    clinic = db.query(Clinic).filter(Clinic.cnpj == cnpj).first()

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
    """
    Cria clínicas iniciais do sistema.
    """

    return {
        "clinic_primary": get_or_create_clinic(
            db=db,
            name="Clínica Primária",
            cnpj="11222333000181",
            email="contato@clinicaprimaria.com",
            phone="8833334444",
            mobile_phone="88999998888",
            zip_code="63000000",
            address="Rua Exemplo",
            number="100",
            complement=None,
            neighborhood="Centro",
            city="Juazeiro do Norte",
            state="CE",
            status_id=statuses["clinic_active"].id,
        ),
        "clinic_secondary": get_or_create_clinic(
            db=db,
            name="Clínica Secundária",
            cnpj="11444777000161",
            email="contato@clinicasecundaria.com",
            phone="8833335555",
            mobile_phone="88999997777",
            zip_code="63000000",
            address="Avenida Exemplo",
            number="200",
            complement="Sala 02",
            neighborhood="Centro",
            city="Juazeiro do Norte",
            state="CE",
            status_id=statuses["clinic_inactive"].id,
        ),
        "clinic_inactive": get_or_create_clinic(
            db=db,
            name="Clínica Bloqueada",
            cnpj="11999888000155",
            email="bloqueada@clinicai.com",
            phone="8833336666",
            mobile_phone="88999996666",
            zip_code="63000000",
            address="Rua Bloqueio",
            number="300",
            complement=None,
            neighborhood="Centro",
            city="Juazeiro do Norte",
            state="CE",
            status_id=statuses["clinic_inactive"].id,
        ),
        "clinic_no_email": get_or_create_clinic(
            db=db,
            name="Clínica Sem Email",
            cnpj="11888777000144",
            email=None,
            phone="8833337777",
            mobile_phone=None,
            zip_code="63000000",
            address="Rua Sem Email",
            number="400",
            complement=None,
            neighborhood="Centro",
            city="Crato",
            state="CE",
            status_id=statuses["clinic_active"].id,
        ),
        "clinic_minimal": get_or_create_clinic(
            db=db,
            name="Clínica Minimalista",
            cnpj="11777666000133",
            email=None,
            phone=None,
            mobile_phone=None,
            zip_code=None,
            address=None,
            number=None,
            complement=None,
            neighborhood=None,
            city="Barbalha",
            state="CE",
            status_id=statuses["clinic_active"].id,
        ),
        "clinic_large": get_or_create_clinic(
            db=db,
            name="Hospital Regional Cariri",
            cnpj="11666555000122",
            email="contato@hospitalcariri.com",
            phone="8833338888",
            mobile_phone="88999995555",
            zip_code="63000000",
            address="Av. Leão Sampaio",
            number="1500",
            complement=None,
            neighborhood="Triângulo",
            city="Juazeiro do Norte",
            state="CE",
            status_id=statuses["clinic_active"].id,
        ),
        "clinic_specialized": get_or_create_clinic(
            db=db,
            name="Centro Endoscópico Cariri",
            cnpj="11555444000111",
            email="endoscopia@cariri.com",
            phone="8833339999",
            mobile_phone="88999994444",
            zip_code="63000000",
            address="Rua Saúde",
            number="50",
            complement="Clínica 3",
            neighborhood="Centro",
            city="Juazeiro do Norte",
            state="CE",
            status_id=statuses["clinic_active"].id,
        ),
        "clinic_other_city": get_or_create_clinic(
            db=db,
            name="Clínica Fortaleza Saúde",
            cnpj="11444333000100",
            email="fortaleza@clinicai.com",
            phone="8533332222",
            mobile_phone="85999993333",
            zip_code="60000000",
            address="Av. Beira Mar",
            number="1000",
            complement=None,
            neighborhood="Meireles",
            city="Fortaleza",
            state="CE",
            status_id=statuses["clinic_active"].id,
        ),
    }
