"""
Model da tabela de pacientes.

A tabela patients armazena os dados dos pacientes vinculados às clínicas.
Pacientes não devem ser excluídos fisicamente, apenas inativados por status.
"""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Patient(Base):
    """
    Model ORM da tabela de pacientes.
    """

    __tablename__ = "patients"

    # Evita que o mesmo CPF seja cadastrado mais de uma vez na mesma clínica.
    __table_args__ = (
        UniqueConstraint("clinic_id", "cpf", name="uq_patient_clinic_cpf"),
    )

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    # Dados principais do paciente
    name = Column(String(150), nullable=False, index=True)
    cpf = Column(String(11), nullable=False, index=True)
    birth_date = Column(Date, nullable=True)
    sex = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(150), nullable=True)

    zip_code = Column(String(8), nullable=True)
    address = Column(String(255), nullable=True)
    number = Column(String(20), nullable=True)
    complement = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)

    # Relacionamentos principais
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False, index=True)

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
    clinic = relationship("Clinic", back_populates="patients")
    doctor = relationship("User", foreign_keys=[doctor_id])
    status = relationship("Status", back_populates="patients")
    exams = relationship("Exam", back_populates="patient")


    def __repr__(self):
        """
        Representação textual útil para debug.
        """
        return f"<Patient(id={self.id}, name='{self.name}', cpf='{self.cpf}')>"
