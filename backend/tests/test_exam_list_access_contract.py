"""Contratos do acesso resumido aos exames."""

from types import SimpleNamespace

import pytest
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


def test_manager_default_matrix_only_grants_listing() -> None:
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


def build_exam_fixture(
    *,
    status_name: str = "awaiting_review",
    status_display_name: str = "Aguardando revisão",
    with_analysis: bool = True,
) -> SimpleNamespace:
    ai_analysis = None

    if with_analysis:
        ai_analysis = SimpleNamespace(
            status=SimpleNamespace(name="completed"),
            prediction_label="abnormal",
            gradcam_path="data/gradcam/example.png",
        )

    return SimpleNamespace(
        id=7,
        clinic_id=2,
        clinic=SimpleNamespace(name="Clínica"),
        patient_id=4,
        patient=SimpleNamespace(name="Paciente"),
        doctor_id=5,
        doctor=SimpleNamespace(name="Médico"),
        status_id=3,
        status=SimpleNamespace(
            name=status_name,
            display_name=status_display_name,
        ),
        exam_type="colonoscopy",
        exam_date=None,
        description="Exame",
        analysis_in_progress=False,
        ai_analysis=ai_analysis,
        file_path="data/exams/example.jpg",
    )


def build_user(
    role_name: str,
    permissions: tuple[str, ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        role=SimpleNamespace(
            name=role_name,
            role_permissions=[
                SimpleNamespace(
                    permission=SimpleNamespace(
                        name=permission,
                    )
                )
                for permission in permissions
            ],
        )
    )


def expected_operational_fields() -> set[str]:
    return {
        "id",
        "clinic_id",
        "clinic_name",
        "patient_id",
        "patient_name",
        "doctor_id",
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


def test_list_route_omits_unset_optional_fields() -> None:
    route = next(
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/exams/"
        and "GET" in route.methods
    )

    assert route.response_model_exclude_unset is True


@pytest.mark.parametrize(
    ("role_name", "permissions"),
    [
        ("clinic_manager", ("exams:list",)),
        ("admin_master", ()),
        ("doctor", ("exams:list",)),
    ],
)
def test_list_response_omits_prediction_for_unauthorized_users(
    role_name: str,
    permissions: tuple[str, ...],
) -> None:
    response = build_exam_list_response(
        build_exam_fixture(),
        current_user=build_user(
            role_name,
            permissions,
        ),
    )

    assert set(response) == expected_operational_fields()
    assert response["clinic_name"] == "Clínica"
    assert response["gradcam_available"] is True
    assert "ai_prediction_label" not in response
    assert "ai_prediction_class" not in response


@pytest.mark.parametrize(
    ("status_name", "status_display_name"),
    [
        ("awaiting_review", "Aguardando revisão"),
        ("completed", "Concluído"),
        (
            "completed_with_divergence",
            "Com divergência",
        ),
    ],
)
def test_list_response_exposes_prediction_to_authorized_doctor(
    status_name: str,
    status_display_name: str,
) -> None:
    response = build_exam_list_response(
        build_exam_fixture(
            status_name=status_name,
            status_display_name=status_display_name,
        ),
        current_user=build_user(
            "doctor",
            (
                "exams:list",
                "ai_analysis:read",
            ),
        ),
    )

    assert set(response) == (
        expected_operational_fields()
        | {"ai_prediction_label"}
    )
    assert response["ai_prediction_label"] == "abnormal"
    assert "ai_prediction_class" not in response


@pytest.mark.parametrize(
    "status_name",
    [
        "pending",
        "processing",
        "failed",
        "canceled",
    ],
)
def test_list_response_omits_prediction_outside_supported_statuses(
    status_name: str,
) -> None:
    response = build_exam_list_response(
        build_exam_fixture(
            status_name=status_name,
            status_display_name=status_name,
        ),
        current_user=build_user(
            "doctor",
            (
                "exams:list",
                "ai_analysis:read",
            ),
        ),
    )

    assert set(response) == expected_operational_fields()
    assert "ai_prediction_label" not in response


def test_list_response_omits_prediction_without_analysis() -> None:
    response = build_exam_list_response(
        build_exam_fixture(
            with_analysis=False,
        ),
        current_user=build_user(
            "doctor",
            (
                "exams:list",
                "ai_analysis:read",
            ),
        ),
    )

    assert set(response) == expected_operational_fields()
    assert response["gradcam_available"] is False
    assert "ai_prediction_label" not in response


def test_list_response_excludes_clinical_and_sensitive_fields() -> None:
    response = build_exam_list_response(
        build_exam_fixture(),
        current_user=build_user(
            "clinic_manager",
            ("exams:list",),
        ),
    )

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

    assert forbidden.isdisjoint(response)
