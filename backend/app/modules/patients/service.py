"""
Service do módulo de pacientes.

Aqui ficam as regras de negócio e operações com o banco.
O router deve ficar mais limpo e apenas chamar essas funções.
"""

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.common.access_control import (
    ensure_user_can_access_clinic_data,
    ensure_user_can_access_patient,
    filter_query_by_user_scope,
)
from app.common.constants import AuditAction, AuditEntity, RoleName, StatusName, StatusScope
from app.common.services import (
    apply_update_data,
    get_user_role_name,
    model_dump_update,
    serialize_for_json,
)
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.patients.model import Patient
from app.modules.statuses.model import Status
from app.modules.users.model import User
from app.modules.patients.schema import PatientCreate, PatientUpdate
from app.modules.audit_logs.service import create_audit_log
from app.modules.statuses.service import get_status_by_name_and_applies_to


def validate_user_can_access_clinic(
    *,
    current_user: User,
    clinic_id: int,
) -> None:
    """
    Garante que usuários de clínica acessem apenas dados da própria clínica.
    """
    ensure_user_can_access_clinic_data(
        current_user=current_user,
        clinic_id=clinic_id,
    )


def validate_user_can_access_patient(
    *,
    patient: Patient,
    current_user: User,
) -> None:
    """
    Garante que o usuário autenticado pode acessar o paciente.
    """
    ensure_user_can_access_patient(
        current_user=current_user,
        patient=patient,
    )


def validate_clinic_is_active(db: Session, clinic_id: int) -> Clinic:
    """
    Valida se a clínica existe e está ativa.
    """
    clinic = (
        db.query(Clinic)
        .join(Status, Clinic.status_id == Status.id)
        .filter(
            Clinic.id == clinic_id,
            Status.name == StatusName.ACTIVE.value,
            Status.applies_to == StatusScope.CLINIC.value,
        )
        .first()
    )

    if not clinic:
        raise HTTPException(
            status_code=400,
            detail="Clínica não encontrada ou não está ativa.",
        )

    return clinic


def validate_doctor_can_be_assigned(
    db: Session,
    *,
    doctor_id: int | None,
    clinic_id: int,
) -> None:
    """
    Valida se o médico informado pode ser vinculado ao paciente.
    """
    if doctor_id is None:
        raise HTTPException(
            status_code=400,
            detail="O paciente deve estar vinculado a um médico.",
        )

    doctor = (
        db.query(User)
        .options(
            joinedload(User.role),
            joinedload(User.status),
        )
        .filter(User.id == doctor_id)
        .first()
    )

    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")

    if not doctor.role or doctor.role.name != RoleName.DOCTOR.value:
        raise HTTPException(
            status_code=400,
            detail="O usuário selecionado não possui perfil de médico.",
        )

    if doctor.clinic_id != clinic_id:
        raise HTTPException(
            status_code=400,
            detail="O médico selecionado não pertence à clínica do paciente.",
        )

    if not doctor.status or doctor.status.name != StatusName.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail="O médico selecionado não está ativo.",
        )


def check_patient_duplicate(
    db: Session,
    *,
    clinic_id: int,
    cpf: str,
    ignore_patient_id: int | None = None,
) -> None:
    """
    Verifica se já existe paciente com o mesmo CPF na mesma clínica.
    """
    query = db.query(Patient).filter(
        Patient.clinic_id == clinic_id,
        Patient.cpf == cpf,
    )

    if ignore_patient_id is not None:
        query = query.filter(Patient.id != ignore_patient_id)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="Já existe um paciente com esse CPF nesta clínica.",
        )


def patient_has_exams(db: Session, patient_id: int) -> bool:
    """Informa se o paciente já possui histórico de exames."""

    return (
        db.query(Exam.id)
        .filter(Exam.patient_id == patient_id)
        .first()
        is not None
    )


def validate_patient_assignment_change(
    db: Session,
    *,
    patient: Patient,
    current_user: User,
    new_clinic_id: int,
    new_doctor_id: int,
) -> bool:
    """Valida troca de clínica ou médico responsável.

    Política acadêmica adotada na CHK-08:
    - médico não transfere nem reatribui pacientes;
    - funcionário pode reatribuir somente dentro da própria clínica;
    - administrador pode transferir entre clínicas;
    - qualquer mudança de vínculo é bloqueada quando já existe exame,
      preservando RN05/RN06 e evitando divergência histórica.
    """

    assignment_changed = (
        new_clinic_id != patient.clinic_id
        or new_doctor_id != patient.doctor_id
    )
    if not assignment_changed:
        return False

    role_name = get_user_role_name(current_user)
    if role_name == RoleName.DOCTOR.value:
        raise HTTPException(
            status_code=403,
            detail=(
                "Médicos não podem transferir o paciente nem alterar o "
                "médico responsável."
            ),
        )

    if patient_has_exams(db, patient.id):
        raise HTTPException(
            status_code=409,
            detail=(
                "Não é possível alterar a clínica ou o médico responsável "
                "porque o paciente já possui exames vinculados."
            ),
        )

    return True


def build_patient_response(patient: Patient) -> dict:
    """
    Monta a resposta do paciente com dados relacionados.
    """
    return {
        "id": patient.id,
        "clinic_id": patient.clinic_id,
        "clinic_name": patient.clinic.name if patient.clinic else None,
        "doctor_id": patient.doctor_id,
        "doctor_name": patient.doctor.name if patient.doctor else None,
        "status_id": patient.status_id,
        "status_name": patient.status.name if patient.status else None,
        "status_display_name": patient.status.display_name if patient.status else None,
        "name": patient.name,
        "cpf": patient.cpf,
        "birth_date": patient.birth_date,
        "sex": patient.sex,
        "email": patient.email,
        "phone": patient.phone,
        "zip_code": patient.zip_code,
        "address": patient.address,
        "number": patient.number,
        "complement": patient.complement,
        "neighborhood": patient.neighborhood,
        "city": patient.city,
        "state": patient.state,
        "created_at": patient.created_at,
        "updated_at": patient.updated_at,
    }


# ========================================
# MAIN METHODS
# ========================================


def get_patient_by_id(db: Session, patient_id: int) -> Patient:
    """
    Busca um paciente pelo ID.
    """
    patient = (
        db.query(Patient)
        .options(
            joinedload(Patient.clinic),
            joinedload(Patient.status),
            joinedload(Patient.doctor),
        )
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    return patient


def list_patients(
    db: Session,
    *,
    include_inactive: bool = False,
    search: str | None = None,
    clinic_id: int | None = None,
    doctor_id: int | None = None,
    current_user: User,
) -> list[dict]:
    """Lista pacientes sem permitir que filtros ampliem o escopo do usuário.

    Escopo documentado:
    - admin_master: todos os pacientes;
    - clinic_manager: pacientes da própria clínica;
    - doctor: somente pacientes sob sua responsabilidade.
    """

    role_name = get_user_role_name(current_user)

    if clinic_id is not None and role_name != RoleName.ADMIN_MASTER.value:
        validate_user_can_access_clinic(
            current_user=current_user,
            clinic_id=clinic_id,
        )

    if (
        doctor_id is not None
        and role_name == RoleName.DOCTOR.value
        and doctor_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Médicos só podem filtrar os próprios pacientes.",
        )

    query = (
        db.query(Patient)
        .options(
            joinedload(Patient.clinic),
            joinedload(Patient.status),
            joinedload(Patient.doctor),
        )
        .join(Status, Patient.status_id == Status.id)
    )

    query = filter_query_by_user_scope(
        query=query,
        model=Patient,
        current_user=current_user,
    )

    if not include_inactive:
        query = query.filter(
            Status.name == StatusName.ACTIVE.value,
            Status.applies_to == StatusScope.PATIENT.value,
        )

    if clinic_id is not None:
        query = query.filter(Patient.clinic_id == clinic_id)

    if doctor_id is not None:
        query = query.filter(Patient.doctor_id == doctor_id)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Patient.name.ilike(term),
                Patient.cpf.ilike(term),
                Patient.email.ilike(term),
            )
        )

    patients = query.order_by(Patient.name.asc()).all()
    return [build_patient_response(patient) for patient in patients]


def create_patient(
    db: Session,
    payload: PatientCreate,
    current_user: User,
) -> dict:
    """Cria paciente com clínica e médico validados no backend."""

    validate_user_can_access_clinic(
        current_user=current_user,
        clinic_id=payload.clinic_id,
    )
    validate_clinic_is_active(db=db, clinic_id=payload.clinic_id)

    active_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.ACTIVE.value,
        applies_to=StatusScope.PATIENT.value,
    )

    check_patient_duplicate(
        db=db,
        clinic_id=payload.clinic_id,
        cpf=payload.cpf,
    )

    doctor_id = payload.doctor_id
    if get_user_role_name(current_user) == RoleName.DOCTOR.value:
        if payload.doctor_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="O médico só pode cadastrar pacientes sob sua responsabilidade.",
            )
        doctor_id = current_user.id

    validate_doctor_can_be_assigned(
        db=db,
        doctor_id=doctor_id,
        clinic_id=payload.clinic_id,
    )

    patient = Patient(
        clinic_id=payload.clinic_id,
        doctor_id=doctor_id,
        status_id=active_status.id,
        name=payload.name,
        cpf=payload.cpf,
        birth_date=payload.birth_date,
        sex=payload.sex,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        zip_code=payload.zip_code,
        address=payload.address,
        number=payload.number,
        complement=payload.complement,
        neighborhood=payload.neighborhood,
        city=payload.city,
        state=payload.state,
    )

    db.add(patient)
    db.flush()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=patient.clinic_id,
        action=AuditAction.CREATE,
        entity=AuditEntity.PATIENT,
        entity_id=patient.id,
        description="Paciente cadastrado.",
        new_data={
            "id": patient.id,
            "clinic_id": patient.clinic_id,
            "doctor_id": patient.doctor_id,
            "status_id": patient.status_id,
            "name": patient.name,
            "cpf": patient.cpf,
            "birth_date": str(patient.birth_date) if patient.birth_date else None,
            "sex": patient.sex,
            "email": patient.email,
            "phone": patient.phone,
        },
    )

    db.commit()
    db.refresh(patient)
    return build_patient_response(get_patient_by_id(db=db, patient_id=patient.id))


def get_patient(
    db: Session,
    patient_id: int,
    current_user: User,
) -> dict:
    """
    Busca um paciente específico pelo ID.
    """
    patient = get_patient_by_id(db=db, patient_id=patient_id)

    validate_user_can_access_patient(
        patient=patient,
        current_user=current_user,
    )

    return build_patient_response(patient)


def update_patient(
    db: Session,
    patient_id: int,
    payload: PatientUpdate,
    current_user: User,
) -> dict:
    """Atualiza paciente e aplica a política de transferência da CHK-08."""

    patient = get_patient_by_id(db=db, patient_id=patient_id)
    validate_user_can_access_patient(patient=patient, current_user=current_user)

    update_data = model_dump_update(payload)
    if not update_data:
        return build_patient_response(patient)

    required_fields = {
        "clinic_id": "O paciente deve permanecer vinculado a uma clínica.",
        "doctor_id": "O paciente deve permanecer vinculado a um médico.",
        "name": "Nome do paciente é obrigatório.",
        "cpf": "CPF do paciente é obrigatório.",
    }
    for field, detail in required_fields.items():
        if field in update_data and update_data[field] is None:
            raise HTTPException(status_code=400, detail=detail)

    new_clinic_id = update_data.get("clinic_id", patient.clinic_id)
    new_doctor_id = update_data.get("doctor_id", patient.doctor_id)
    new_cpf = update_data.get("cpf", patient.cpf)

    assignment_changed = validate_patient_assignment_change(
        db=db,
        patient=patient,
        current_user=current_user,
        new_clinic_id=new_clinic_id,
        new_doctor_id=new_doctor_id,
    )

    validate_user_can_access_clinic(
        current_user=current_user,
        clinic_id=new_clinic_id,
    )
    validate_clinic_is_active(db=db, clinic_id=new_clinic_id)
    validate_doctor_can_be_assigned(
        db=db,
        doctor_id=new_doctor_id,
        clinic_id=new_clinic_id,
    )
    check_patient_duplicate(
        db=db,
        clinic_id=new_clinic_id,
        cpf=new_cpf,
        ignore_patient_id=patient_id,
    )

    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = str(update_data["email"])

    old_data = {
        "clinic_id": patient.clinic_id,
        "doctor_id": patient.doctor_id,
        "status_id": patient.status_id,
        "name": patient.name,
        "cpf": patient.cpf,
        "birth_date": str(patient.birth_date) if patient.birth_date else None,
        "sex": patient.sex,
        "email": patient.email,
        "phone": patient.phone,
        "zip_code": patient.zip_code,
        "address": patient.address,
        "number": patient.number,
        "complement": patient.complement,
        "neighborhood": patient.neighborhood,
        "city": patient.city,
        "state": patient.state,
    }

    apply_update_data(patient, update_data)
    audit_new_data = serialize_for_json(update_data)
    if assignment_changed:
        audit_new_data["assignment_changed"] = True

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=patient.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.PATIENT,
        entity_id=patient.id,
        description=(
            "Vínculo do paciente atualizado."
            if assignment_changed
            else "Paciente atualizado."
        ),
        old_data=old_data,
        new_data=audit_new_data,
    )

    db.commit()
    db.refresh(patient)
    return build_patient_response(get_patient_by_id(db=db, patient_id=patient.id))


def activate_patient(
    db: Session,
    patient_id: int,
    current_user: User,
) -> dict:
    """Ativa paciente somente com clínica e médico ainda válidos."""

    patient = get_patient_by_id(db=db, patient_id=patient_id)
    validate_user_can_access_patient(patient=patient, current_user=current_user)

    if patient.status and patient.status.name == StatusName.ACTIVE.value:
        return build_patient_response(patient)

    validate_clinic_is_active(db=db, clinic_id=patient.clinic_id)
    validate_doctor_can_be_assigned(
        db=db,
        doctor_id=patient.doctor_id,
        clinic_id=patient.clinic_id,
    )

    active_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.ACTIVE.value,
        applies_to=StatusScope.PATIENT.value,
    )

    old_data = {
        "status_id": patient.status_id,
        "status_name": patient.status.name if patient.status else None,
    }
    patient.status_id = active_status.id

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=patient.clinic_id,
        action=AuditAction.CHANGE_STATUS_ACTIVATE,
        entity=AuditEntity.PATIENT,
        entity_id=patient.id,
        description="Paciente ativado.",
        old_data=old_data,
        new_data={
            "status_id": active_status.id,
            "status_name": StatusName.ACTIVE.value,
        },
    )

    db.commit()
    db.refresh(patient)
    return build_patient_response(get_patient_by_id(db=db, patient_id=patient.id))


def inactivate_patient(
    db: Session,
    patient_id: int,
    current_user: User,
) -> dict:
    """Inativa paciente de forma lógica e idempotente."""

    patient = get_patient_by_id(db=db, patient_id=patient_id)
    validate_user_can_access_patient(patient=patient, current_user=current_user)

    if patient.status and patient.status.name == StatusName.INACTIVE.value:
        return build_patient_response(patient)

    inactive_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.INACTIVE.value,
        applies_to=StatusScope.PATIENT.value,
    )

    old_data = {
        "status_id": patient.status_id,
        "status_name": patient.status.name if patient.status else None,
    }
    patient.status_id = inactive_status.id

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=patient.clinic_id,
        action=AuditAction.CHANGE_STATUS_INACTIVATE,
        entity=AuditEntity.PATIENT,
        entity_id=patient.id,
        description="Paciente inativado.",
        old_data=old_data,
        new_data={
            "status_id": inactive_status.id,
            "status_name": StatusName.INACTIVE.value,
        },
    )

    db.commit()
    db.refresh(patient)
    return build_patient_response(get_patient_by_id(db=db, patient_id=patient.id))
