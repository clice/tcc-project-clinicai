"""
Repository do módulo de statuses.

Responsável exclusivamente pelo acesso ao banco de dados.
NÃO deve conter regras de negócio.
"""

from sqlalchemy.orm import Session

from app.modules.statuses.model import Status


# ========================================
# UTILITARIAS
# ========================================

def exists_status(
    db: Session,
    name: str,
    applies_to: str,
    ignore_status_id: int | None = None,
) -> bool:
    """
    Verifica existência de status duplicado.
    ignore_status_id:
    - usado em updates para ignorar o próprio registro.
    """    
    query = db.query(Status).filter(
        Status.name == name,
        Status.applies_to == applies_to,
    )

    if ignore_status_id is not None:
        query = query.filter(Status.id != ignore_status_id)

    return query.first() is not None


def get_status_by_id(db: Session, status_id: int) -> Status | None:
    """
    Busca um status pelo ID.
    Retorna None se não existir.
    """    
    return db.query(Status).filter(Status.id == status_id).first()


def get_status_by_name_and_applies_to(
    db: Session,
    name: str,
    applies_to: str,
) -> Status | None:
    """
    Busca um status pelo nome interno e aplicação (ex: 'active' para 'user').
    Usado para garantir consistência entre módulos.
    """    
    return (
        db.query(Status)
        .filter(
            Status.name == name,
            Status.applies_to == applies_to,
        )
        .first()
    )


# ========================================
# MÓDULOS
# ========================================

def list_statuses(
    db: Session,
    applies_to: str | None = None,
) -> list[Status]:
    """
    Lista statuses, com filtro opcional por aplicação.

    Exemplo:
    - user
    - clinic
    - patient
    - exam
    """    
    query = db.query(Status)

    # Aplica filtro apenas se informado
    if applies_to:
        query = query.filter(Status.applies_to == applies_to)

    return (
        query
        .order_by(Status.applies_to.asc(), Status.display_name.asc())
        .all()
    )


def create_status(db: Session, status: Status) -> Status:
    """
    Persiste um novo status no banco.
    """    
    db.add(status)
    db.commit()
    db.refresh(status)
    return status


def save_status(db: Session, status: Status) -> Status:
    """
    Persiste alterações em um status existente.
    Usado após updates no service.
    """    
    db.commit()
    db.refresh(status)
    return status
