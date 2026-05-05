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

from app.common.constants import AuditAction, AuditEntity, RoleName, StatusName, StatusScope
from app.modules.audit_logs.service import create_audit_log
from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.exams.schema import ExamCreate, ExamUpdate
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
    "application/pdf",
}

ALLOWED_EXAM_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".pdf",
}


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
        "file_path": exam.file_path,
        "file_name": exam.file_name,
        "file_mime_type": exam.file_mime_type,
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
    Cria um novo exame com status inicial pendente.
    """
    doctor_id = payload.doctor_id

    if current_user.role and current_user.role.name == RoleName.DOCTOR.value:
        doctor_id = current_user.id

    validate_user_can_access_clinic(
        current_user=current_user,
        clinic_id=payload.clinic_id,
    )

    pending_status = get_status_by_name_and_applies_to(
        db=db,
        name=StatusName.PENDING.value,
        applies_to=StatusScope.EXAM.value,
    )

    validate_exam_relationships(
        db=db,
        clinic_id=payload.clinic_id,
        patient_id=payload.patient_id,
        doctor_id=doctor_id,
        status_id=pending_status.id,
    )

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
        findings=payload.findings,
        conclusion=payload.conclusion,
    )

    db.add(exam)
    db.flush()

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

    if exam.status and exam.status.name == StatusName.CANCELED.value:
        raise HTTPException(
            status_code=400,
            detail="Não é possível editar um exame cancelado.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return build_exam_response(exam)

    clinic_id = update_data.get("clinic_id", exam.clinic_id)
    patient_id = update_data.get("patient_id", exam.patient_id)
    doctor_id = update_data.get("doctor_id", exam.doctor_id)

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
        status_id=exam.status_id,
    )

    old_data = {
        "clinic_id": exam.clinic_id,
        "patient_id": exam.patient_id,
        "doctor_id": exam.doctor_id,
        "exam_type": exam.exam_type,
        "exam_date": str(exam.exam_date) if exam.exam_date else None,
        "title": exam.title,
        "description": exam.description,
        "clinical_indication": exam.clinical_indication,
        "findings": exam.findings,
        "conclusion": exam.conclusion,
    }

    for field, value in update_data.items():
        setattr(exam, field, value)

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

    return build_exam_response(exam)


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
