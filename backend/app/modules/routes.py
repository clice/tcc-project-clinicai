"""
Arquivo central de registro das rotas dos módulos.

Este arquivo concentra a inclusão dos routers da aplicação,
mantendo o main.py mais limpo e organizado.
"""

from fastapi import FastAPI

from app.modules.roles.router import router as roles_router
from app.modules.statuses.router import router as statuses_router



def register_routes(app: FastAPI) -> None:
    """
    Registra todas as rotas dos módulos da aplicação.
    """

    # Tabelas estruturais / administrativas
    app.include_router(statuses_router)
    app.include_router(roles_router)
