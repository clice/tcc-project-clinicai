"""Protege a separação entre listagem operacional e ações clínicas."""

import pytest
from fastapi.routing import APIRoute

from app.main import app


CLINICAL_ROUTE_POLICIES = {
    "get_exam_form_options_route": "exams:read",
    "create_exam_route": "exams:create",
    "get_exam_route": "exams:read",
    "get_exam_history_route": "exams:read",
    "update_exam_route": "exams:update",
    "cancel_exam_route": "exams:change_status",
    "restore_exam_route": "exams:change_status",
    "analyze_exam_route": "ai_analysis:create",
    "review_exam_route": "exams:review",
    "preview_exam_file_route": "exams:download",
    "download_exam_file_route": "exams:download",
    "preview_exam_ai_file_route": "ai_analysis:read",
    "download_exam_ai_file_route": "ai_analysis:read",
    "download_exam_images_package_route": "exams:download",
    "replace_exam_file_route": "exams:upload",
    "create_ai_analysis_route": "ai_analysis:create",
    "list_ai_analysis_route": "ai_analysis:read",
    "get_ai_analysis_by_exam_route": "ai_analysis:read",
    "get_ai_analysis_route": "ai_analysis:read",
    "update_ai_analysis_route": "ai_analysis:update",
}


def get_route(route_name: str) -> APIRoute:
    matches = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.name == route_name
    ]

    assert len(matches) == 1, (
        f"Esperada uma rota chamada {route_name}; "
        f"encontradas {len(matches)}."
    )

    return matches[0]


def get_permission_dependency(route: APIRoute):
    dependencies = [
        dependency.call
        for dependency in route.dependant.dependencies
        if getattr(
            dependency.call,
            "required_permission_name",
            None,
        )
    ]

    assert len(dependencies) == 1, (
        f"{route.name} deve declarar exatamente "
        "uma dependência de permissão."
    )

    return dependencies[0]


@pytest.mark.parametrize(
    ("route_name", "permission_name"),
    CLINICAL_ROUTE_POLICIES.items(),
)
def test_clinical_routes_require_doctor_role_and_permission(
    route_name: str,
    permission_name: str,
) -> None:
    dependency = get_permission_dependency(
        get_route(route_name)
    )

    assert dependency.required_role_name == "doctor"
    assert (
        dependency.required_permission_name
        == permission_name
    )


def test_exam_list_remains_operational() -> None:
    dependency = get_permission_dependency(
        get_route("list_exams_route")
    )

    assert (
        getattr(
            dependency,
            "required_role_name",
            None,
        )
        is None
    )

    assert (
        dependency.required_permission_name
        == "exams:list"
    )
