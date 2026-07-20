"""Contratos do acesso resumido aos exames."""

from types import SimpleNamespace

from fastapi.routing import APIRoute

from app.main import app
from app.modules.exams.service import build_exam_list_response
from app.modules.role_permissions.seed import (
    CLINIC_MANAGER_PERMISSIONS,
    DOCTOR_PERMISSIONS,
)


def required_permission(path: str, method: str) -> str | None:
    route = next(
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == path
        and method in route.methods
    )
    return next(
        getattr(
            dependency.call,
            "required_permission_name",
            None,
        )
        for dependency in route.dependant.dependencies
        if getattr(
            dependency.call,
            "required_permission_name",
            None,
        )
        is not None
    )


def test_list_and_detail_use_distinct_permissions() -> None:
    assert required_permission("/exams/", "GET") == "exams:list"
    assert (
        required_permission(
            "/exams/{exam_id}/images/download",
            "GET",
        )
        == "exams:download"
    )
    assert (
        required_permission("/exams/{exam_id}", "GET")
        == "exams:read"
    )
    assert (
        required_permission(
            "/exams/{exam_id}/history",
            "GET",
        )
        == "exams:read"
    )
    assert (
        required_permission("/exams/form-options", "GET")
        == "exams:read"
    )


def test_staff_default_matrix_only_grants_listing() -> None:
    assert "exams:list" in CLINIC_MANAGER_PERMISSIONS
    assert "exams:read" not in CLINIC_MANAGER_PERMISSIONS
    assert "exams:create" not in CLINIC_MANAGER_PERMISSIONS
    assert "exams:update" not in CLINIC_MANAGER_PERMISSIONS
    assert "exams:download" not in CLINIC_MANAGER_PERMISSIONS
    assert (
        "exams:change_status"
        not in CLINIC_MANAGER_PERMISSIONS
    )
    assert "exams:review" not in CLINIC_MANAGER_PERMISSIONS
    assert (
        "ai_analysis:create"
        not in CLINIC_MANAGER_PERMISSIONS
    )
    assert "ai_analysis:read" not in CLINIC_MANAGER_PERMISSIONS
    assert "exams:list" in DOCTOR_PERMISSIONS
    assert "exams:read" in DOCTOR_PERMISSIONS


def test_list_response_contains_only_operational_summary() -> None:
    exam = SimpleNamespace(
        id=7,
        clinic_id=2,
        clinic=SimpleNamespace(name="Clínica"),
        patient=SimpleNamespace(name="Paciente"),
        doctor=SimpleNamespace(name="Médico"),
        status_id=3,
        status=SimpleNamespace(
            name="awaiting_review",
            display_name="Aguardando revisão",
        ),
        exam_type="colonoscopy",
        exam_date=None,
        description="Exame",
        analysis_in_progress=False,
        ai_analysis=SimpleNamespace(
            status=SimpleNamespace(name="completed"),
            gradcam_path="data/gradcam/example.png",
        ),
        file_path="data/exams/example.jpg",
    )

    response = build_exam_list_response(exam)

    assert set(response) == {
        "id",
        "clinic_id",
        "clinic_name",
        "patient_name",
        "doctor_name",
        "status_id",
        "status_name",
        "status_display_name",
        "exam_type",
        "exam_date",
        "description",
        "analysis_in_progress",
        "ai_analysis_status",
        "file_available",
        "gradcam_available",
    }

    forbidden = {
        "observations",
        "clinical_indication",
        "findings",
        "conclusion",
        "file_name",
        "file_mime_type",
        "ai_prediction_label",
        "ai_prediction_class",
        "patient_cpf",
        "patient_birth_date",
    }
    assert response["clinic_name"] == "Clínica"
    assert response["gradcam_available"] is True
    assert forbidden.isdisjoint(response)
