"""Configuração compartilhada da suíte automatizada do backend."""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


# Valores locais e descartáveis tornam `pytest` independente de um arquivo
# .env e não substituem variáveis explicitamente fornecidas pelo ambiente.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "chave-descartavel-exclusiva-para-testes")
os.environ.setdefault("ALGORITHM", "HS256")

from app.core.database import Base  # noqa: E402
from app.modules import models  # noqa: E402, F401 - registra todos os mappers


@pytest.fixture
def db_session() -> Session:
    """Fornece um banco SQLite completo e isolado para cada teste."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)

    try:
        yield session
    finally:
        session.close()
        engine.dispose()
