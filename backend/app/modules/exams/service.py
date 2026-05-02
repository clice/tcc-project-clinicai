"""
Service do módulo de exames.

Concentra as regras de negócio relacionadas aos exames.
"""

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.modules.clinics.model import Clinic
from app.modules.exams.model import Exam
from app.modules.exams.schema import ExamCreate, ExamUpdate
from app.modules.patients.model import Patient
from app.modules.statuses.model import Status
from app.modules.statuses.service import (
    get_status_by_id_and_context,
    get_status_by_name_and_context,
)
from app.modules.users.model import User


def build_exam_response(exam: Exam) -> dict:
    """
    Monta a resposta incluindo dados do status relacionado.
    """
    return {
        "id": exam.id,
        "clinic_id": exam.clinic_id,
        "patient_id": exam.patient_id,
        "doctor_id": exam.doctor_id,
        "status_id": exam.status_id,
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
        "status_name": exam.status.name if exam.status else None,
        "status_display_name": exam.status.display_name if exam.status else None,
        "created_at": exam.created_at,
        "updated_at": exam.updated_at,
    }


def validate_exam_relationships(
    db: Session,
    *,
    clinic_id: int,
    patient_id: int,
    doctor_id: int | None,
    status_id: int,
) -> None:
    """
    Valida se clínica, paciente, médico e status existem.
    """
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()

    if not clinic:
        raise HTTPException(status_code=404, detail="Clínica não encontrada.")

    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    if patient.clinic_id != clinic_id:
        raise HTTPException(
            status_code=400,
            detail="Paciente não pertence à clínica informada.",
        )

    if doctor_id is not None:
        doctor = db.query(User).filter(User.id == doctor_id).first()

        if not doctor:
            raise HTTPException(status_code=404, detail="Médico não encontrado.")

        if doctor.clinic_id != clinic_id:
            raise HTTPException(
                status_code=400,
                detail="Médico não pertence à clínica informada.",
            )

    get_status_by_id_and_context(
        db=db,
        status_id=status_id,
        applies_to="exam",
    )


def get_exam_model_by_id(db: Session, exam_id: int) -> Exam:
    """
    Busca o model de exame pelo ID.

    Usado internamente pelo service.
    """
    exam = (
        db.query(Exam)
        .options(joinedload(Exam.status))
        .filter(Exam.id == exam_id)
        .first()
    )

    if not exam:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    return exam


def get_exam_by_id(db: Session, exam_id: int) -> dict:
    """
    Busca um exame pelo ID.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)
    return build_exam_response(exam)


def list_exams(
    db: Session,
    search: str | None = None,
    clinic_id: int | None = None,
    patient_id: int | None = None,
    doctor_id: int | None = None,
    status_id: int | None = None,
    include_inactive: bool = True,
) -> list[dict]:
    """
    Lista exames cadastrados.
    """
    query = db.query(Exam).options(joinedload(Exam.status))

    if clinic_id:
        query = query.filter(Exam.clinic_id == clinic_id)

    if patient_id:
        query = query.filter(Exam.patient_id == patient_id)

    if doctor_id:
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
        query = query.join(Status).filter(Status.name != "inactive")

    exams = query.order_by(Exam.created_at.desc()).all()

    return [build_exam_response(exam) for exam in exams]


def create_exam(db: Session, payload: ExamCreate) -> dict:
    """
    Cria um novo exame.
    """
    validate_exam_relationships(
        db=db,
        clinic_id=payload.clinic_id,
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        status_id=payload.status_id,
    )

    exam = Exam(**payload.model_dump())

    db.add(exam)
    db.commit()
    db.refresh(exam)

    exam = get_exam_model_by_id(db=db, exam_id=exam.id)

    return build_exam_response(exam)


def update_exam(
    db: Session,
    exam_id: int,
    payload: ExamUpdate,
) -> dict:
    """
    Atualiza parcialmente um exame.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return build_exam_response(exam)

    clinic_id = update_data.get("clinic_id", exam.clinic_id)
    patient_id = update_data.get("patient_id", exam.patient_id)
    doctor_id = update_data.get("doctor_id", exam.doctor_id)
    status_id = update_data.get("status_id", exam.status_id)

    validate_exam_relationships(
        db=db,
        clinic_id=clinic_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status_id=status_id,
    )

    for field, value in update_data.items():
        setattr(exam, field, value)

    db.commit()
    db.refresh(exam)

    exam = get_exam_model_by_id(db=db, exam_id=exam.id)

    return build_exam_response(exam)


def delete_exam(db: Session, exam_id: int) -> dict:
    """
    Remove logicamente um exame usando status inactive.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    inactive_status = get_status_by_name_and_context(
        db=db,
        name="inactive",
        applies_to="exam",
    )

    exam.status_id = inactive_status.id

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
) -> dict:
    """
    Vincula dados de arquivo a um exame.

    Nesta etapa, ainda não faz upload físico.
    Apenas salva as informações do arquivo.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    exam.file_path = file_path
    exam.file_name = file_name
    exam.file_mime_type = file_mime_type

    db.commit()
    db.refresh(exam)

    exam = get_exam_model_by_id(db=db, exam_id=exam.id)

    return build_exam_response(exam)


def download_exam_file(db: Session, exam_id: int) -> dict:
    """
    Retorna os dados do arquivo vinculado ao exame.
    """
    exam = get_exam_model_by_id(db=db, exam_id=exam_id)

    if not exam.file_path:
        raise HTTPException(
            status_code=404,
            detail="Este exame não possui arquivo vinculado.",
        )

    return {
        "exam_id": exam.id,
        "file_path": exam.file_path,
        "file_name": exam.file_name,
        "file_mime_type": exam.file_mime_type,
    }
    