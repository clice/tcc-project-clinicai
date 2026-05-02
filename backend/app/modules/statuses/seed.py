"""
Seed do módulo de statuses.

Este arquivo cadastra os status iniciais usados pelo sistema.
"""

from sqlalchemy.orm import Session

from app.modules.statuses.model import Status


def get_or_create_status(
    db: Session,
    name: str,
    display_name: str,
    applies_to: str,
    description: str | None = None,
) -> Status:
    """
    Busca um status existente ou cria um novo.
    Evita duplicação nos seeds.
    """
    status = (
        db.query(Status)
        .filter(
            Status.name == name,
            Status.applies_to == applies_to,
        )
        .first()
    )

    if status:
        return status

    status = Status(
        name=name,
        display_name=display_name,
        applies_to=applies_to,
        description=description,
    )

    db.add(status)
    db.commit()
    db.refresh(status)

    return status


def seed_statuses(db: Session) -> dict[str, Status]:
    """
    Cria os status iniciais do sistema.

    Retorna um dicionário para que outros seeds possam reutilizar
    esses registros, por exemplo no seed de usuários e clínicas.
    """

    return {
        "user_active": get_or_create_status(
            db,
            name="active",
            display_name="Ativo",
            applies_to="user",
            description="Usuário ativo no sistema",
        ),
        "user_inactive": get_or_create_status(
            db,
            name="inactive",
            display_name="Inativo",
            applies_to="user",
            description="Usuário inativo/arquivado no sistema",
        ),
        "clinic_active": get_or_create_status(
            db,
            name="active",
            display_name="Ativa",
            applies_to="clinic",
            description="Clínica ativa no sistema",
        ),
        "clinic_inactive": get_or_create_status(
            db,
            name="inactive",
            display_name="Inativa",
            applies_to="clinic",
            description="Clínica inativa no sistema",
        ),
        "patient_active": get_or_create_status(
            db,
            name="active",
            display_name="Ativo",
            applies_to="patient",
            description="Paciente ativo no sistema",
        ),
        "patient_inactive": get_or_create_status(
            db,
            name="inactive",
            display_name="Inativo",
            applies_to="patient",
            description="Paciente inativo/arquivado no sistema",
        ),
        "exam_pending": get_or_create_status(
            db,
            name="pending",
            display_name="Pendente",
            applies_to="exam",
            description="Exame cadastrado aguardando envio, análise ou revisão.",
        ),
        "exam_uploaded": get_or_create_status(
            db,
            name="uploaded",
            display_name="Arquivo enviado",
            applies_to="exam",
            description="Exame com arquivo enviado ao sistema.",
        ),
        "exam_processing": get_or_create_status(
            db,
            name="processing",
            display_name="Em processamento",
            applies_to="exam",
            description="Exame em processamento ou aguardando análise da IA.",
        ),
        "exam_analyzed": get_or_create_status(
            db,
            name="analyzed",
            display_name="Analisado",
            applies_to="exam",
            description="Exame analisado pela IA ou pela equipe médica.",
        ),
        "exam_reviewed": get_or_create_status(
            db,
            name="reviewed",
            display_name="Revisado",
            applies_to="exam",
            description="Exame revisado e validado por um médico.",
        ),
        "exam_canceled": get_or_create_status(
            db,
            name="canceled",
            display_name="Cancelado",
            applies_to="exam",
            description="Exame cancelado no sistema.",
        ),
        "exam_archived": get_or_create_status(
            db,
            name="archived",
            display_name="Arquivado",
            applies_to="exam",
            description="Exame arquivado, mantido apenas para histórico.",
        ),
    }