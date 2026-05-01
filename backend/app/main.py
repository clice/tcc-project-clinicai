"""
Arquivo principal da aplicação FastAPI.

Responsável por criar a instância da API, configurar CORS
e registrar as rotas do sistema.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


app = FastAPI(
    title="ClinicAI Backend",
    version="0.1.0",
)