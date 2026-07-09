"""
Schemas do módulo de audit logs.

Define os modelos Pydantic usados nas respostas da API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """
    Schema usado nas respostas da API.
    """

    id: int

    user_id: int | None = None
    user_name: str | None = None

    clinic_id: int | None = None
    clinic_name: str | None = None

    action: str
    entity: str
    entity_id: int | None = None

    description: str | None = None

    old_data: Any | None = None
    new_data: Any | None = None

    ip_address: str | None = None
    user_agent: str | None = None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class AuditLogListResponse(BaseModel):
    """
    Schema paginado usado na listagem de audit logs.
    """

    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int
