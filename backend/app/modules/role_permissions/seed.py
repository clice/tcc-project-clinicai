"""Bootstrap e reconciliação da matriz de permissões por role.

O seed executado na inicialização é deliberadamente não destrutivo: ele
preenche apenas roles que ainda não têm nenhum vínculo. Depois do bootstrap,
a matriz passa a ser configuração administrativa e não pode ser sobrescrita
por uma reinicialização da aplicação.

Mudanças oficiais em bancos existentes devem ser feitas por migrations de
dados. A reconciliação integral existe apenas para o comando administrativo
explícito ``python -m app.modules.role_permissions.reconcile``.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.roles.model import Role


DOCTOR_PERMISSIONS = [
    "users:read_profile",
    "users:update_profile",
    "clinics:read_profile",
    "clinics:update_profile",
    "patients:create",
    "patients:read",
    "patients:update",
    "patients:change_status",
    "exams:create",
    "exams:read",
    "exams:update",
    "exams:upload",
    "exams:download",
    "exams:change_status",
    "exams:review",
    "ai_analysis:create",
    "ai_analysis:read",
    "ai_analysis:update",
]

CLINIC_STAFF_PERMISSIONS = [
    "users:read_profile",
    "users:update_profile",
    "clinics:read_profile",
    "clinics:update_profile",
    "patients:create",
    "patients:read",
    "patients:update",
    "patients:change_status",
]


@dataclass(frozen=True)
class ReconciliationResult:
    """Resumo auditável de uma reconciliação explícita."""

    role_name: str
    added: int
    removed: int


def build_role_permission_map(
    permissions: dict[str, Permission],
) -> dict[str, list[str]]:
    """Monta a matriz padrão usada no primeiro bootstrap e no comando manual."""

    return {
        "admin_master": list(permissions.keys()),
        "doctor": DOCTOR_PERMISSIONS,
        "clinic_staff": CLINIC_STAFF_PERMISSIONS,
    }


def _resolve_permissions(
    role: Role,
    permissions: dict[str, Permission],
    permission_names: list[str],
) -> dict[str, Permission]:
    """Resolve e valida todos os nomes referenciados pela matriz padrão."""

    resolved: dict[str, Permission] = {}
    for permission_name in permission_names:
        permission = permissions.get(permission_name)
        if permission is None:
            raise ValueError(
                f"Permissão '{permission_name}' referenciada para a role "
                f"'{role.name}' não existe no catálogo de permissions. "
                "Corrija a matriz ou adicione a permissão ao catálogo."
            )
        resolved[permission_name] = permission
    return resolved


def bootstrap_permissions_for_role(
    db: Session,
    role: Role,
    permissions: dict[str, Permission],
    permission_names: list[str],
) -> bool:
    """Preenche uma role somente quando ela ainda não possui configuração.

    Retorna ``True`` quando o bootstrap foi aplicado e ``False`` quando a role
    já foi inicializada. O marcador persistente permite preservar inclusive
    uma matriz intencionalmente esvaziada pelo administrador.
    """

    desired = _resolve_permissions(role, permissions, permission_names)
    if role.permissions_initialized:
        return False

    for permission in desired.values():
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    role.permissions_initialized = True
    db.add(role)
    return True


def seed_role_permissions(
    db: Session,
    roles: dict[str, Role],
    permissions: dict[str, Permission],
) -> list[str]:
    """Executa apenas o bootstrap inicial das roles sem configuração.

    A função é segura para ser executada em toda inicialização: roles que já
    possuem vínculos não são reconciliadas com a matriz padrão. Evoluções de
    dados pertencem a migrations Alembic.
    """

    bootstrapped_roles: list[str] = []
    for role_name, permission_names in build_role_permission_map(permissions).items():
        role = roles.get(role_name)
        if role is None:
            continue
        if bootstrap_permissions_for_role(
            db, role, permissions, permission_names
        ):
            bootstrapped_roles.append(role_name)

    db.commit()
    return bootstrapped_roles


def reconcile_permissions_for_role(
    db: Session,
    role: Role,
    permissions: dict[str, Permission],
    permission_names: list[str],
) -> ReconciliationResult:
    """Reconcilia uma role; uso exclusivo do comando administrativo manual."""

    desired = _resolve_permissions(role, permissions, permission_names)
    current_links = (
        db.query(RolePermission)
        .filter(RolePermission.role_id == role.id)
        .all()
    )
    current_ids = {link.permission_id for link in current_links}
    desired_ids = {permission.id for permission in desired.values()}

    ids_to_remove = current_ids - desired_ids
    ids_to_add = desired_ids - current_ids

    if ids_to_remove:
        (
            db.query(RolePermission)
            .filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id.in_(ids_to_remove),
            )
            .delete(synchronize_session=False)
        )
    for permission_id in ids_to_add:
        db.add(RolePermission(role_id=role.id, permission_id=permission_id))

    role.permissions_initialized = True
    db.add(role)

    return ReconciliationResult(
        role_name=role.name,
        added=len(ids_to_add),
        removed=len(ids_to_remove),
    )


def reconcile_role_permissions(
    db: Session,
    roles: dict[str, Role],
    permissions: dict[str, Permission],
) -> list[ReconciliationResult]:
    """Reconcilia toda a matriz em uma transação controlada."""

    results: list[ReconciliationResult] = []
    try:
        for role_name, permission_names in build_role_permission_map(permissions).items():
            role = roles.get(role_name)
            if role is None:
                continue
            results.append(
                reconcile_permissions_for_role(
                    db, role, permissions, permission_names
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return results
