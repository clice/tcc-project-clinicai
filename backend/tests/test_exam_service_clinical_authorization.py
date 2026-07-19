"""Defesa em profundidade dos serviços clínicos de exames."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.exams.service import (
    create_exam,
    list_exam_form_options,
)


def build_user(role_name: str):
    return SimpleNamespace(
        id=10,
        clinic_id=1,
        role=SimpleNamespace(
            name=role_name,
        ),
    )


@pytest.mark.parametrize(
    "role_name",
    [
        "clinic_staff",
        "admin_master",
    ],
)
@pytest.mark.parametrize(
    "operation",
    [
        "create",
        "form_options",
    ],
)
def test_non_doctor_cannot_call_clinical_exam_services(
    role_name: str,
    operation: str,
) -> None:
    user = build_user(role_name)

    with pytest.raises(HTTPException) as exc_info:
        if operation == "create":
            create_exam(
                db=None,
                payload=None,
                file=None,
                current_user=user,
            )
        else:
            list_exam_form_options(
                db=None,
                current_user=user,
            )

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == "Apenas usuários com perfil médico "
        "podem executar ações clínicas de exames."
    )
