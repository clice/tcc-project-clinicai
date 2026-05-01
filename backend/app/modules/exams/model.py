"""
Model da tabela de exames.

A tabela exams armazena exames vinculados a pacientes, clínicas e médicos.
Também guarda informações clínicas, arquivo enviado e status da análise por IA.
"""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Exam(Base):
    """
    Model ORM da tabela de exames.
    """

    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)

    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False, index=True)

    exam_type = Column(String(80), nullable=False, index=True)
    exam_date = Column(Date, nullable=True)

    title = Column(String(180), nullable=False)
    description = Column(Text, nullable=True)
    clinical_indication = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)

    ai_analysis_status = Column(String(50), nullable=True)
    ai_summary = Column(Text, nullable=True)

    file_path = Column(String(255), nullable=True)
    file_name = Column(String(180), nullable=True)
    file_mime_type = Column(String(100), nullable=True)

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

    clinic = relationship("Clinic", back_populates="exams")
    patient = relationship("Patient", back_populates="exams")
    doctor = relationship("User", foreign_keys=[doctor_id])
    status = relationship("Status", back_populates="exams")


    def __repr__(self):
        return (
            f"<Exam(id={self.id}, title='{self.title}', "
            f"exam_type='{self.exam_type}', patient_id={self.patient_id})>"
        )