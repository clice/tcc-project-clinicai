"""Testes de regressão dos catálogos fechados de perfis e status."""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.modules.roles.router import router as roles_router
from app.modules.roles.schema import RoleUpdate
from app.modules.statuses.router import router as statuses_router
from app.modules.statuses.schema import StatusUpdate


def route_methods(router) -> set[str]:
    """Retorna os métodos HTTP publicados por um router da aplicação."""

    return {
        method
        for route in router.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }


def test_role_and_status_routers_do_not_expose_creation() -> None:
    assert route_methods(roles_router) == {"GET", "PATCH"}
    assert route_methods(statuses_router) == {"GET", "PATCH"}


def test_role_and_status_updates_accept_only_presentation_fields() -> None:
    presentation_fields = {"display_name", "description"}

    assert set(RoleUpdate.model_fields) == presentation_fields
    assert set(StatusUpdate.model_fields) == presentation_fields


def test_openapi_announces_only_supported_catalog_operations() -> None:
    """Garante que o contrato público não volte a anunciar os POSTs removidos."""

    app = FastAPI()
    app.include_router(roles_router)
    app.include_router(statuses_router)
    paths = app.openapi()["paths"]

    assert set(paths["/roles/"]) == {"get"}
    assert set(paths["/roles/{role_id}"]) == {"get", "patch"}
    assert set(paths["/statuses/"]) == {"get"}
    assert set(paths["/statuses/{status_id}"]) == {"get", "patch"}
