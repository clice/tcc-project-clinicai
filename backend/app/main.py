"""
Arquivo principal da aplicação FastAPI.

Responsável por criar a instância da API, configurar CORS
e registrar as rotas do sistema.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.modules.routes import register_routes


# ==================================================
# APP
# ==================================================

app = FastAPI(
    title="ClinicAI Backend",
    version="1.0.0",
    description="ClinicAI Backend API",
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# ROTAS BASE
# ==================================================

@app.get("/")
def root():
    return {
        "message": "ClinicAI Backend is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ClinicAI Backend",
    }


register_routes(app)
