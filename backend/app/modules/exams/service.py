"""
Service do módulo de exames.

Concentra as regras de negócio relacionadas aos exames.
"""

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.common.access_control import (
    ensure_user_can_access_clinic_data,
    ensure_user_can_access_exam,
)
from app.common.constants import AuditAction, AuditEntity, RoleName, StatusName, StatusScope
from app.common.services import (
    apply_update_data,
    model_dump_update,
)
from app.modules.ai_analysis.client import AIServiceError, request_prediction
from app.modules.ai_analysis.file_storage import (
    resolve_safe_gradcam_path,
    serialize_gradcam_path,
)
from app.modules.ai_analysis.model import AIAnalysis
from app.modules.ai_analysis.schema import AIAnalysisCreate
from app.modules.ai_analysis.service import build_ai_analysis_response, create_ai_analysis
from app.modules.audit_logs.service import create_audit_log, list_entity_audit_logs
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.exams.file_storage import (
    delete_exam_file_safely,
    resolve_safe_exam_file_path,
    serialize_exam_file_path,
    store_validated_exam_file,
    validate_exam_file,
)
from app.modules.exams.schema import ExamCreate, ExamMedicalReview, ExamUpdate
from app.modules.exams.state_machine import (
    ExamTransitionAction,
    ensure_exam_is_editable,
    get_transition_target,
    transition_audit_payload,
)
from app.modules.patients.model import Patient
from app.modules.statuses.model import Status
from app.modules.statuses.service import (
    get_status_by_id_and_applies_to,
    get_status_by_name_and_applies_to,
)
from app.modules.users.model import User



def build_exam_response(exam: Exam, current_user: User | None = None) -> dict:
    """
    Monta a resposta incluindo dados relacionados.

    Os campos de predição da IA (ai_prediction_label/ai_prediction_class)
    só são incluídos se current_user for informado e não for
    Funcionário da Clínica — esse perfil não tem acesso a resultados
    diagnósticos (Art. 34 do CFM), mesmo agregados na listagem de exames.
    Quando current_user não é informado (uso interno), os campos vêm
    preenchidos por padrão.
    """
    role_name = current_user.role.name if current_user and current_user.role else None
    can_see_ai_prediction = role_name != RoleName.CLINIC_STAFF.value

    ai_prediction_label = None
    ai_prediction_class = None
    if can_see_ai_prediction and exam.ai_analysis:
        ai_prediction_label = exam.ai_analysis.prediction_label
        ai_prediction_class = exam.ai_analysis.prediction_class

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
        "analysis_in_progress": bool(exam.analysis_in_progress),
        "analysis_started_at": exam.analysis_started_at,
        "ai_analysis_status": (
            exam.ai_analysis.status.name
            if exam.ai_analysis and exam.ai_analysis.status
            else None
        ),
        "reviewed_by_id": exam.reviewed_by_id,
        "reviewed_by_name": exam.reviewed_by.name if exam.reviewed_by else None,
        "reviewed_at": exam.reviewed_at,
        "file_name": exam.file_name,
        "file_mime_type": exam.file_mime_type,
        "ai_prediction_label": ai_prediction_label,
        "ai_prediction_class": ai_prediction_class,
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
    ensure_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )


def validate_user_can_access_clinic(
    *,
    current_user: User,
    clinic_id: int,
) -> None:
    """
    Garante que usuários comuns acessem apenas dados da própria clínica.
    """
    ensure_user_can_access_clinic_data(
        current_user=current_user,
        clinic_id=clinic_id,
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


def list_exam_form_options(
    db: Session,
    current_user: User,
) -> dict:
    """
    Retorna os dados necessários para montar o formulário de exames.
    """
    role_name = current_user.role.name if current_user.role else None

    clinics_query = db.query(Clinic).options(joinedload(Clinic.status))
    patients_query = db.query(Patient).options(
        joinedload(Patient.status),
        joinedload(Patient.doctor),
    )
    doctors_query = db.query(User).options(
        joinedload(User.role),
        joinedload(User.status),
    )

    if role_name == RoleName.ADMIN_MASTER.value:
        pass

    elif role_name == RoleName.CLINIC_STAFF.value:
        if current_user.clinic_id is None:
            raise HTTPException(
                status_code=403,
                detail="Usuário não está vinculado a uma clínica.",
            )

        clinics_query = clinics_query.filter(Clinic.id == current_user.clinic_id)
        patients_query = patients_query.filter(Patient.clinic_id == current_user.clinic_id)
        doctors_query = doctors_query.filter(User.clinic_id == current_user.clinic_id)

    elif role_name == RoleName.DOCTOR.value:
        if current_user.clinic_id is None:
            raise HTTPException(
                status_code=403,
                detail="Usuário não está vinculado a uma clínica.",
            )

        clinics_query = clinics_query.filter(Clinic.id == current_user.clinic_id)
        patients_query = patients_query.filter(Patient.doctor_id == current_user.id)
        doctors_query = doctors_query.filter(User.id == current_user.id)

    else:
        raise HTTPException(
            status_code=403,
            detail="Usuário sem permissão para acessar formulário de exames.",
        )

    clinics = clinics_query.all()
    patients = patients_query.all()

    doctors = (
        doctors_query
        .join(User.role)
        .filter(User.role.has(name=RoleName.DOCTOR.value))
        .all()
    )

    statuses = (
        db.query(Status)
        .filter(Status.applies_to == StatusScope.EXAM.value)
        .order_by(Status.id.asc())
        .all()
    )

    return {
        "clinics": [
            {
                "id": clinic.id,
                "name": clinic.name,
                "status_name": clinic.status.name if clinic.status else None,
            }
            for clinic in clinics
        ],
        "patients": [
            {
                "id": patient.id,
                "name": patient.name,
                "clinic_id": patient.clinic_id,
                "doctor_id": patient.doctor_id,
                "status_name": patient.status.name if patient.status else None,
            }
            for patient in patients
        ],
        "doctors": [
            {
                "id": doctor.id,
                "name": doctor.name,
                "clinic_id": doctor.clinic_id,
                "role_name": doctor.role.name if doctor.role else None,
                "status_name": doctor.status.name if doctor.status else None,
            }
            for doctor in doctors
        ],
        "statuses": [
            {
                "id": status.id,
                "name": status.name,
                "display_name": status.display_name,
                "applies_to": status.applies_to,
            }
            for status in statuses
        ],
    }


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
            joinedload(Exam.reviewed_by),
            joinedload(Exam.ai_analysis),
        )
        .filter(Exam.id == exam_id)
        .first()
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    return exam


def get_exam_model_for_update(db: Session, exam_id: int) -> Exam:
    """Busca e bloqueia o exame durante uma transição crítica.

    PostgreSQL mantém o bloqueio até o commit/rollback. No SQLite usado pelos
    testes, ``FOR UPDATE`` é ignorado, e as operações condicionais continuam
    garantindo a semântica exercitada pela suíte.
    """

    exam = (
        db.query(Exam)
        .options(
            joinedload(Exam.clinic),
            joinedload(Exam.patient),
            joinedload(Exam.doctor),
            joinedload(Exam.reviewed_by),
            joinedload(Exam.status),
            joinedload(Exam.ai_analysis),
        )
        .filter(Exam.id == exam_id)
        .with_for_update(of=Exam)
        .first()
    )
    if not exam:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")
    return exam


def claim_exam_for_analysis(
    db: Session,
    exam_id: int,
    current_user: User | None = None,
) -> None:
    """Adquire e audita, de forma atômica, o direito de executar a inferência.

    A atualização condicional impede que clique duplo, retry do navegador ou
    duas sessões disparem o serviço de IA mais de uma vez para o mesmo exame.
    O marcador e o evento de início são confirmados no mesmo commit.
    """

    pending_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.PENDING.value,
        applies_to=StatusScope.EXAM.value,
    )
    target_name = get_transition_target(
        StatusName.PENDING.value,
        ExamTransitionAction.START_PROCESSING,
    )
    processing_status = get_status_by_name_and_applies_to(
        db=db,
        name=target_name,
        applies_to=StatusScope.EXAM.value,
    )
    started_at = datetime.now(timezone.utc)
    claimed = (
        db.query(Exam)
        .filter(
            Exam.id == exam_id,
            Exam.status_id == pending_status.id,
            Exam.analysis_in_progress.is_(False),
        )
        .update(
            {
                Exam.status_id: processing_status.id,
                Exam.analysis_in_progress: True,
                Exam.analysis_started_at: started_at,
            },
            synchronize_session=False,
        )
    )
    if claimed != 1:
        db.rollback()
        current = get_exam_model_by_id(db=db, exam_id=exam_id)
        if current.ai_analysis:
            return
        if current.analysis_in_progress:
            raise HTTPException(
                status_code=409,
                detail="Este exame já possui uma análise de IA em andamento.",
            )
        get_transition_target(
            current.status.name if current.status else None,
            ExamTransitionAction.START_PROCESSING,
        )
        raise HTTPException(status_code=409, detail="Não foi possível iniciar a análise.")

    try:
        clinic_id = (
            db.query(Exam.clinic_id)
            .filter(Exam.id == exam_id)
            .scalar()
        )
        create_audit_log(
            db=db,
            user_id=current_user.id if current_user else None,
            clinic_id=clinic_id,
            action=AuditAction.RUN_AI_ANALYSIS,
            entity=AuditEntity.EXAM,
            entity_id=exam_id,
            description="Execução da análise de IA iniciada.",
            old_data={
                "status_id": pending_status.id,
                "status_name": StatusName.PENDING.value,
                "analysis_in_progress": False,
                "analysis_started_at": None,
            },
            new_data={
                "phase": "started",
                "status_id": processing_status.id,
                "status_name": target_name,
                "transition_action": ExamTransitionAction.START_PROCESSING.value,
                "analysis_in_progress": True,
                "analysis_started_at": started_at.isoformat(),
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def clear_exam_analysis_claim(db: Session, exam: Exam) -> None:
    """Libera o marcador de execução atual dentro da transação aberta."""

    exam.analysis_in_progress = False
    exam.analysis_started_at = None


# ========================================
# MAIN METHODS
# ========================================


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

    return build_exam_response(exam, current_user=current_user)


def list_exams(
    db: Session,
    current_user: User,
    search: str | None = None,
    clinic_id: int | None = None,
    patient_id: int | None = None,
    doctor_id: int | None = None,
    status_id: int | None = None,
    ai_prediction_class: int | None = None,
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
            joinedload(Exam.ai_analysis),
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

    if ai_prediction_class is not None:
        if role_name == RoleName.CLINIC_STAFF.value:
            raise HTTPException(
                status_code=403,
                detail="Funcionário da clínica não tem permissão para filtrar por resultado da IA.",
            )
        query = query.join(AIAnalysis, AIAnalysis.exam_id == Exam.id).filter(
            AIAnalysis.prediction_class == ai_prediction_class
        )

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

    return [build_exam_response(exam, current_user=current_user) for exam in exams]


def create_exam(
    db: Session,
    payload: ExamCreate,
    file: UploadFile,
    current_user: User,
) -> dict:
    """
    Cria um novo exame com upload obrigatório.
    Status inicial: PENDING.
    """
    doctor_id = payload.doctor_id

    if current_user.role and current_user.role.name == RoleName.DOCTOR.value:
        doctor_id = current_user.id

    validate_user_can_access_clinic(
        current_user=current_user,
        clinic_id=payload.clinic_id,
    )

    initial_status_name = get_transition_target(None, ExamTransitionAction.CREATE)
    pending_status = get_status_by_name_and_applies_to(
        db=db,
        name=initial_status_name,
        applies_to=StatusScope.EXAM.value,
    )

    validate_exam_relationships(
        db=db,
        clinic_id=payload.clinic_id,
        patient_id=payload.patient_id,
        doctor_id=doctor_id,
        status_id=pending_status.id,
    )

    validated_image = validate_exam_file(file)

    exam = Exam(
        clinic_id=payload.clinic_id,
        patient_id=payload.patient_id,
        doctor_id=doctor_id,
        status_id=pending_status.id,
        exam_type=payload.exam_type,
        exam_date=payload.exam_date,
        title=payload.title,
        description=payload.description,
        clinical_indication=payload.clinical_indication,
    )

    db.add(exam)
    db.flush()

    stored_file_path = None

    try:
        stored_file_path = store_validated_exam_file(
            validated_image,
            clinic_id=exam.clinic_id,
            patient_id=exam.patient_id,
            exam_id=exam.id,
        )

        stored_file_reference = (
            serialize_exam_file_path(
                stored_file_path
            )
        )
        exam.file_path = stored_file_reference
        exam.file_name = stored_file_path.name
        exam.file_mime_type = validated_image.mime_type

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
                "status_name": initial_status_name,
                "transition_action": ExamTransitionAction.CREATE.value,
                "exam_type": exam.exam_type,
                "exam_date": exam.exam_date.isoformat() if exam.exam_date else None,
                "title": exam.title,
            },
        )
        create_audit_log(
            db=db,
            user_id=current_user.id,
            clinic_id=exam.clinic_id,
            action=AuditAction.UPLOAD,
            entity=AuditEntity.EXAM,
            entity_id=exam.id,
            description="Imagem inicial do exame armazenada.",
            new_data={
                "file_name": exam.file_name,
                "file_mime_type": validated_image.mime_type,
                "file_size_bytes": validated_image.size_bytes,
                "image_width": validated_image.width,
                "image_height": validated_image.height,
                "sha256": validated_image.sha256,
            },
        )

        db.commit()

    except HTTPException:
        db.rollback()
        if stored_file_path is not None:
            delete_exam_file_safely(str(stored_file_path))
        raise
    except Exception as exc:
        db.rollback()
        if stored_file_path is not None:
            delete_exam_file_safely(str(stored_file_path))
        raise HTTPException(
            status_code=500,
            detail="Erro ao criar exame.",
        ) from exc

    db.refresh(exam)

    exam = get_exam_model_by_id(db=db, exam_id=exam.id)

    return build_exam_response(exam, current_user=current_user)


def update_exam(
    db: Session,
    exam_id: int,
    payload: ExamUpdate,
    current_user: User,
) -> dict:
    """Atualiza metadados somente antes da revisão clínica."""

    exam = get_exam_model_for_update(db=db, exam_id=exam_id)
    validate_user_can_access_exam(current_user=current_user, exam=exam)
    current_status = exam.status.name if exam.status else None
    ensure_exam_is_editable(current_status)

    update_data = model_dump_update(payload)
    if not update_data:
        db.rollback()
        return build_exam_response(exam, current_user=current_user)

    validate_user_can_access_clinic(current_user=current_user, clinic_id=exam.clinic_id)
    old_data = {
        "exam_type": exam.exam_type,
        "exam_date": exam.exam_date.isoformat() if exam.exam_date else None,
        "title": exam.title,
        "description": exam.description,
        "clinical_indication": exam.clinical_indication,
    }
    apply_update_data(exam, update_data)
    audit_new_data = {
        "exam_type": exam.exam_type,
        "exam_date": exam.exam_date.isoformat() if exam.exam_date else None,
        "title": exam.title,
        "description": exam.description,
        "clinical_indication": exam.clinical_indication,
    }
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.UPDATE,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Dados básicos do exame atualizados.",
        old_data=old_data,
        new_data=audit_new_data,
    )
    db.commit()
    exam = get_exam_model_by_id(db=db, exam_id=exam.id)
    return build_exam_response(exam, current_user=current_user)


def cancel_exam(
    db: Session,
    exam_id: int,
    current_user: User,
) -> dict:
    """Cancela pending/processing; repetição sobre canceled é idempotente."""

    exam = get_exam_model_for_update(db=db, exam_id=exam_id)
    validate_user_can_access_exam(current_user=current_user, exam=exam)
    current_status = exam.status.name if exam.status else None

    if current_status == StatusName.CANCELED.value:
        db.rollback()
        return build_exam_response(exam, current_user=current_user)

    target_name = get_transition_target(current_status, ExamTransitionAction.CANCEL)
    target_status = get_status_by_name_and_applies_to(
        db=db,
        name=target_name,
        applies_to=StatusScope.EXAM.value,
    )
    old_data, new_data = transition_audit_payload(
        old_status_id=exam.status_id,
        old_status_name=current_status or "",
        new_status_id=target_status.id,
        new_status_name=target_name,
        action=ExamTransitionAction.CANCEL,
    )
    exam.status_id = target_status.id
    clear_exam_analysis_claim(db, exam)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.CANCEL_EXAM,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Exame cancelado.",
        old_data=old_data,
        new_data=new_data,
    )
    db.commit()
    exam = get_exam_model_by_id(db=db, exam_id=exam.id)
    return build_exam_response(exam, current_user=current_user)


def restore_exam(
    db: Session,
    exam_id: int,
    current_user: User,
) -> dict:
    """Restaura canceled/failed para pending de forma idempotente."""

    exam = get_exam_model_for_update(db=db, exam_id=exam_id)
    validate_user_can_access_exam(current_user=current_user, exam=exam)
    current_status = exam.status.name if exam.status else None

    if current_status == StatusName.PENDING.value:
        db.rollback()
        return build_exam_response(exam, current_user=current_user)

    target_name = get_transition_target(current_status, ExamTransitionAction.RESTORE)
    if exam.ai_analysis:
        raise HTTPException(
            status_code=409,
            detail="Exame com análise concluída não pode retornar à fila de análise.",
        )
    if not exam.file_path:
        raise HTTPException(status_code=409, detail="Não é possível restaurar exame sem arquivo.")
    file_path = resolve_safe_exam_file_path(exam.file_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=409,
            detail="O arquivo do exame não está disponível para nova análise.",
        )

    target_status = get_status_by_name_and_applies_to(
        db=db,
        name=target_name,
        applies_to=StatusScope.EXAM.value,
    )
    old_data, new_data = transition_audit_payload(
        old_status_id=exam.status_id,
        old_status_name=current_status or "",
        new_status_id=target_status.id,
        new_status_name=target_name,
        action=ExamTransitionAction.RESTORE,
    )
    exam.status_id = target_status.id
    clear_exam_analysis_claim(db, exam)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.RESTORE_EXAM,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Exame restaurado e disponibilizado para nova análise.",
        old_data=old_data,
        new_data=new_data,
    )
    db.commit()
    exam = get_exam_model_by_id(db=db, exam_id=exam.id)
    return build_exam_response(exam, current_user=current_user)


def slugify_exam_download_component(
    value: str | None,
    *,
    fallback: str,
    max_length: int = 60,
) -> str:
    """Normaliza componentes do nome público do arquivo."""

    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")

    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        ascii_value,
    ).strip("-").lower()

    return slug[:max_length].strip("-") or fallback


def build_exam_download_filename(exam: Exam, file_path) -> str:
    """Gera nome amigável sem revelar o UUID físico armazenado."""

    patient_name = exam.patient.name if exam.patient else None

    patient_slug = slugify_exam_download_component(
        patient_name,
        fallback="paciente",
    )

    date_part = exam.exam_date.isoformat() if exam.exam_date else "sem-data"

    extension = (
        ".png"
        if exam.file_mime_type == "image/png"
        or file_path.suffix.lower() == ".png"
        else ".jpg"
    )

    return (
        f"exame-{exam.id}-"
        f"{patient_slug}-"
        f"{date_part}"
        f"{extension}"
    )


def get_authorized_exam_file(
    db: Session,
    exam_id: int,
    current_user: User,
):
    """Resolve a imagem original após validar usuário, escopo e caminho."""

    exam = get_exam_model_by_id(
        db=db,
        exam_id=exam_id,
    )

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )

    if not exam.file_path:
        raise HTTPException(
            status_code=404,
            detail="Este exame não possui arquivo vinculado.",
        )

    file_path = resolve_safe_exam_file_path(
        exam.file_path,
    )

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Arquivo físico não encontrado no servidor.",
        )

    return exam, file_path


def preview_exam_file(
    db: Session,
    exam_id: int,
    current_user: User,
):
    """
    Retorna a imagem original para visualização autenticada.

    A abertura automática da tela não é registrada como download manual.
    """

    exam, file_path = get_authorized_exam_file(
        db=db,
        exam_id=exam_id,
        current_user=current_user,
    )

    return FileResponse(
        path=file_path,
        filename=build_exam_download_filename(
            exam,
            file_path,
        ),
        media_type=exam.file_mime_type,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "private, no-store",
        },
    )


def download_exam_file(
    db: Session,
    exam_id: int,
    current_user: User,
):
    """Retorna a imagem original como download explicitamente solicitado."""

    exam, file_path = get_authorized_exam_file(
        db=db,
        exam_id=exam_id,
        current_user=current_user,
    )

    download_name = build_exam_download_filename(
        exam,
        file_path,
    )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.DOWNLOAD,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Download da imagem original autorizado.",
        new_data={
            "file_name": exam.file_name,
            "file_mime_type": exam.file_mime_type,
            "download_name": download_name,
            "delivery_mode": "attachment",
        },
    )

    db.commit()

    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type=exam.file_mime_type,
        content_disposition_type="attachment",
        headers={
            "Cache-Control": "no-store",
        },
    )


def get_authorized_gradcam_file(
    db: Session,
    exam_id: int,
    current_user: User,
):
    """Resolve o mapa de atribuição da IA após validar perfil, escopo e caminho."""

    exam = get_exam_model_by_id(
        db=db,
        exam_id=exam_id,
    )

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )

    role_name = (
        current_user.role.name
        if current_user.role
        else None
    )

    if role_name not in {
        RoleName.ADMIN_MASTER.value,
        RoleName.DOCTOR.value,
    }:
        raise HTTPException(
            status_code=403,
            detail=(
                "Somente médicos e o administrador podem "
                "acessar o resultado visual da IA."
            ),
        )

    analysis = exam.ai_analysis

    if not analysis or not analysis.gradcam_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "Este exame não possui mapa de atribuição da IA "
                "disponível."
            ),
        )

    file_path = resolve_safe_gradcam_path(
        analysis.gradcam_path
    )

    media_type = (
        "image/png"
        if file_path.suffix.lower() == ".png"
        else "image/jpeg"
    )

    return exam, analysis, file_path, media_type


def build_gradcam_download_filename(
    exam: Exam,
    file_path,
) -> str:
    """Gera nome público amigável para o mapa de atribuição da IA."""

    patient_name = (
        exam.patient.name
        if exam.patient
        else None
    )

    patient_slug = slugify_exam_download_component(
        patient_name,
        fallback="paciente",
    )

    date_part = (
        exam.exam_date.isoformat()
        if exam.exam_date
        else "sem-data"
    )

    extension = (
        ".png"
        if file_path.suffix.lower() == ".png"
        else ".jpg"
    )

    return (
        f"mapa-atribuicao-exame-{exam.id}-"
        f"{patient_slug}-"
        f"{date_part}"
        f"{extension}"
    )


def preview_exam_ai_file(
    db: Session,
    exam_id: int,
    current_user: User,
):
    """
    Retorna o mapa de atribuição da IA para visualização inline.

    A prévia automática não registra download manual.
    """

    exam, _, file_path, media_type = (
        get_authorized_gradcam_file(
            db=db,
            exam_id=exam_id,
            current_user=current_user,
        )
    )

    return FileResponse(
        path=file_path,
        filename=build_gradcam_download_filename(
            exam,
            file_path,
        ),
        media_type=media_type,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "private, no-store",
        },
    )


def download_exam_ai_file(
    db: Session,
    exam_id: int,
    current_user: User,
):
    """Retorna o mapa de atribuição da IA como download explicitamente solicitado."""

    exam, analysis, file_path, media_type = (
        get_authorized_gradcam_file(
            db=db,
            exam_id=exam_id,
            current_user=current_user,
        )
    )

    download_name = build_gradcam_download_filename(
        exam,
        file_path,
    )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.DOWNLOAD,
        entity=AuditEntity.AI_ANALYSIS,
        entity_id=analysis.id,
        description="Download do mapa de atribuição da IA autorizado.",
        new_data={
            "artifact_type": "ai_attribution_map",
            "media_type": media_type,
            "download_name": download_name,
            "delivery_mode": "attachment",
        },
    )

    db.commit()

    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type=media_type,
        content_disposition_type="attachment",
        headers={
            "Cache-Control": "no-store",
        },
    )


def mark_exam_ai_failed(
    db: Session,
    exam_id: int,
    error_message: str | None = None,
) -> dict:
    """Registra processing -> failed sem sobrescrever transição concorrente."""

    exam = get_exam_model_for_update(db=db, exam_id=exam_id)
    current_status = exam.status.name if exam.status else None
    target_name = get_transition_target(current_status, ExamTransitionAction.ANALYSIS_FAILED)
    target_status = get_status_by_name_and_applies_to(
        db=db,
        name=target_name,
        applies_to=StatusScope.EXAM.value,
    )
    old_data, new_data = transition_audit_payload(
        old_status_id=exam.status_id,
        old_status_name=current_status or "",
        new_status_id=target_status.id,
        new_status_name=target_name,
        action=ExamTransitionAction.ANALYSIS_FAILED,
        error_recorded=bool(error_message),
    )
    exam.status_id = target_status.id
    clear_exam_analysis_claim(db, exam)
    safe_error = str(error_message)[:500] if error_message else None
    create_audit_log(
        db=db,
        user_id=None,
        clinic_id=exam.clinic_id,
        action=AuditAction.AI_ANALYSIS_FAILED,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description=f"Falha na análise de IA: {safe_error}" if safe_error else "Falha na análise de IA.",
        old_data=old_data,
        new_data=new_data,
    )
    db.commit()
    exam = get_exam_model_by_id(db=db, exam_id=exam.id)
    return build_exam_response(exam)


def get_exam_history(
    db: Session,
    exam_id: int,
    current_user: User,
) -> dict:
    """
    Retorna o histórico de eventos/alterações de status de um exame (RF36).

    Regra: quem passa pela mesma validação de escopo usada nos detalhes do
    exame pode ver seu histórico. Não é preciso ter `audit_logs:read`, que
    permanece exclusiva da área administrativa global.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )

    return list_entity_audit_logs(
        db=db,
        entity=AuditEntity.EXAM.value,
        entity_id=exam_id,
        limit=200,
    )


def review_exam(
    db: Session,
    exam_id: int,
    payload: ExamMedicalReview,
    current_user: User,
) -> dict:
    """Registra exatamente uma revisão médica e encerra o exame."""

    exam = get_exam_model_for_update(db=db, exam_id=exam_id)
    if not current_user.role or current_user.role.name != RoleName.DOCTOR.value:
        raise HTTPException(status_code=403, detail="Apenas usuários com perfil médico podem revisar exames.")
    validate_user_can_access_exam(current_user=current_user, exam=exam)
    if not exam.ai_analysis:
        raise HTTPException(status_code=409, detail="O exame ainda não possui análise de IA concluída.")

    current_status = exam.status.name if exam.status else None
    action = (
        ExamTransitionAction.REVIEW_DIVERGENCE
        if payload.has_discrepancy
        else ExamTransitionAction.REVIEW_CONFIRM
    )
    target_name = get_transition_target(current_status, action)
    target_status = get_status_by_name_and_applies_to(
        db=db,
        name=target_name,
        applies_to=StatusScope.EXAM.value,
    )
    old_data, new_data = transition_audit_payload(
        old_status_id=exam.status_id,
        old_status_name=current_status or "",
        new_status_id=target_status.id,
        new_status_name=target_name,
        action=action,
        has_discrepancy=payload.has_discrepancy,
        reviewed_by_id=current_user.id,
    )
    reviewed_at = datetime.now(timezone.utc)
    old_data.update(
        {
            "findings": exam.findings,
            "conclusion": exam.conclusion,
            "reviewed_by_id": exam.reviewed_by_id,
            "reviewed_at": exam.reviewed_at.isoformat() if exam.reviewed_at else None,
        }
    )
    new_data.update(
        {
            "findings": payload.findings,
            "conclusion": payload.conclusion,
            "reviewed_by_id": current_user.id,
            "reviewed_at": reviewed_at.isoformat(),
        }
    )
    exam.findings = payload.findings
    exam.conclusion = payload.conclusion
    exam.reviewed_by_id = current_user.id
    exam.reviewed_at = reviewed_at
    exam.status_id = target_status.id
    clear_exam_analysis_claim(db, exam)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.REVIEW_EXAM,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description=(
            "Exame revisado com divergência sinalizada pelo médico."
            if payload.has_discrepancy
            else "Exame revisado e confirmado pelo médico."
        ),
        old_data=old_data,
        new_data=new_data,
    )
    db.commit()
    exam = get_exam_model_by_id(db=db, exam_id=exam.id)
    return build_exam_response(exam, current_user=current_user)


def replace_exam_file(
    db: Session,
    exam_id: int,
    file: UploadFile,
    current_user: User,
) -> dict:
    """Substitui imagem em pending/failed e mantém o exame pronto para análise."""

    exam = get_exam_model_for_update(db=db, exam_id=exam_id)
    validate_user_can_access_exam(current_user=current_user, exam=exam)
    current_status = exam.status.name if exam.status else None
    target_name = get_transition_target(current_status, ExamTransitionAction.REPLACE_FILE)
    if exam.analysis_in_progress:
        raise HTTPException(status_code=409, detail="A imagem não pode ser substituída durante a análise de IA.")
    if exam.ai_analysis:
        raise HTTPException(status_code=409, detail="A imagem não pode ser substituída após uma análise concluída.")
    validated_image = validate_exam_file(file)

    old_file_path = exam.file_path
    stored_file_path = None
    try:
        stored_file_path = store_validated_exam_file(
            validated_image,
            clinic_id=exam.clinic_id,
            patient_id=exam.patient_id,
            exam_id=exam.id,
        )
        target_status = get_status_by_name_and_applies_to(
            db=db,
            name=target_name,
            applies_to=StatusScope.EXAM.value,
        )
        old_data = {
            "file_name": exam.file_name,
            "file_mime_type": exam.file_mime_type,
            "status_id": exam.status_id,
            "status_name": current_status,
        }
        stored_file_reference = (
            serialize_exam_file_path(
                stored_file_path
            )
        )
        exam.file_path = stored_file_reference
        exam.file_name = stored_file_path.name
        exam.file_mime_type = validated_image.mime_type
        exam.status_id = target_status.id
        clear_exam_analysis_claim(db, exam)
        new_data = {
            "file_name": exam.file_name,
            "file_mime_type": exam.file_mime_type,
            "file_size_bytes": validated_image.size_bytes,
            "image_width": validated_image.width,
            "image_height": validated_image.height,
            "sha256": validated_image.sha256,
            "status_id": target_status.id,
            "status_name": target_name,
            "transition_action": ExamTransitionAction.REPLACE_FILE.value,
        }
        create_audit_log(
            db=db,
            user_id=current_user.id,
            clinic_id=exam.clinic_id,
            action=AuditAction.UPLOAD,
            entity=AuditEntity.EXAM,
            entity_id=exam.id,
            description="Imagem do exame substituída.",
            old_data=old_data,
            new_data=new_data,
        )
        db.commit()
    except HTTPException:
        db.rollback()
        if stored_file_path is not None:
            delete_exam_file_safely(str(stored_file_path))
        raise
    except Exception as exc:
        db.rollback()
        if stored_file_path is not None:
            delete_exam_file_safely(str(stored_file_path))
        raise HTTPException(status_code=500, detail="Erro ao substituir imagem do exame.") from exc

    if (
        old_file_path
        and old_file_path
        != stored_file_reference
    ):
        delete_exam_file_safely(old_file_path)
    exam = get_exam_model_by_id(db=db, exam_id=exam.id)
    return build_exam_response(exam, current_user=current_user)


async def analyze_exam(
    db: Session,
    exam_id: int,
    current_user: User,
) -> dict:
    """Executa a IA com claim atômico e resposta idempotente após sucesso."""

    exam = get_exam_model_by_id(db=db, exam_id=exam_id)
    ensure_user_can_access_exam(
        current_user=current_user,
        exam=exam,
        detail="Você não tem permissão para analisar este exame.",
    )
    if exam.ai_analysis:
        return build_ai_analysis_response(exam.ai_analysis)
    current_status = exam.status.name if exam.status else None
    # Valida pending -> processing antes de adquirir o claim atômico.
    get_transition_target(current_status, ExamTransitionAction.START_PROCESSING)
    if not exam.file_path:
        raise HTTPException(status_code=409, detail="O exame precisa ter um arquivo antes da análise de IA.")
    claim_exam_for_analysis(
        db=db,
        exam_id=exam_id,
        current_user=current_user,
    )
    # Um concorrente pode ter concluído entre a primeira leitura e o claim.
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)
    if exam.ai_analysis:
        return build_ai_analysis_response(exam.ai_analysis)

    try:
        file_path = resolve_safe_exam_file_path(exam.file_path)
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError("Arquivo do exame não encontrado no disco.")
        image_bytes = file_path.read_bytes()
    except (HTTPException, OSError) as exc:
        try:
            mark_exam_ai_failed(db=db, exam_id=exam_id, error_message=str(exc))
        except HTTPException as conflict:
            raise HTTPException(status_code=409, detail="O estado do exame mudou durante a análise.") from conflict
        raise HTTPException(
            status_code=500,
            detail="Arquivo do exame não encontrado. Exame marcado como falha.",
        ) from exc

    started_at = datetime.now(timezone.utc)
    try:
        prediction = await request_prediction(
            image_bytes=image_bytes,
            filename=exam.file_name or file_path.name,
            content_type=exam.file_mime_type or "application/octet-stream",
            exam_type=exam.exam_type,
        )
    except AIServiceError as exc:
        try:
            mark_exam_ai_failed(db=db, exam_id=exam_id, error_message=str(exc))
        except HTTPException as conflict:
            raise HTTPException(status_code=409, detail="O estado do exame mudou durante a análise.") from conflict
        raise HTTPException(status_code=502, detail=f"Falha ao processar exame no serviço de IA: {exc}") from exc

    processing_time_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
    payload = AIAnalysisCreate(
        exam_id=exam_id,
        prediction_label=prediction["label"],
        prediction_class=prediction["prediction_class"],
        confidence=prediction["confidence"],
        model_name=prediction["model_name"],
        model_version=prediction["model_version"],
        gradcam_path=(
            serialize_gradcam_path(
                Path(
                    prediction[
                        "gradcam_path"
                    ]
                )
            )
            if (
                prediction[
                    "gradcam_available"
                ]
                and prediction[
                    "gradcam_path"
                ]
            )
            else None
        ),
        processing_time_ms=processing_time_ms,
        raw_response=json.dumps(
            prediction,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ),
    )
    return create_ai_analysis(db=db, payload=payload, current_user=current_user)
