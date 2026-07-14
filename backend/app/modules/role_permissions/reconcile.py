"""Comando explícito para restaurar a matriz RBAC padrão.

Uso consciente:
    python -m app.modules.role_permissions.reconcile --confirm RECONCILE_RBAC

O comando pode remover customizações administrativas. Ele não é chamado pelo
entrypoint nem pelo executor de seeds.
"""

import argparse
import logging

from app.core.database import SessionLocal
from app.modules.permissions.model import Permission
from app.modules.role_permissions.seed import reconcile_role_permissions
from app.modules.roles.model import Role


CONFIRMATION_TEXT = "RECONCILE_RBAC"
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Substitui as permissões atuais das roles pela matriz padrão. "
            "Esta operação pode remover customizações administrativas."
        )
    )
    parser.add_argument(
        "--confirm",
        required=True,
        help=f"Confirmação obrigatória: {CONFIRMATION_TEXT}",
    )
    args = parser.parse_args()
    if args.confirm != CONFIRMATION_TEXT:
        parser.error(f"confirmação inválida; informe --confirm {CONFIRMATION_TEXT}")
    return args


def main() -> None:
    parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    db = SessionLocal()
    try:
        roles = {role.name: role for role in db.query(Role).all()}
        permissions = {
            permission.name: permission for permission in db.query(Permission).all()
        }
        logger.warning(
            "Iniciando reconciliação explícita da matriz RBAC; "
            "customizações administrativas podem ser removidas."
        )
        results = reconcile_role_permissions(db, roles, permissions)
        for result in results:
            logger.info(
                "role=%s adicionadas=%d removidas=%d",
                result.role_name,
                result.added,
                result.removed,
            )
        logger.info("Reconciliação RBAC concluída com sucesso.")
    except Exception:
        logger.exception("Reconciliação RBAC falhou e foi revertida.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
