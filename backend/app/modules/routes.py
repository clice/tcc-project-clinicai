"""
Arquivo central de registro das rotas dos módulos.

Este arquivo concentra a inclusão dos routers da aplicação,
mantendo o main.py mais limpo e organizado.
"""

from fastapi import FastAPI

from app.modules.statuses.router import router as statuses_router
from app.modules.roles.router import router as roles_router
from app.modules.permissions.router import router as permissions_router
from app.modules.role_permissions.router import router as role_permissions_router
from app.modules.clinics.router import router as clinics_router
from app.modules.users.router import router as users_router


def register_routes(app: FastAPI) -> None:
    """
    Registra todas as rotas dos módulos da aplicação.
    """

    # Tabelas estruturais / administrativas
    app.include_router(statuses_router)
    app.include_router(roles_router)
    app.include_router(permissions_router)
    app.include_router(role_permissions_router)
    
    # Módulos de negócio
    app.include_router(clinics_router)
    app.include_router(users_router)
