"""
Centraliza a configuração de acesso ao banco de dados.

Este arquivo define a engine de conexão com o banco, a fábrica de sessões do SQLAlchemy,
a classe Base usada pelos models ORM e a dependência get_db() para uso nas rotas do FastAPI
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Cria a engine principal de conexão com o banco de dados.
# A engine é o ponto central de comunicação entre a aplicação e o PostgreSQL.
engine = create_engine(settings.database_url)

# Cria a fábrica de sessões do SQLAlchemy.
# Cada sessão representa uma conversa temporária com o banco.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Classe base que será herdada por todos os models ORM do projeto.
Base = declarative_base()


def get_db():
    """
    Fornece uma sessão do banco para uso nas rotas do FastAPI.    
    Ela abre uma sessão no início da requisição e garante o fechamento ao final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()