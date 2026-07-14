"""Testes de regressão da matriz de acesso definida na RBAC-04."""

from fastapi.routing import APIRoute

from app.core.deps import require_admin
from app.modules.audit_logs.router import router as audit_logs_router
from app.modules.clinics.router import router as clinics_router
from app.modules.users.router import router as users_router


ADMIN_ONLY_ROUTES = (
    (clinics_router, "/clinics/", "POST"),
    (clinics_router, "/clinics/", "GET"),
    (clinics_router, "/clinics/{clinic_id}", "GET"),
    (clinics_router, "/clinics/{clinic_id}", "PATCH"),
    (clinics_router, "/clinics/{clinic_id}/inactivate", "PATCH"),
    (clinics_router, "/clinics/{clinic_id}/activate", "PATCH"),
    (users_router, "/users/", "POST"),
    (users_router, "/users/", "GET"),
    (users_router, "/users/{user_id}", "GET"),
    (users_router, "/users/{user_id}", "PATCH"),
    (users_router, "/users/{user_id}/password", "PATCH"),
    (users_router, "/users/{user_id}/inactivate", "PATCH"),
    (users_router, "/users/{user_id}/activate", "PATCH"),
    (audit_logs_router, "/audit-logs/", "GET"),
)


def find_route(router, path: str, method: str) -> APIRoute:
    """Localiza uma rota por caminho e método para inspecionar dependências."""

    return next(
        route
        for route in router.routes
        if isinstance(route, APIRoute)
        and route.path == path
        and method in route.methods
    )


def test_structural_modules_require_admin_master() -> None:
    """Impede que uma permissão delegada abra módulos administrativos."""

    for router, path, method in ADMIN_ONLY_ROUTES:
        route = find_route(router, path, method)
        dependencies = {dependency.call for dependency in route.dependant.dependencies}

        assert require_admin in dependencies, f"{method} {path} deve exigir require_admin"


def test_self_service_and_support_routes_are_not_admin_only() -> None:
    """Preserva perfil próprio e apoio ao cadastro de pacientes por permissão."""

    delegated_routes = (
        (clinics_router, "/clinics/me", "GET"),
        (clinics_router, "/clinics/me", "PATCH"),
        (users_router, "/users/me", "GET"),
        (users_router, "/users/me", "PATCH"),
        (users_router, "/users/me/password", "PATCH"),
        (users_router, "/users/doctors", "GET"),
    )

    for router, path, method in delegated_routes:
        route = find_route(router, path, method)
        dependencies = {dependency.call for dependency in route.dependant.dependencies}

        assert require_admin not in dependencies, f"{method} {path} deve continuar delegável"


def test_static_clinic_profile_routes_precede_dynamic_id_routes() -> None:
    """Evita que /clinics/me seja capturada por /clinics/{clinic_id}."""

    routes = [route for route in clinics_router.routes if isinstance(route, APIRoute)]

    for method in ("GET", "PATCH"):
        static_index = next(
            index
            for index, route in enumerate(routes)
            if route.path == "/clinics/me" and method in route.methods
        )
        dynamic_index = next(
            index
            for index, route in enumerate(routes)
            if route.path == "/clinics/{clinic_id}" and method in route.methods
        )

        assert static_index < dynamic_index
