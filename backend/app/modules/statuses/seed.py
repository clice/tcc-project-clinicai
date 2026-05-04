"""
Seed do módulo de statuses.

Este arquivo cadastra apenas os status oficiais definidos em constants.py.
"""

from sqlalchemy.orm import Session

from app.common.constants import StatusName, StatusScope
from app.modules.statuses.model import Status


def get_or_create_status(
    db: Session,
    name: StatusName,
    display_name: str,
    applies_to: StatusScope,
    description: str | None = None,
) -> Status:
    status = (
        db.query(Status)
        .filter(
            Status.name == name.value,
            Status.applies_to == applies_to.value,
        )
        .first()
    )

    if status:
        return status

    status = Status(
        name=name.value,
        display_name=display_name,
        applies_to=applies_to.value,
        description=description,
    )

    db.add(status)
    db.commit()
    db.refresh(status)

    return status


def seed_statuses(db: Session) -> dict[str, Status]:
    """
    Cria os status iniciais oficiais do sistema.
    """

    return {
        # Users
        "user_active": get_or_create_status(
            db,
            name=StatusName.ACTIVE,
            display_name="Ativo",
            applies_to=StatusScope.USER,
            description="Usuário ativo no sistema.",
        ),
        "user_inactive": get_or_create_status(
            db,
            name=StatusName.INACTIVE,
            display_name="Inativo",
            applies_to=StatusScope.USER,
            description="Usuário inativo no sistema.",
        ),

        # Clinics
        "clinic_active": get_or_create_status(
            db,
            name=StatusName.ACTIVE,
            display_name="Ativa",
            applies_to=StatusScope.CLINIC,
            description="Clínica ativa no sistema.",
        ),
        "clinic_inactive": get_or_create_status(
            db,
            name=StatusName.INACTIVE,
            display_name="Inativa",
            applies_to=StatusScope.CLINIC,
            description="Clínica inativa no sistema.",
        ),

        # Patients
        "patient_active": get_or_create_status(
            db,
            name=StatusName.ACTIVE,
            display_name="Ativo",
            applies_to=StatusScope.PATIENT,
            description="Paciente ativo no sistema.",
        ),
        "patient_inactive": get_or_create_status(
            db,
            name=StatusName.INACTIVE,
            display_name="Inativo",
            applies_to=StatusScope.PATIENT,
            description="Paciente inativo no sistema.",
        ),

        # Exams
        "exam_pending": get_or_create_status(
            db,
            name=StatusName.PENDING,
            display_name="Pendente",
            applies_to=StatusScope.EXAM,
            description="Exame cadastrado e aguardando processamento.",
        ),
        "exam_processing": get_or_create_status(
            db,
            name=StatusName.PROCESSING,
            display_name="Em processamento",
            applies_to=StatusScope.EXAM,
            description="Exame em processamento ou análise.",
        ),
        "exam_completed": get_or_create_status(
            db,
            name=StatusName.COMPLETED,
            display_name="Concluído",
            applies_to=StatusScope.EXAM,
            description="Exame concluído.",
        ),
        "exam_canceled": get_or_create_status(
            db,
            name=StatusName.CANCELED,
            display_name="Cancelado",
            applies_to=StatusScope.EXAM,
            description="Exame cancelado.",
        ),
        "exam_failed": get_or_create_status(
            db,
            name=StatusName.FAILED,
            display_name="Falhou",
            applies_to=StatusScope.EXAM,
            description="Exame com erro no processamento.",
        ),

        # AI Analysis
        "ai_analysis_pending": get_or_create_status(
            db,
            name=StatusName.PENDING,
            display_name="Pendente",
            applies_to=StatusScope.AI_ANALYSIS,
            description="Análise de IA aguardando processamento.",
        ),
        "ai_analysis_processing": get_or_create_status(
            db,
            name=StatusName.PROCESSING,
            display_name="Processando",
            applies_to=StatusScope.AI_ANALYSIS,
            description="Análise de IA em processamento.",
        ),
        "ai_analysis_completed": get_or_create_status(
            db,
            name=StatusName.COMPLETED,
            display_name="Concluída",
            applies_to=StatusScope.AI_ANALYSIS,
            description="Análise de IA concluída.",
        ),
        "ai_analysis_failed": get_or_create_status(
            db,
            name=StatusName.FAILED,
            display_name="Falhou",
            applies_to=StatusScope.AI_ANALYSIS,
            description="Análise de IA com falha.",
        ),
    }