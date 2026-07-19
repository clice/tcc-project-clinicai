"""Testes da autorização não delegável para revisão médica."""

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.core.deps import require_doctor_permission
from app.modules.exams.router import router as exams_router
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.roles.model import Role
from app.modules.users.model import User


REVIEW_PERMISSION = "exams:review"


def build_user(role_name: str, permission_names: list[str]) -> User:
    """Monta usuário sem persistência para exercitar a dependência."""

    role = Role(name=role_name, display_name=role_name)
    role.role_permissions = [
        RolePermission(
            permission=Permission(
                name=permission_name,
                display_name=permission_name,
                module="exams",
            )
        )
        for permission_name in permission_names
    ]
    return User(role=role)


def get_review_dependency():
    """Localiza a dependência clínica registrada na rota de revisão."""

    route = next(
        route
        for route in exams_router.routes
        if isinstance(route, APIRoute)
        and route.path == "/exams/{exam_id}/review"
        and "PATCH" in route.methods
    )
    return next(
        dependency.call
        for dependency in route.dependant.dependencies
        if getattr(dependency.call, "required_permission_name", None)
        == REVIEW_PERMISSION
    )


def test_review_route_requires_doctor_and_review_permission() -> None:
    """Confirma a regra combinada publicada pela rota FastAPI."""

    dependency = get_review_dependency()

    assert dependency.required_role_name == "doctor"
    assert dependency.required_permission_name == REVIEW_PERMISSION


def test_doctor_with_review_permission_is_authorized() -> None:
    """Médico com a permissão clínica pode prosseguir para a regra do exame."""

    doctor = build_user("doctor", [REVIEW_PERMISSION])
    dependency = require_doctor_permission(REVIEW_PERMISSION)

    assert dependency(doctor) is doctor


@pytest.mark.parametrize("role_name", ["clinic_staff", "admin_master"])
def test_non_doctor_is_forbidden_even_with_review_permission(role_name: str) -> None:
    """Conceder a permissão manualmente não transforma a role em médica."""

    user = build_user(role_name, [REVIEW_PERMISSION])
    dependency = require_doctor_permission(REVIEW_PERMISSION)

    with pytest.raises(HTTPException) as exc_info:
        dependency(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "Apenas usuários com perfil médico podem executar ações clínicas de exames."
    )


def test_doctor_without_review_permission_is_forbidden() -> None:
    """A role médica não substitui a concessão explícita da permissão."""

    doctor = build_user("doctor", [])
    dependency = require_doctor_permission(REVIEW_PERMISSION)

    with pytest.raises(HTTPException) as exc_info:
        dependency(doctor)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Permissão 'exams:review' necessária."
