"""
Model da tabela de clínicas.

Este arquivo define a estrutura ORM da tabela clinics.
A clínica representa uma unidade cadastrada no sistema e poderá ter usuários,
pacientes e exames vinculados futuramente.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Clinic(Base):
    """
    Model ORM da tabela clinics.
    """

    __tablename__ = "clinics"

    # Garante que não exista o mesmo CNPJ e e-mail repetido para a mesma entidade.
    __table_args__ = (
        UniqueConstraint("cnpj", name="uq_clinics_cnpj"),
        UniqueConstraint("email", name="uq_clinics_email"),
    )

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    # Campos da tabela
    name = Column(String(180), nullable=False, index=True)
    cnpj = Column(String(14), nullable=False, index=True)
    email = Column(String(150), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    mobile_phone = Column(String(20), nullable=True)

    zip_code = Column(String(8), nullable=True)
    address = Column(String(255), nullable=True)
    number = Column(String(20), nullable=True)
    complement = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)

    # Relacionamento principal
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False)

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
    status = relationship("Status", back_populates="clinics")
    users = relationship("User", back_populates="clinic")
    patients = relationship("Patient", back_populates="clinic")
    exams = relationship("Exam", back_populates="clinic")


    def __repr__(self):
        return f"<Clinic(id={self.id}, name='{self.name}', cnpj='{self.cnpj}')>"