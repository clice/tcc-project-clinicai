"""Políticas de acesso aplicadas a sessões autenticadas do ClinicAI."""

from fastapi import HTTPException, status

from app.common.constants import RoleName, StatusName, StatusScope
from app.modules.users.model import User


def validate_active_session_context(user: User) -> None:
    """Valida usuário e clínica antes de aceitar uma sessão.

    Administradores master não possuem clínica. Para médicos e funcionários,
    a clínica vinculada também precisa existir e estar ativa. A mesma regra é
    reutilizada no login, no refresh token e em todas as rotas protegidas para
    evitar comportamentos diferentes entre os três pontos.
    """

    if (
        not user.status
        or user.status.applies_to != StatusScope.USER.value
        or user.status.name != StatusName.ACTIVE.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo ou bloqueado.",
        )

    is_admin_master = (
        user.role is not None
        and user.role.name == RoleName.ADMIN_MASTER.value
    )

    if is_admin_master:
        return

    if user.clinic_id is None or user.clinic is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem clínica ativa vinculada.",
        )

    clinic_status = user.clinic.status

    if (
        clinic_status is None
        or clinic_status.applies_to != StatusScope.CLINIC.value
        or clinic_status.name != StatusName.ACTIVE.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clínica inativa ou bloqueada.",
        )
