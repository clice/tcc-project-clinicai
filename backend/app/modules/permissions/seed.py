"""Bootstrap e validação do catálogo fechado de permissões."""

from sqlalchemy.orm import Session

from app.modules.permissions.catalog import (
    OFFICIAL_PERMISSION_DEFINITIONS,
    OFFICIAL_PERMISSION_NAMES,
)
from app.modules.permissions.model import Permission


def _bootstrap_empty_catalog(db: Session) -> dict[str, Permission]:
    """Popula o catálogo completo somente quando a tabela está vazia."""

    permissions = {
        definition.name: Permission(
            name=definition.name,
            display_name=definition.display_name,
            description=definition.description,
            module=definition.module.value,
        )
        for definition in OFFICIAL_PERMISSION_DEFINITIONS
    }
    db.add_all(permissions.values())
    db.commit()

    for permission in permissions.values():
        db.refresh(permission)

    return permissions


def seed_permissions(db: Session) -> dict[str, Permission]:
    """Inicializa banco vazio ou valida um catálogo existente.

    Uma aplicação em atualização nunca cria permissões ausentes durante o
    startup. A ausência indica que a migration obrigatória não foi aplicada.
    """

    stored_permissions = db.query(Permission).all()

    if not stored_permissions:
        return _bootstrap_empty_catalog(db)

    stored_by_name = {permission.name: permission for permission in stored_permissions}
    missing_names = sorted(OFFICIAL_PERMISSION_NAMES - stored_by_name.keys())

    if missing_names:
        missing_list = ", ".join(missing_names)
        raise RuntimeError(
            "Catálogo oficial incompleto. Crie e aplique uma migration de dados "
            f"para as permissões ausentes: {missing_list}."
        )

    return {
        name: stored_by_name[name]
        for name in OFFICIAL_PERMISSION_NAMES
    }
