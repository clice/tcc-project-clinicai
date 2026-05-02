"""
Arquivo principal da aplicação FastAPI.

Responsável por criar a instância da API, configurar CORS
e registrar as rotas do sistema.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.modules.routes import register_routes


app = FastAPI(
    title="ClinicAI Backend",
    version="0.1.0",
)

# Permite que o frontend React acesse a API durante o desenvolvimento.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routes(app)