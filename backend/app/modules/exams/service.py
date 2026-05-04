"""
Service do módulo de exames.

Concentra as regras de negócio relacionadas aos exames.
"""

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.common.constants import AuditAction, AuditEntity, RoleName, StatusName, StatusScope
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.exams.schema import ExamCreate, ExamUpdate
from app.modules.patients.model import Patient
from app.modules.statuses.model import Status
from app.modules.audit_logs.service import create_audit_log
from app.modules.statuses.service import (
    get_status_by_id_and_applies_to,
    get_status_by_name_and_applies_to,
)
from app.modules.users.model import User


def is_admin_master(user: User) -> bool:
    """
    Verifica se o usuário autenticado é admin_master.
    """
    return bool(user.role and user.role.name == RoleName.ADMIN_MASTER.value)


def build_exam_response(exam: Exam) -> dict:
    """
    Monta a resposta incluindo dados relacionados.
    """
    return {
        "id": exam.id,
        "clinic_id": exam.clinic_id,
        "clinic_name": exam.clinic.name if exam.clinic else None,
        "patient_id": exam.patient_id,
        "patient_name": exam.patient.name if exam.patient else None,
        "doctor_id": exam.doctor_id,
        "doctor_name": exam.doctor.name if exam.doctor else None,
        "status_id": exam.status_id,
        "status_name": exam.status.name if exam.status else None,
        "status_display_name": exam.status.display_name if exam.status else None,
        "exam_type": exam.exam_type,
        "exam_date": exam.exam_date,
        "title": exam.title,
        "description": exam.description,
        "clinical_indication": exam.clinical_indication,
        "findings": exam.findings,
        "conclusion": exam.conclusion,
        "ai_analysis_status": exam.ai_analysis_status,
        "ai_summary": exam.ai_summary,
        "file_path": exam.file_path,
        "file_name": exam.file_name,
        "file_mime_type": exam.file_mime_type,
        "created_at": exam.created_at,
        "updated_at": exam.updated_at,
    }


def validate_user_can_access_exam(
    *,
    current_user: User,
    exam: Exam,
) -> None:
    """
    Garante que o usuário autenticado pode acessar o exame.
    """
    role_name = current_user.role.name if current_user.role else None

    if role_name == RoleName.ADMIN_MASTER.value:
        return

    if role_name == RoleName.CLINIC_STAFF.value and exam.clinic_id == current_user.clinic_id:
        return

    if role_name == RoleName.DOCTOR.value and exam.doctor_id == current_user.id:
        return

    raise HTTPException(
        status_code=403,
        detail="Você não tem permissão para acessar este exame.",
    )


def validate_user_can_access_clinic(
    *,
    current_user: User,
    clinic_id: int,
) -> None:
    """
    Garante que usuários comuns acessem apenas dados da própria clínica.
    """
    if is_admin_master(current_user):
        return

    if current_user.clinic_id is None:
        raise HTTPException(
            status_code=403,
            detail="Usuário não está vinculado a uma clínica.",
        )

    if current_user.clinic_id != clinic_id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para acessar dados desta clínica.",
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


def validate_patient_belongs_to_clinic(
    db: Session,
    *,
    patient_id: int,
    clinic_id: int,
) -> Patient:
    """
    Valida paciente e vínculo com a clínica.
    """
    patient = (
        db.query(Patient)
        .options(
            joinedload(Patient.status),
            joinedload(Patient.doctor),
        )
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    if patient.clinic_id != clinic_id:
        raise HTTPException(
            status_code=400,
            detail="Paciente não pertence à clínica informada.",
        )

    if not patient.status or patient.status.name != StatusName.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail="Paciente não está ativo.",
        )

    return patient


def validate_doctor_can_be_assigned(
    db: Session,
    *,
    doctor_id: int | None,
    clinic_id: int,
) -> User:
    """
    Valida se o médico informado pode ser vinculado ao exame.
    """
    if doctor_id is None:
        raise HTTPException(
            status_code=400,
            detail="O exame deve estar vinculado a um médico.",
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
            detail="O médico selecionado não pertence à clínica do exame.",
        )

    if not doctor.status or doctor.status.name != StatusName.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail="O médico selecionado não está ativo.",
        )

    return doctor


def validate_exam_relationships(
    db: Session,
    *,
    clinic_id: int,
    patient_id: int,
    doctor_id: int | None,
    status_id: int,
) -> None:
    """
    Valida clínica, paciente, médico e status.
    """
    validate_clinic_is_active(db=db, clinic_id=clinic_id)

    patient = validate_patient_belongs_to_clinic(
        db=db,
        patient_id=patient_id,
        clinic_id=clinic_id,
    )

    validate_doctor_can_be_assigned(
        db=db,
        doctor_id=doctor_id,
        clinic_id=clinic_id,
    )

    if patient.doctor_id != doctor_id:
        raise HTTPException(
            status_code=400,
            detail="O médico do exame deve ser o médico responsável pelo paciente.",
        )

    get_status_by_id_and_applies_to(
        db=db,
        status_id=status_id,
        applies_to=StatusScope.EXAM.value,
    )


def get_exam_model_by_id(db: Session, exam_id: int) -> Exam:
    """
    Busca o model de exame pelo ID.
    """
    exam = (
        db.query(Exam)
        .options(
            joinedload(Exam.clinic),
            joinedload(Exam.patient),
            joinedload(Exam.doctor),
            joinedload(Exam.status),
        )
        .filter(Exam.id == exam_id)
        .first()
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    return exam


def get_exam_by_id(
    db: Session,
    exam_id: int,
    current_user: User,
) -> dict:
    """
    Busca um exame pelo ID.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )

    return build_exam_response(exam)


def list_exams(
    db: Session,
    current_user: User,
    search: str | None = None,
    clinic_id: int | None = None,
    patient_id: int | None = None,
    doctor_id: int | None = None,
    status_id: int | None = None,
    include_inactive: bool = True,
) -> list[dict]:
    """
    Lista exames cadastrados conforme perfil do usuário.
    """
    query = (
        db.query(Exam)
        .options(
            joinedload(Exam.clinic),
            joinedload(Exam.patient),
            joinedload(Exam.doctor),
            joinedload(Exam.status),
        )
        .join(Status, Exam.status_id == Status.id)
    )

    role_name = current_user.role.name if current_user.role else None

    if role_name == RoleName.ADMIN_MASTER.value:
        if clinic_id is not None:
            query = query.filter(Exam.clinic_id == clinic_id)

    elif role_name == RoleName.CLINIC_STAFF.value:
        if current_user.clinic_id is None:
            raise HTTPException(
                status_code=403,
                detail="Usuário não está vinculado a uma clínica.",
            )

        if clinic_id is not None and clinic_id != current_user.clinic_id:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para listar exames de outra clínica.",
            )

        query = query.filter(Exam.clinic_id == current_user.clinic_id)

    elif role_name == RoleName.DOCTOR.value:
        if doctor_id is not None and doctor_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para listar exames de outro médico.",
            )

        query = query.filter(Exam.doctor_id == current_user.id)

    else:
        raise HTTPException(
            status_code=403,
            detail="Usuário sem permissão para listar exames.",
        )

    if patient_id:
        query = query.filter(Exam.patient_id == patient_id)

    if doctor_id and role_name != RoleName.DOCTOR.value:
        query = query.filter(Exam.doctor_id == doctor_id)

    if status_id:
        query = query.filter(Exam.status_id == status_id)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Exam.title.ilike(term),
                Exam.exam_type.ilike(term),
                Exam.description.ilike(term),
                Exam.clinical_indication.ilike(term),
                Exam.findings.ilike(term),
                Exam.conclusion.ilike(term),
            )
        )

    if not include_inactive:
        query = query.filter(
            Status.name != StatusName.CANCELED.value,
            Status.applies_to == StatusScope.EXAM.value,
        )

    exams = query.order_by(Exam.created_at.desc()).all()

    return [build_exam_response(exam) for exam in exams]


def create_exam(
    db: Session,
    payload: ExamCreate,
    current_user: User,
) -> dict:
    """
    Cria um novo exame.
    """
    doctor_id = payload.doctor_id

    if current_user.role and current_user.role.name == RoleName.DOCTOR.value:
        doctor_id = current_user.id

    validate_user_can_access_clinic(
        current_user=current_user,
        clinic_id=payload.clinic_id,
    )

    validate_exam_relationships(
        db=db,
        clinic_id=payload.clinic_id,
        patient_id=payload.patient_id,
        doctor_id=doctor_id,
        status_id=payload.status_id,
    )

    exam = Exam(
        clinic_id=payload.clinic_id,
        patient_id=payload.patient_id,
        doctor_id=doctor_id,
        status_id=payload.status_id,
        exam_type=payload.exam_type,
        exam_date=payload.exam_date,
        title=payload.title,
        description=payload.description,
        clinical_indication=payload.clinical_indication,
        findings=payload.findings,
        conclusion=payload.conclusion,
        ai_analysis_status=payload.ai_analysis_status,
        ai_summary=payload.ai_summary,
        file_path=payload.file_path,
        file_name=payload.file_name,
        file_mime_type=payload.file_mime_type,
    )

    db.add(exam)
    db.flush()

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.CREATE,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Exame cadastrado.",
        new_data={
            "id": exam.id,
            "clinic_id": exam.clinic_id,
            "patient_id": exam.patient_id,
            "doctor_id": exam.doctor_id,
            "status_id": exam.status_id,
            "exam_type": exam.exam_type,
            "exam_date": str(exam.exam_date) if exam.exam_date else None,
            "title": exam.title,
        },
    )

    db.commit()
    db.refresh(exam)

    exam = get_exam_model_by_id(db=db, exam_id=exam.id)

    return build_exam_response(exam)


def update_exam(
    db: Session,
    exam_id: int,
    payload: ExamUpdate,
    current_user: User,
) -> dict:
    """
    Atualiza parcialmente um exame.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return build_exam_response(exam)

    clinic_id = update_data.get("clinic_id", exam.clinic_id)
    patient_id = update_data.get("patient_id", exam.patient_id)
    doctor_id = update_data.get("doctor_id", exam.doctor_id)
    status_id = update_data.get("status_id", exam.status_id)

    if current_user.role and current_user.role.name == RoleName.DOCTOR.value:
        doctor_id = current_user.id
        update_data["doctor_id"] = current_user.id

    validate_user_can_access_clinic(
        current_user=current_user,
        clinic_id=clinic_id,
    )

    validate_exam_relationships(
        db=db,
        clinic_id=clinic_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status_id=status_id,
    )

    old_data = {
        "clinic_id": exam.clinic_id,
        "patient_id": exam.patient_id,
        "doctor_id": exam.doctor_id,
        "status_id": exam.status_id,
        "exam_type": exam.exam_type,
        "exam_date": str(exam.exam_date) if exam.exam_date else None,
        "title": exam.title,
        "description": exam.description,
        "clinical_indication": exam.clinical_indication,
        "findings": exam.findings,
        "conclusion": exam.conclusion,
        "ai_analysis_status": exam.ai_analysis_status,
        "ai_summary": exam.ai_summary,
    }
    
    for field, value in update_data.items():
        setattr(exam, field, value)

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Exame atualizado.",
        old_data=old_data,
        new_data=update_data,
    )
    
    db.commit()
    db.refresh(exam)

    exam = get_exam_model_by_id(db=db, exam_id=exam.id)

    return build_exam_response(exam)


def cancel_exam(
    db: Session,
    exam_id: int,
    current_user: User,
) -> dict:
    """
    Cancela logicamente um exame.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )

    canceled_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.CANCELED.value,
        applies_to=StatusScope.EXAM.value,
    )

    old_data = {
        "status_id": exam.status_id,
        "status_name": exam.status.name if exam.status else None,
    }

    exam.status_id = canceled_status.id

    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.CANCEL_EXAM,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Exame cancelado.",
        old_data=old_data,
        new_data={
            "status_id": canceled_status.id,
            "status_name": StatusName.CANCELED.value,
        },
    )

    db.commit()
    db.refresh(exam)

    exam = get_exam_model_by_id(db=db, exam_id=exam.id)

    return build_exam_response(exam)


def upload_exam_file(
    db: Session,
    exam_id: int,
    file_path: str,
    file_name: str,
    file_mime_type: str,
    current_user: User,
) -> dict:
    """
    Vincula dados de arquivo a um exame.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )
    
    exam.file_path = file_path
    exam.file_name = file_name
    exam.file_mime_type = file_mime_type
    
    old_data = {
        "file_path": exam.file_path,
        "file_name": exam.file_name,
        "file_mime_type": exam.file_mime_type,
    }
    
    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.UPLOAD,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Arquivo de exame vinculado.",
        old_data=old_data,
        new_data={
            "file_path": exam.file_path,
            "file_name": exam.file_name,
            "file_mime_type": exam.file_mime_type,
        },
    )

    db.commit()
    db.refresh(exam)

    exam = get_exam_model_by_id(db=db, exam_id=exam.id)

    return build_exam_response(exam)


def download_exam_file(
    db: Session,
    exam_id: int,
    current_user: User,
) -> dict:
    """
    Retorna os dados do arquivo vinculado ao exame.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )

    if not exam.file_path:
        raise HTTPException(
            status_code=404,
            detail="Este exame não possui arquivo vinculado.",
        )
        
    old_data = {
        "file_path": exam.file_path,
        "file_name": exam.file_name,
        "file_mime_type": exam.file_mime_type,
    }
    
    # Adiciona log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.DOWNLOAD,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Arquivo de exame vinculado.",
        old_data=old_data,
        new_data={
            "file_path": exam.file_path,
            "file_name": exam.file_name,
            "file_mime_type": exam.file_mime_type,
        },
    )

    return {
        "exam_id": exam.id,
        "file_path": exam.file_path,
        "file_name": exam.file_name,
        "file_mime_type": exam.file_mime_type,
    }
