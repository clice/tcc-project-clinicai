"""Testes das barreiras de isolamento entre clínicas, médicos e registros."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.common.access_control import (
    ensure_user_can_access_clinic_data,
    ensure_user_can_access_exam,
    ensure_user_can_access_patient,
)
from app.modules.roles.model import Role
from app.modules.users.model import User


def build_user(
    role_name: str,
    *,
    user_id: int = 10,
    clinic_id: int | None = 1,
) -> User:
    return User(
        id=user_id,
        clinic_id=clinic_id,
        role=Role(name=role_name, display_name=role_name),
    )


def test_clinic_manager_patient_access_is_limited_to_own_clinic() -> None:
    staff = build_user("clinic_manager", clinic_id=1)
    own_record = SimpleNamespace(clinic_id=1, doctor_id=99)
    other_record = SimpleNamespace(clinic_id=2, doctor_id=99)

    ensure_user_can_access_patient(
        current_user=staff,
        patient=own_record,
    )

    with pytest.raises(HTTPException) as exc_info:
        ensure_user_can_access_patient(
            current_user=staff,
            patient=other_record,
        )

    assert exc_info.value.status_code == 403


def test_clinic_manager_cannot_access_individual_exams() -> None:
    staff = build_user("clinic_manager", clinic_id=1)

    for exam in (
        SimpleNamespace(clinic_id=1, doctor_id=99),
        SimpleNamespace(clinic_id=2, doctor_id=99),
    ):
        with pytest.raises(HTTPException) as exc_info:
            ensure_user_can_access_exam(
                current_user=staff,
                exam=exam,
            )

        assert exc_info.value.status_code == 403


@pytest.mark.parametrize("resource_kind", ["patient", "exam"])
def test_doctor_access_is_limited_to_assigned_records(resource_kind: str) -> None:
    doctor = build_user("doctor", user_id=10, clinic_id=1)
    own_record = SimpleNamespace(clinic_id=1, doctor_id=10)
    colleague_record = SimpleNamespace(clinic_id=1, doctor_id=11)
    guard = (
        ensure_user_can_access_patient
        if resource_kind == "patient"
        else ensure_user_can_access_exam
    )

    guard(current_user=doctor, **{resource_kind: own_record})
    with pytest.raises(HTTPException) as exc_info:
        guard(current_user=doctor, **{resource_kind: colleague_record})

    assert exc_info.value.status_code == 403


def test_non_admin_cannot_submit_data_for_another_clinic() -> None:
    user = build_user("clinic_manager", clinic_id=1)

    ensure_user_can_access_clinic_data(current_user=user, clinic_id=1)
    with pytest.raises(HTTPException) as exc_info:
        ensure_user_can_access_clinic_data(current_user=user, clinic_id=2)

    assert exc_info.value.status_code == 403


def test_admin_master_has_administrative_but_not_clinical_access() -> None:
    admin = build_user("admin_master", clinic_id=None)
    external_record = SimpleNamespace(clinic_id=999, doctor_id=999)

    ensure_user_can_access_clinic_data(
        current_user=admin,
        clinic_id=999,
    )
    ensure_user_can_access_patient(
        current_user=admin,
        patient=external_record,
    )

    with pytest.raises(HTTPException) as exc_info:
        ensure_user_can_access_exam(
            current_user=admin,
            exam=external_record,
        )

    assert exc_info.value.status_code == 403
