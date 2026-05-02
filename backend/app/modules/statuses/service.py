"""
Service do módulo de statuses.

Aqui ficam as regras de negócio e operações com o banco.
O router deve ficar mais limpo e apenas chamar essas funções.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.statuses.model import Status
from app.modules.statuses.schema import StatusCreate, StatusUpdate


def get_status_by_id_and_applies_to(
    db: Session,
    status_id: int,
    applies_to: str,
) -> Status:
    """
    Busca um status pelo ID e valida se pertence ao contexto esperado.

    Exemplo:
    - status de user
    - status de clinic
    - status de patient
    """
    status = get_status_by_id(db=db, status_id=status_id)

    if status.applies_to != applies_to:
        raise HTTPException(
            status_code=400,
            detail=f"Status inválido para {applies_to}.",
        )

    return status


def get_status_by_name_and_applies_to(
    db: Session,
    name: str,
    applies_to: str,
) -> Status:
    """
    Busca um status pelo nome interno e contexto.
    """
    status = (
        db.query(Status)
        .filter(
            Status.name == name,
            Status.applies_to == applies_to,
        )
        .first()
    )

    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Status '{name}' para '{applies_to}' não encontrado.",
        )

    return status


def check_status_duplicate(
    db: Session,
    name: str,
    applies_to: str,
    ignore_status_id: int | None = None,
) -> None:
    """
    Verifica se já existe outro status com o mesmo name e applies_to.
    """
    query = db.query(Status).filter(
        Status.name == name,
        Status.applies_to == applies_to,
    )

    if ignore_status_id is not None:
        query = query.filter(Status.id != ignore_status_id)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="Já existe um status com esse nome para essa referência.",
        )


def get_status_by_id(db: Session, status_id: int) -> Status:
    """
    Busca um status pelo ID.
    """
    status = db.query(Status).filter(Status.id == status_id).first()

    if not status:
        raise HTTPException(status_code=404, detail="Status não encontrado.")

    return status


def list_statuses(db: Session) -> list[Status]:
    """
    Lista todos os statuses cadastrados.
    """
    return (
        db.query(Status)
        .order_by(Status.applies_to.asc(), Status.display_name.asc())
        .all()
    )


def create_status(db: Session, payload: StatusCreate) -> Status:
    """
    Cria um novo status.
    """
    check_status_duplicate(
        db=db,
        name=payload.name,
        applies_to=payload.applies_to,
    )

    status = Status(
        name=payload.name,
        display_name=payload.display_name,
        applies_to=payload.applies_to,
        description=payload.description,
    )

    db.add(status)
    db.commit()
    db.refresh(status)

    return status


def update_status(
    db: Session,
    status_id: int,
    payload: StatusUpdate,
) -> Status:
    """
    Atualiza parcialmente um status.
    """
    status = get_status_by_id(db=db, status_id=status_id)
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return status

    new_name = update_data.get("name", status.name)
    new_applies_to = update_data.get("applies_to", status.applies_to)

    check_status_duplicate(
        db=db,
        name=new_name,
        applies_to=new_applies_to,
        ignore_status_id=status_id,
    )

    for field, value in update_data.items():
        setattr(status, field, value)

    db.commit()
    db.refresh(status)

    return status
