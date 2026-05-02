"""
Executor central dos seeds do sistema.

Este arquivo é responsável por chamar os arquivos seed.py
de cada módulo na ordem correta de dependência.
"""

from app.core.database import SessionLocal

from app.modules.statuses.seed import seed_statuses
from app.modules.roles.seed import seed_roles
from app.modules.permissions.seed import seed_permissions
from app.modules.role_permissions.seed import seed_role_permissions
from app.modules.clinics.seed import seed_clinics
from app.modules.users.seed import seed_users
from app.modules.patients.seed import seed_patients


def run_seed() -> None:
    """
    Executa todos os seeds do sistema.
    """

    db = SessionLocal()

    try:
        print("Iniciando seed...")
        
        # Base inicial do sistema        
        statuses = seed_statuses(db)
        print("Statuses criados/verificados.")
        
        roles = seed_roles(db)
        print("Roles criados/verificados.")
        
        permissions = seed_permissions(db)
        print("Permissions criadas/verificadas.")
        
        seed_role_permissions(db, roles, permissions)
        print("Role permissions criadas/verificadas.")
        
        seed_clinics(db, statuses)
        print("Clinics criadas/verificadas.")
        
        seed_users(db)
        print("Users criados/verificados.")
        
        seed_patients(db)
        print("Patients criados/verificados.")

        print("Seeds executados com sucesso.")

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()