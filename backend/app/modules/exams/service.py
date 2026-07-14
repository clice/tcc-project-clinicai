"""
Service do módulo de exames.

Concentra as regras de negócio relacionadas aos exames.
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

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
from app.modules.ai_analysis.model import AIAnalysis
from app.modules.ai_analysis.schema import AIAnalysisCreate
from app.modules.ai_analysis.service import build_ai_analysis_response, create_ai_analysis
from app.modules.audit_logs.service import create_audit_log, list_entity_audit_logs
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
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


from app.core.config import settings

UPLOAD_DIR = Path(settings.upload_dir) / "exams"
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024

ALLOWED_EXAM_MIME_TYPES = {
    "image/jpeg",
    "image/png",
}

ALLOWED_EXAM_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


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
        "reviewed_by_id": exam.reviewed_by_id,
        "reviewed_by_name": exam.reviewed_by.name if exam.reviewed_by else None,
        "reviewed_at": exam.reviewed_at,
        "file_path": exam.file_path,
        "file_name": exam.file_name,
        "file_mime_type": exam.file_mime_type,
        "ai_prediction_label": ai_prediction_label,
        "ai_prediction_class": ai_prediction_class,
        "created_at": exam.created_at,
        "updated_at": exam.updated_at,
    }


def build_exam_storage_dir(patient_id: int) -> Path:
    """
    Cria e retorna o diretório seguro do paciente para armazenar exames.
    """
    patient_dir = UPLOAD_DIR / str(patient_id)
    patient_dir.mkdir(parents=True, exist_ok=True)

    return patient_dir


def build_exam_file_name(
    *,
    exam_id: int,
    patient_id: int,
    file_extension: str,
) -> str:
    """
    Gera um nome padronizado e seguro para o arquivo do exame.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid4().hex[:8]

    return f"exam_{exam_id}_patient_{patient_id}_{timestamp}_{short_uuid}{file_extension}"


def resolve_safe_exam_file_path(file_path: str) -> Path:
    """
    Garante que o arquivo solicitado está dentro da pasta segura de uploads.
    Evita path traversal no download.
    """
    base_dir = UPLOAD_DIR.resolve()
    resolved_path = Path(file_path).resolve()

    try:
        resolved_path.relative_to(base_dir)
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail="Caminho de arquivo inválido.",
        ) from exc

    return resolved_path


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


def claim_exam_for_analysis(db: Session, exam_id: int) -> None:
    """Adquire de forma atômica o direito de executar a inferência.

    A atualização condicional impede que clique duplo, retry do navegador ou
    duas sessões disparem o serviço de IA mais de uma vez para o mesmo exame.
    """

    processing_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.PROCESSING.value,
        applies_to=StatusScope.EXAM.value,
    )
    claimed = (
        db.query(Exam)
        .filter(
            Exam.id == exam_id,
            Exam.status_id == processing_status.id,
            Exam.analysis_in_progress.is_(False),
        )
        .update(
            {
                Exam.analysis_in_progress: True,
                Exam.analysis_started_at: datetime.now(timezone.utc),
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
            ExamTransitionAction.ANALYSIS_SUCCEEDED,
        )
        raise HTTPException(status_code=409, detail="Não foi possível iniciar a análise.")

    db.commit()


def clear_exam_analysis_claim(db: Session, exam: Exam) -> None:
    """Libera o marcador de execução atual dentro da transação aberta."""

    exam.analysis_in_progress = False
    exam.analysis_started_at = None


def validate_exam_file(file: UploadFile) -> None:
    """
    Valida o tipo de arquivo enviado no upload para o exame.
    """
    if file.content_type not in ALLOWED_EXAM_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Tipo de arquivo não permitido. Use JPG ou PNG.",
        )

    file_extension = Path(file.filename or "").suffix.lower()

    if file_extension not in ALLOWED_EXAM_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Extensão de arquivo não permitida.",
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Arquivo vazio não é permitido.",
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Tamanho máximo permitido: {settings.max_upload_size_mb} MB.",
        )
        

def delete_exam_file_safely(file_path: str | None) -> None:
    """
    Remove com segurança um arquivo antigo de exame.

    A função só remove arquivos dentro da pasta segura de uploads.
    Se o arquivo não existir, simplesmente ignora.
    """
    if not file_path:
        return

    try:
        resolved_path = resolve_safe_exam_file_path(file_path)
    except HTTPException:
        return

    if resolved_path.exists() and resolved_path.is_file():
        resolved_path.unlink()
        
        
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
    Status inicial: PROCESSING.
    """
    doctor_id = payload.doctor_id

    if current_user.role and current_user.role.name == RoleName.DOCTOR.value:
        doctor_id = current_user.id

    validate_user_can_access_clinic(
        current_user=current_user,
        clinic_id=payload.clinic_id,
    )

    processing_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.PROCESSING.value,
        applies_to=StatusScope.EXAM.value,
    )

    validate_exam_relationships(
        db=db,
        clinic_id=payload.clinic_id,
        patient_id=payload.patient_id,
        doctor_id=doctor_id,
        status_id=processing_status.id,
    )

    validate_exam_file(file)

    exam = Exam(
        clinic_id=payload.clinic_id,
        patient_id=payload.patient_id,
        doctor_id=doctor_id,
        status_id=processing_status.id,
        exam_type=payload.exam_type,
        exam_date=payload.exam_date,
        title=payload.title,
        description=payload.description,
        clinical_indication=payload.clinical_indication,
    )

    db.add(exam)
    db.flush()

    patient_dir = build_exam_storage_dir(patient_id=exam.patient_id)

    file_extension = Path(file.filename or "").suffix.lower()

    stored_file_name = build_exam_file_name(
        exam_id=exam.id,
        patient_id=exam.patient_id,
        file_extension=file_extension,
    )

    stored_file_path = patient_dir / stored_file_name

    try:
        with stored_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        exam.file_path = str(stored_file_path)
        exam.file_name = stored_file_name
        exam.file_mime_type = file.content_type

        create_audit_log(
            db=db,
            user_id=current_user.id,
            clinic_id=exam.clinic_id,
            action=AuditAction.CREATE,
            entity=AuditEntity.EXAM,
            entity_id=exam.id,
            description="Exame cadastrado com imagem obrigatória.",
            new_data={
                "id": exam.id,
                "clinic_id": exam.clinic_id,
                "patient_id": exam.patient_id,
                "doctor_id": exam.doctor_id,
                "status_name": StatusName.PROCESSING.value,
                "file_name": exam.file_name,
            },
        )

        db.commit()

    except Exception as exc:
        db.rollback()
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
    """Restaura canceled/failed para processing de forma idempotente."""

    exam = get_exam_model_for_update(db=db, exam_id=exam_id)
    validate_user_can_access_exam(current_user=current_user, exam=exam)
    current_status = exam.status.name if exam.status else None

    if current_status == StatusName.PROCESSING.value:
        db.rollback()
        return build_exam_response(exam, current_user=current_user)

    target_name = get_transition_target(current_status, ExamTransitionAction.RESTORE)
    if exam.ai_analysis:
        raise HTTPException(
            status_code=409,
            detail="Exame com análise concluída não pode retornar ao processamento.",
        )
    if not exam.file_path:
        raise HTTPException(status_code=409, detail="Não é possível restaurar exame sem arquivo.")
    file_path = resolve_safe_exam_file_path(exam.file_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=409,
            detail="O arquivo do exame não está disponível para reprocessamento.",
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
        description="Exame restaurado para processamento.",
        old_data=old_data,
        new_data=new_data,
    )
    db.commit()
    exam = get_exam_model_by_id(db=db, exam_id=exam.id)
    return build_exam_response(exam, current_user=current_user)

def upload_exam_file(
    db: Session,
    exam_id: int,
    file: UploadFile,
    current_user: User,
) -> dict:
    """
    Faz upload físico do arquivo do exame e atualiza metadados.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    validate_user_can_access_exam(
        current_user=current_user,
        exam=exam,
    )

    if exam.status and exam.status.name == StatusName.CANCELED.value:
        raise HTTPException(
            status_code=400,
            detail="Não é possível enviar arquivo para um exame cancelado.",
        )

    if file.content_type not in ALLOWED_EXAM_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Tipo de arquivo não permitido. Use PDF, JPG ou PNG.",
        )

    file_extension = Path(file.filename or "").suffix.lower()

    if file_extension not in ALLOWED_EXAM_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Extensão de arquivo não permitida.",
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Tamanho máximo permitido: {settings.max_upload_size_mb} MB.",
        )

    patient_dir = build_exam_storage_dir(patient_id=exam.patient_id)

    stored_file_name = build_exam_file_name(
        exam_id=exam.id,
        patient_id=exam.patient_id,
        file_extension=file_extension,
    )

    stored_file_path = patient_dir / stored_file_name

    old_file_path = exam.file_path

    old_data = {
        "file_path": exam.file_path,
        "file_name": exam.file_name,
        "file_mime_type": exam.file_mime_type,
        "status_id": exam.status_id,
        "status_name": exam.status.name if exam.status else None,
    }

    try:
        with stored_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Erro ao salvar arquivo do exame.",
        ) from exc

    processing_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.PROCESSING.value,
        applies_to=StatusScope.EXAM.value,
    )

    exam.file_path = str(stored_file_path)
    exam.file_name = stored_file_name
    exam.file_mime_type = file.content_type
    exam.status_id = processing_status.id

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.UPLOAD,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Arquivo de exame enviado.",
        old_data=old_data,
        new_data={
            "file_path": exam.file_path,
            "file_name": exam.file_name,
            "file_mime_type": exam.file_mime_type,
            "status_id": exam.status_id,
            "status_name": StatusName.PROCESSING.value,
        },
    )

    try:
        db.commit()
    except Exception as exc:
        db.rollback()

        if stored_file_path.exists() and stored_file_path.is_file():
            stored_file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar dados do exame.",
        ) from exc

    db.refresh(exam)

    if old_file_path and old_file_path != str(stored_file_path):
        delete_exam_file_safely(old_file_path)

    exam = get_exam_model_by_id(db=db, exam_id=exam.id)

    return build_exam_response(exam, current_user=current_user)


def download_exam_file(
    db: Session,
    exam_id: int,
    current_user: User,
):
    """
    Retorna o arquivo físico vinculado ao exame.
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

    file_path = resolve_safe_exam_file_path(exam.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Arquivo físico não encontrado no servidor.",
        )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        clinic_id=exam.clinic_id,
        action=AuditAction.DOWNLOAD,
        entity=AuditEntity.EXAM,
        entity_id=exam.id,
        description="Arquivo de exame baixado.",
        new_data={
            "file_path": exam.file_path,
            "file_name": exam.file_name,
            "file_mime_type": exam.file_mime_type,
        },
    )

    db.commit()

    return FileResponse(
        path=file_path,
        filename=exam.file_name,
        media_type=exam.file_mime_type,
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
    exam.findings = payload.findings
    exam.conclusion = payload.conclusion
    exam.reviewed_by_id = current_user.id
    exam.reviewed_at = datetime.now(timezone.utc)
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
    """Substitui imagem somente em processing/failed, sem corrida com IA."""

    exam = get_exam_model_for_update(db=db, exam_id=exam_id)
    validate_user_can_access_exam(current_user=current_user, exam=exam)
    current_status = exam.status.name if exam.status else None
    target_name = get_transition_target(current_status, ExamTransitionAction.REPLACE_FILE)
    if exam.analysis_in_progress:
        raise HTTPException(status_code=409, detail="A imagem não pode ser substituída durante a análise de IA.")
    if exam.ai_analysis:
        raise HTTPException(status_code=409, detail="A imagem não pode ser substituída após uma análise concluída.")
    validate_exam_file(file)

    old_file_path = exam.file_path
    patient_dir = build_exam_storage_dir(patient_id=exam.patient_id)
    file_extension = Path(file.filename or "").suffix.lower()
    stored_file_name = build_exam_file_name(
        exam_id=exam.id,
        patient_id=exam.patient_id,
        file_extension=file_extension,
    )
    stored_file_path = patient_dir / stored_file_name
    try:
        with stored_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
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
        exam.file_path = str(stored_file_path)
        exam.file_name = stored_file_name
        exam.file_mime_type = file.content_type
        exam.status_id = target_status.id
        clear_exam_analysis_claim(db, exam)
        new_data = {
            "file_name": exam.file_name,
            "file_mime_type": exam.file_mime_type,
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
        delete_exam_file_safely(str(stored_file_path))
        raise
    except Exception as exc:
        db.rollback()
        delete_exam_file_safely(str(stored_file_path))
        raise HTTPException(status_code=500, detail="Erro ao substituir imagem do exame.") from exc

    if old_file_path and old_file_path != str(stored_file_path):
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
    # Valida processing -> awaiting_review antes de iniciar a chamada externa.
    get_transition_target(current_status, ExamTransitionAction.ANALYSIS_SUCCEEDED)
    if not exam.file_path:
        raise HTTPException(status_code=409, detail="O exame precisa ter um arquivo antes da análise de IA.")
    file_path = resolve_safe_exam_file_path(exam.file_path)
    if not file_path.exists() or not file_path.is_file():
        try:
            mark_exam_ai_failed(db=db, exam_id=exam_id, error_message="Arquivo do exame não encontrado no disco.")
        except HTTPException as conflict:
            raise HTTPException(status_code=409, detail="O estado do exame mudou durante a análise.") from conflict
        raise HTTPException(status_code=500, detail="Arquivo do exame não encontrado. Exame marcado como falha.")

    claim_exam_for_analysis(db=db, exam_id=exam_id)
    # Um concorrente pode ter concluído entre a primeira leitura e o claim.
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)
    if exam.ai_analysis:
        return build_ai_analysis_response(exam.ai_analysis)

    image_bytes = file_path.read_bytes()
    started_at = datetime.now(timezone.utc)
    try:
        prediction = await request_prediction(
            image_bytes=image_bytes,
            filename=exam.file_name or file_path.name,
            content_type=exam.file_mime_type or "application/octet-stream",
        )
    except AIServiceError as exc:
        try:
            mark_exam_ai_failed(db=db, exam_id=exam_id, error_message=str(exc))
        except HTTPException as conflict:
            raise HTTPException(status_code=409, detail="O estado do exame mudou durante a análise.") from conflict
        raise HTTPException(status_code=502, detail=f"Falha ao processar exame no serviço de IA: {exc}") from exc

    processing_time_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
    label = prediction.get("label")
    prediction_class = 1 if label == "abnormal" else 0 if label == "normal" else None
    payload = AIAnalysisCreate(
        exam_id=exam_id,
        prediction_label=label or "desconhecido",
        prediction_class=prediction_class,
        confidence=prediction.get("confidence", 0.0),
        model_name=prediction.get("model_name", "desconhecido"),
        model_version=prediction.get("model_version", "0.0.0"),
        gradcam_path=prediction.get("gradcam_path"),
        processing_time_ms=processing_time_ms,
        raw_response=str(prediction),
    )
    return create_ai_analysis(db=db, payload=payload, current_user=current_user)
