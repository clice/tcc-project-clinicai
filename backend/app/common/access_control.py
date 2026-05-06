"""
Funções comuns de controle de acesso.

Centraliza regras de acesso por perfil para evitar repetição.
"""

from fastapi import HTTPException

from app.common.constants import RoleName
from app.common.services import get_user_role_name, ensure_user_has_clinic
from app.modules.users.model import User


def ensure_user_can_access_clinic_data(
    *,
    current_user: User,
    clinic_id: int,
    detail: str = "Você não tem permissão para acessar dados desta clínica.",
) -> None:
    """
    Regra:
    - admin_master acessa qualquer clínica;
    - usuários comuns acessam apenas a própria clínica.
    """
    role_name = get_user_role_name(current_user)

    if role_name == RoleName.ADMIN_MASTER.value:
        return

    current_clinic_id = ensure_user_has_clinic(current_user)

    if current_clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail=detail)


def ensure_user_can_access_patient(
    *,
    current_user: User,
    patient,
    detail: str = "Você não tem permissão para acessar este paciente.",
) -> None:
    """
    Regra:
    - admin_master acessa qualquer paciente;
    - clinic_staff acessa pacientes da própria clínica;
    - doctor acessa apenas pacientes vinculados a ele.
    """
    role_name = get_user_role_name(current_user)

    if role_name == RoleName.ADMIN_MASTER.value:
        return

    if role_name == RoleName.CLINIC_STAFF.value and patient.clinic_id == current_user.clinic_id:
        return

    if role_name == RoleName.DOCTOR.value and patient.doctor_id == current_user.id:
        return

    raise HTTPException(status_code=403, detail=detail)


def ensure_user_can_access_exam(
    *,
    current_user: User,
    exam,
    detail: str = "Você não tem permissão para acessar este exame.",
) -> None:
    """
    Regra:
    - admin_master acessa qualquer exame;
    - clinic_staff acessa exames da própria clínica;
    - doctor acessa apenas exames vinculados a ele.
    """
    role_name = get_user_role_name(current_user)

    if role_name == RoleName.ADMIN_MASTER.value:
        return

    if role_name == RoleName.CLINIC_STAFF.value and exam.clinic_id == current_user.clinic_id:
        return

    if role_name == RoleName.DOCTOR.value and exam.doctor_id == current_user.id:
        return

    raise HTTPException(status_code=403, detail=detail)
    

def filter_query_by_user_scope(
    *,
    query,
    model,
    current_user: User,
    clinic_field_name: str = "clinic_id",
    doctor_field_name: str = "doctor_id",
    doctor_only: bool = False,
):
    """
    Aplica escopo de listagem conforme perfil.

    Regra:
    - admin_master vê tudo;
    - clinic_staff vê registros da própria clínica;
    - doctor vê registros vinculados a ele.
    """
    role_name = get_user_role_name(current_user)

    if role_name == RoleName.ADMIN_MASTER.value:
        return query

    if role_name == RoleName.CLINIC_STAFF.value:
        clinic_id = ensure_user_has_clinic(current_user)
        return query.filter(getattr(model, clinic_field_name) == clinic_id)

    if role_name == RoleName.DOCTOR.value:
        if doctor_only:
            return query.filter(getattr(model, doctor_field_name) == current_user.id)

        return query.filter(getattr(model, doctor_field_name) == current_user.id)

    raise HTTPException(
        status_code=403,
        detail="Usuário sem permissão para listar registros.",
    )
    