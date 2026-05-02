"""
Model da tabela de permissões do sistema.

A tabela permissions define as ações que podem ser executadas
dentro do sistema, como criar usuários, visualizar clínicas ou atualizar exames.
"""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Permission(Base):
    """
    Model ORM da tabela de permissions.
    """

    __tablename__ = "permissions"

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    module = Column(String(50), nullable=False, index=True)

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

    # Relacionamento com a tabela associativa role_permissions.
    role_permissions = relationship(
        "RolePermission",
        back_populates="permission",
    )


    def __repr__(self):
        """
        Representação textual útil para debug.
        """
        return f"<Permission(id={self.id}, name='{self.name}')>"
