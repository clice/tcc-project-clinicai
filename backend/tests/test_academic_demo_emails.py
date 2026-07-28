"""Convenções dos e-mails da massa acadêmica."""

from app.modules.patients.seed import (
    get_demo_patient_definitions,
)
from app.modules.users.seed import (
    ACADEMIC_DEMO_EMAILS,
)


EXPECTED_ACADEMIC_USER_EMAILS = {
    "dr.joao@clinicai.com",
    "dr.lucas@clinicai.com",
    "gestor.clinicai@clinicai.com",
    "dr.marcos@hospitalcariri.com",
    "gestor.hospital@hospitalcariri.com",
    "dra.helena@cariri.com",
    "gestor.centro@cariri.com",
    "dr.renato@clinicai.com",
    "dra.paula@clinicai.com",
    "gestor.inativo@hospitalcariri.com",
    "gestor.inativo@cariri.com",
    "admin.inativo@clinicai.com",
}


def test_academic_user_emails_follow_role_convention():
    assert set(ACADEMIC_DEMO_EMAILS) == (
        EXPECTED_ACADEMIC_USER_EMAILS
    )

    assert len(ACADEMIC_DEMO_EMAILS) == len(
        set(ACADEMIC_DEMO_EMAILS)
    )

    assert all(
        email == email.lower()
        for email in ACADEMIC_DEMO_EMAILS
    )


def test_patient_emails_use_first_two_name_parts():
    definitions = (
        get_demo_patient_definitions()
    )

    actual_emails = {
        definition["email"]
        for definition in definitions.values()
    }

    assert len(actual_emails) == 30

    assert {
        "maria.oliveira@example.com",
        "joao.santos@example.com",
        "ana.clara@example.com",
        "carlos.eduardo@example.com",
        "antonio.rodrigues@example.com",
        "claudia.mendes@example.com",
    }.issubset(actual_emails)

    assert all(
        email.endswith("@example.com")
        and email.count("@") == 1
        and "." in email.split("@", 1)[0]
        and email == email.lower()
        and email.isascii()
        for email in actual_emails
    )
