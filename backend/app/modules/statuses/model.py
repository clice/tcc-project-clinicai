"""
Model da tabela de status do sistema.

A tabela statuses centraliza os possíveis estados dos registros
de diferentes módulos do sistema.
"""

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class Status(Base):
    """
    Model ORM da tabela de statuses.
    """

    __tablename__ = "statuses"

    # Garante que não exista o mesmo status repetido para a mesma entidade.
    __table_args__ = (
        UniqueConstraint("name", "applies_to", name="uq_status_name_applies_to"),
    )

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)
    
    # Campos da tabela
    name = Column(String(50), nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    applies_to = Column(String(50), nullable=False, index=True)
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
    

    def __repr__(self):
        """
        Representação textual útil para debug.
        """
        return f"<Status(id={self.id}, name='{self.name}', applies_to='{self.applies_to}')>"