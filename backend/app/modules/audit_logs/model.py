"""
Model da tabela de logs de auditoria do sistema.

A tabela audit_logs armazena registros de ações importantes realizadas
no ClinicAI, permitindo rastrear alterações, acessos e eventos relevantes.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AuditLog(Base):
    """
    Model ORM da tabela audit_logs.
    """

    __tablename__ = "audit_logs"

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    # Campos da tabela
    action = Column(String(100), nullable=False, index=True)
    entity = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True, index=True)

    description = Column(Text, nullable=True)

    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)

    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relacionamento principal
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=True, index=True)

    # Data de criação do log
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamentos ORM
    user = relationship("User", back_populates="audit_logs")
    clinic = relationship("Clinic", back_populates="audit_logs")


    def __repr__(self):
        """
        Representação textual útil para debug.
        """
        return (
            f"<AuditLog(id={self.id}, action='{self.action}', "
            f"entity='{self.entity}', entity_id={self.entity_id})>"
        )
