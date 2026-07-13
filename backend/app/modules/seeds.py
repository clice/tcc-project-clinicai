"""
Executor central dos seeds do sistema.

Este arquivo é responsável por chamar os arquivos seed.py
de cada módulo na ordem correta de dependência.
"""

from app.core.database import SessionLocal

from app.modules import models

from app.modules.statuses.seed import seed_statuses
from app.modules.roles.seed import seed_roles
from app.modules.permissions.seed import seed_permissions
from app.modules.role_permissions.seed import seed_role_permissions
from app.modules.clinics.seed import seed_clinics
from app.modules.users.seed import seed_users
from app.modules.patients.seed import seed_patients
from app.modules.exams.seed import seed_exams
from app.modules.ai_analysis.seed import seed_ai_analysis


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
        
        bootstrapped_roles = seed_role_permissions(db, roles, permissions)
        if bootstrapped_roles:
            print(
                "Role permissions inicializadas para: "
                + ", ".join(bootstrapped_roles)
                + "."
            )
        else:
            print(
                "Role permissions já configuradas; "
                "customizações administrativas preservadas."
            )
        
        clinics = seed_clinics(db, statuses)
        print("Clinics criadas/verificadas.")
        
        users = seed_users(db, roles, statuses, clinics)
        print("Users criados/verificados.")
        
        patients = seed_patients(db)
        print("Patients criados/verificados.")
        
        exams = seed_exams(db, clinics, patients, users, statuses)
        print("Exames criados/verificados.")
        
        seed_ai_analysis(db, exams)
        print("AI analysis criados/verificados.")

        print("Seeds executados com sucesso.")

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
