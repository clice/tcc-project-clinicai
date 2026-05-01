"""
Model da tabela de usuários do sistema.

A tabela users armazena os usuários que acessam o ClinicAI,
incluindo administradores, médicos e funcionários vinculados a clínicas.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    Model ORM da tabela users.
    """

    __tablename__ = "users"

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    # Campos da tabela
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    cpf = Column(String(11), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)

    # Segurança
    password_hash = Column(String(255), nullable=False)

    # Relacionamentos principais
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=True, index=True)

    # Controle de acesso
    last_access_at = Column(DateTime(timezone=True), nullable=True)

    # Datas de auditoria
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relacionamentos ORM
    role = relationship("Role", back_populates="users")
    status = relationship("Status", back_populates="users")
    clinic = relationship("Clinic", back_populates="users")


    def __repr__(self):
        """
        Representação textual útil para debug.
        """
        return f"<User(id={self.id}, email='{self.email}')>"