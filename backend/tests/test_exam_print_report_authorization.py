"""Testes do contrato de impressão de exames finalizados."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.main import app
from app.modules.exams.pdf_report import (
    build_exam_report_filename,
    generate_exam_report_pdf,
)

from app.modules.exams.service import (
    build_exam_print_report_response,
    validate_user_can_print_exam,
)


PRINT_ROUTE_NAMES = {
    "get_exam_print_report_route",
    "preview_print_exam_file_route",
    "preview_print_exam_ai_file_route",
    "download_exam_print_report_pdf_route",
}


def build_user(
    role_name: str,
    *,
    user_id: int = 10,
    clinic_id: int | None = 20,
):
    return SimpleNamespace(
        id=user_id,
        clinic_id=clinic_id,
        role=SimpleNamespace(name=role_name),
    )


def build_exam(
    *,
    status_name: str = "completed",
    doctor_id: int = 10,
    clinic_id: int = 20,
):
    return SimpleNamespace(
        id=30,
        clinic_id=clinic_id,
        clinic=SimpleNamespace(name="Clínica Teste"),
        patient=SimpleNamespace(
            name="Paciente Teste",
            cpf="12345678901",
            birth_date=None,
            sex="female",
            phone="88999999999",
        ),
        doctor_id=doctor_id,
        doctor=SimpleNamespace(name="Médico Teste"),
        status=SimpleNamespace(
            name=status_name,
            display_name="Concluído",
        ),
        exam_type="colonoscopy",
        exam_date=None,
        description="Colonoscopia de acompanhamento",
        observations="Observação do exame",
        clinical_indication="Indicação clínica",
        findings="Achados da revisão",
        conclusion="Conclusão médica",
        reviewed_by=SimpleNamespace(name="Médico Revisor"),
        reviewed_at=None,
        file_path="data/exams/original.jpg",
        ai_analysis=SimpleNamespace(
            prediction_label="abnormal",
            prediction_class=1,
            confidence=0.93,
            model_name="ClinicAI Ensemble",
            model_version="1.0",
            gradcam_path="data/gradcam/map.png",
        ),
    )


def test_print_routes_require_operational_exam_permission():
    routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.name in PRINT_ROUTE_NAMES
    ]

    assert {route.name for route in routes} == PRINT_ROUTE_NAMES

    for route in routes:
        dependencies = [
            dependency.call
            for dependency in route.dependant.dependencies
            if getattr(
                dependency.call,
                "required_permission_name",
                None,
            )
        ]

        assert len(dependencies) == 1
        assert (
            dependencies[0].required_permission_name
            == "exams:list"
        )
        assert (
            getattr(
                dependencies[0],
                "required_role_name",
                None,
            )
            is None
        )


@pytest.mark.parametrize(
    ("role_name", "status_name"),
    [
        ("doctor", "completed"),
        ("doctor", "completed_with_divergence"),
        ("clinic_manager", "completed"),
        ("clinic_manager", "completed_with_divergence"),
    ],
)
def test_authorized_profiles_can_print_finalized_exam(
    role_name: str,
    status_name: str,
):
    user = build_user(role_name)
    exam = build_exam(status_name=status_name)

    validate_user_can_print_exam(
        current_user=user,
        exam=exam,
    )


@pytest.mark.parametrize(
    "role_name",
    ["admin_master", "unknown"],
)
def test_unauthorized_role_cannot_print(role_name: str):
    user = build_user(role_name)
    exam = build_exam()

    with pytest.raises(HTTPException) as exc_info:
        validate_user_can_print_exam(
            current_user=user,
            exam=exam,
        )

    assert exc_info.value.status_code == 403


def test_doctor_cannot_print_exam_from_another_doctor():
    user = build_user("doctor", user_id=99)
    exam = build_exam(doctor_id=10)

    with pytest.raises(HTTPException) as exc_info:
        validate_user_can_print_exam(
            current_user=user,
            exam=exam,
        )

    assert exc_info.value.status_code == 403


def test_manager_cannot_print_exam_from_another_clinic():
    user = build_user(
        "clinic_manager",
        clinic_id=99,
    )
    exam = build_exam(clinic_id=20)

    with pytest.raises(HTTPException) as exc_info:
        validate_user_can_print_exam(
            current_user=user,
            exam=exam,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.parametrize(
    "status_name",
    [
        "pending",
        "processing",
        "awaiting_review",
        "failed",
        "canceled",
    ],
)
def test_non_finalized_exam_cannot_be_printed(
    status_name: str,
):
    user = build_user("doctor")
    exam = build_exam(status_name=status_name)

    with pytest.raises(HTTPException) as exc_info:
        validate_user_can_print_exam(
            current_user=user,
            exam=exam,
        )

    assert exc_info.value.status_code == 409


def test_report_contains_exam_ai_and_medical_review():
    response = build_exam_print_report_response(
        build_exam()
    )

    assert response["description"] == (
        "Colonoscopia de acompanhamento"
    )
    assert response["patient_name"] == "Paciente Teste"
    assert response["ai_prediction_label"] == "abnormal"
    assert response["ai_confidence"] == 0.93
    assert response["findings"] == "Achados da revisão"
    assert response["conclusion"] == "Conclusão médica"
    assert response["original_image_available"] is True
    assert response["gradcam_available"] is True

    assert "history" not in response
    assert "audit_logs" not in response

def test_pdf_generator_returns_valid_document():
    exam = build_exam()

    content = generate_exam_report_pdf(
        exam,
        original_image_path=None,
        gradcam_path=None,
    )

    assert content.startswith(b"%PDF-")
    assert len(content) > 1000


def test_pdf_filename_is_safe_and_descriptive():
    filename = build_exam_report_filename(
        build_exam()
    )

    assert filename == (
        "relatorio-exame-30-paciente-teste.pdf"
    )

