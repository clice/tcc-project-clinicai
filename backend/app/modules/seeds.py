"""
Executor central dos seeds do sistema.

Este arquivo é responsável por chamar os arquivos seed.py
de cada módulo na ordem correta de dependência.
"""

from app.core.database import SessionLocal

from app.modules.statuses.seed import seed_statuses
from app.modules.roles.seed import seed_roles
from app.modules.permissions.seed import seed_permissions


def run_seed() -> None:
    """
    Executa todos os seeds do sistema.
    """

    db = SessionLocal()

    try:
        print("Iniciando seed...")
        
        # Base inicial do sistema        
        seed_statuses(db)
        print("Statuses criados/verificados.")
        
        seed_roles(db)
        print("Roles criados/verificados.")
        
        seed_permissions(db)
        print("Permissions criadas/verificadas.")

        print("Seeds executados com sucesso.")

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()