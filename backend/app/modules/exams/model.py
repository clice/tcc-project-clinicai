"""
Model da tabela de exames.

A tabela exams armazena exames vinculados a pacientes, clínicas e médicos,
além dos metadados do arquivo enviado.
"""

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Exam(Base):
    """
    Model ORM da tabela de exames.
    """

    __tablename__ = "exams"

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    # Campos da tabela
    exam_type = Column(String(80), nullable=False, index=True)
    exam_date = Column(Date, nullable=True)

    description = Column(String(180), nullable=False)
    observations = Column(Text, nullable=True)
    clinical_indication = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)

    file_path = Column(String(255), nullable=True)
    file_name = Column(String(180), nullable=True)
    file_mime_type = Column(String(100), nullable=True)

    # Relacionamentos principais
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False, index=True)

    # Controle de concorrência da análise de IA
    analysis_in_progress = Column(Boolean, nullable=False, default=False, server_default="false")
    analysis_started_at = Column(DateTime(timezone=True), nullable=True)

    # Revisão médica do resultado da IA
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

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
    clinic = relationship("Clinic", back_populates="exams")
    patient = relationship("Patient", back_populates="exams")
    doctor = relationship("User", foreign_keys=[doctor_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    status = relationship("Status", back_populates="exams")

    ai_analysis = relationship(
        "AIAnalysis",
        back_populates="exam",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        """
        Representação textual útil para debug.
        """
        return (
            f"<Exam(id={self.id}, description='{self.description}', "
            f"exam_type='{self.exam_type}', patient_id={self.patient_id})>"
        )
