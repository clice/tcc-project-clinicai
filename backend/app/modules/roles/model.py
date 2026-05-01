"""
Model da tabela de perfis de acesso do sistema.

A tabela roles define os perfis principais de usuários,
como administrador master, administrador da clínica, médico e funcionário.
"""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Role(Base):
    """
    Model ORM da tabela de roles.
    """

    __tablename__ = "roles"

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

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

    # Relacionamentos com outras tabelas do sistema
    users = relationship("User", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role")


    def __repr__(self):
        """
        Representação textual útil para debug.
        """
        return f"<Role(id={self.id}, name='{self.name}')>"