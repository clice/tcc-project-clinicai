"""Matriz executável de perfis versus todas as rotas protegidas."""

from dataclasses import dataclass

from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.core.deps import get_current_user, require_admin
from app.main import app
from app.modules.permissions.catalog import OFFICIAL_PERMISSION_NAMES
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.role_permissions.seed import (
    CLINIC_MANAGER_PERMISSIONS,
    DOCTOR_PERMISSIONS,
)
from app.modules.roles.model import Role
from app.modules.users.model import User


PUBLIC_ROUTES = {
    ("GET", "/"),
    ("GET", "/health"),
    ("POST", "/auth/login"),
    ("POST", "/auth/refresh"),
}

ROLE_PERMISSIONS = {
    "admin_master": OFFICIAL_PERMISSION_NAMES,
    "doctor": set(DOCTOR_PERMISSIONS),
    "clinic_manager": set(CLINIC_MANAGER_PERMISSIONS),
}


@dataclass(frozen=True)
class AccessRule:
    kind: str
    dependency: object
    permission_name: str | None = None
    role_name: str | None = None


def build_user(role_name: str) -> User:
    """Monta uma role com sua matriz padrão para exercitar as dependências."""

    role = Role(name=role_name, display_name=role_name)
    role.role_permissions = [
        RolePermission(
            permission=Permission(
                name=permission_name,
                display_name=permission_name,
                module=permission_name.split(":", 1)[0],
            )
        )
        for permission_name in ROLE_PERMISSIONS[role_name]
    ]
    return User(role=role)


def resolve_access_rule(route: APIRoute) -> AccessRule:
    """Extrai a barreira de autorização declarada diretamente na rota."""

    rules: list[AccessRule] = []
    for dependency in route.dependant.dependencies:
        call = dependency.call
        permission_name = getattr(call, "required_permission_name", None)
        required_role = getattr(call, "required_role_name", None)

        if call is require_admin:
            rules.append(AccessRule("admin", call, role_name="admin_master"))
        elif call is get_current_user:
            rules.append(AccessRule("authenticated", call))
        elif permission_name:
            rules.append(
                AccessRule(
                    "doctor_permission" if required_role else "permission",
                    call,
                    permission_name=permission_name,
                    role_name=required_role,
                )
            )

    assert len(rules) == 1, (
        f"{','.join(sorted(route.methods))} {route.path} deve declarar "
        "exatamente uma política de autorização."
    )
    return rules[0]


def is_allowed(rule: AccessRule, role_name: str) -> bool:
    """Executa a dependência real e informa se a role foi autorizada."""

    if rule.kind == "authenticated":
        return True

    try:
        rule.dependency(build_user(role_name))
    except HTTPException as exc:
        assert exc.status_code == 403
        return False
    return True


def expected_access(rule: AccessRule, role_name: str) -> bool:
    if rule.kind == "authenticated":
        return True
    if rule.kind == "admin":
        return role_name == "admin_master"
    if rule.kind == "doctor_permission":
        return (
            role_name == rule.role_name
            and rule.permission_name in ROLE_PERMISSIONS[role_name]
        )
    return (
        role_name == "admin_master"
        or rule.permission_name in ROLE_PERMISSIONS[role_name]
    )


def protected_routes() -> list[APIRoute]:
    routes = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = route.methods - {"HEAD", "OPTIONS"}
        if all((method, route.path) in PUBLIC_ROUTES for method in methods):
            continue
        routes.append(route)
    return routes


def test_every_non_public_route_has_an_explicit_access_policy() -> None:
    """Faz uma rota nova e desprotegida falhar automaticamente na suíte."""

    routes = protected_routes()

    assert routes
    for route in routes:
        rule = resolve_access_rule(route)
        if rule.permission_name:
            assert rule.permission_name in OFFICIAL_PERMISSION_NAMES


def test_every_role_matches_the_policy_of_every_protected_route() -> None:
    """Executa a matriz completa usando as dependências registradas no FastAPI."""

    for route in protected_routes():
        rule = resolve_access_rule(route)
        for role_name in ROLE_PERMISSIONS:
            assert is_allowed(rule, role_name) is expected_access(rule, role_name), (
                f"Matriz divergente para {role_name} em "
                f"{','.join(sorted(route.methods))} {route.path}."
            )
