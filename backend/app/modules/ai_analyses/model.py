"""
Model da tabela de análises de IA.

A tabela ai_analyses armazena os resultados gerados pelo modelo de IA
para exames médicos enviados ao sistema.
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AIAnalysis(Base):
    """
    Model ORM da tabela de análises de IA.
    """

    __tablename__ = "ai_analyses"

    # Chave primária
    id = Column(Integer, primary_key=True, index=True)

    # Campos da tabela
    prediction_label = Column(String(80), nullable=False)
    prediction_class = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=False)

    model_name = Column(String(120), nullable=False)
    model_version = Column(String(50), nullable=False)

    gradcam_path = Column(String(255), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    ai_notes = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    
    # Relacionamento principal
    exam_id = Column(
        Integer,
        ForeignKey("exams.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    status_id = Column(
        Integer,
        ForeignKey("statuses.id"),
        nullable=False,
        index=True,
    )

    # Chave primária
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
    exam = relationship("Exam", back_populates="ai_analysis")
    status = relationship("Status")


    def __repr__(self):
        """
        Representação textual útil para debug.
        """
        return (
            f"<AIAnalysis(id={self.id}, exam_id={self.exam_id}, "
            f"prediction_label='{self.prediction_label}', confidence={self.confidence})>"
        )