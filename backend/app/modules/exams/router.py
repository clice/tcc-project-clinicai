"""
Rotas do módulo de exames.
"""

from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.modules.exams.schema import ExamCreate, ExamResponse, ExamUpdate
from app.modules.exams.service import (
    cancel_exam,
    create_exam,
    download_exam_file,
    get_exam_by_id,
    list_exam_form_options,
    list_exams,
    replace_exam_file,
    restore_exam,
    update_exam,
)
from app.modules.users.model import User


router = APIRouter(prefix="/exams", tags=["Exams"])


@router.get("/form-options")
def get_exam_form_options_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("exams:read")),
):
    """
    Retorna dados auxiliares para o formulário de exames.
    Essa rota evita que o frontend dependa de várias rotas administrativas.
    """
    return list_exam_form_options(db=db, current_user=current_user)


@router.post("/", response_model=ExamResponse, status_code=201)
def create_exam_route(
    clinic_id: int = Form(...),
    patient_id: int = Form(...),
    doctor_id: int | None = Form(default=None),
    exam_type: str = Form(...),
    exam_date: date | None = Form(default=None),
    title: str = Form(...),
    description: str | None = Form(default=None),
    clinical_indication: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("exams:create")),
):
    """
    Cria um novo exame.
    """
    payload = ExamCreate(
        clinic_id=clinic_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        exam_type=exam_type,
        exam_date=exam_date,
        title=title,
        description=description,
        clinical_indication=clinical_indication,
    )

    return create_exam(
        db=db,
        payload=payload,
        file=file,
        current_user=current_user,
    )


@router.get("/", response_model=list[ExamResponse])
def list_exams_route(
    search: str | None = Query(default=None),
    clinic_id: int | None = Query(default=None),
    patient_id: int | None = Query(default=None),
    doctor_id: int | None = Query(default=None),
    status_id: int | None = Query(default=None),
    include_inactive: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("exams:read")),
):
    """
    Lista exames cadastrados.
    """
    return list_exams(
        db=db,
        current_user=current_user,
        search=search,
        clinic_id=clinic_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status_id=status_id,
        include_inactive=include_inactive,
    )


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam_route(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("exams:read")),
):
    """
    Busca um exame específico pelo ID.
    """
    return get_exam_by_id(
        db=db,
        exam_id=exam_id,
        current_user=current_user,
    )


@router.patch("/{exam_id}", response_model=ExamResponse)
def update_exam_route(
    exam_id: int,
    payload: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("exams:update")),
):
    """
    Atualiza parcialmente um exame.
    """
    return update_exam(
        db=db,
        exam_id=exam_id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/{exam_id}/cancel", response_model=ExamResponse)
def cancel_exam_route(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("exams:change_status")),
):
    """
    Cancela logicamente um exame.
    """
    return cancel_exam(
        db=db,
        exam_id=exam_id,
        current_user=current_user,
    )
    
    
@router.patch("/{exam_id}/restore", response_model=ExamResponse)
def restore_exam_route(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("exams:change_status")),
):
    """
    Retoma um exame cancelado.

    Se o exame possuir arquivo, retorna para processing.
    Se não possuir arquivo, retorna para pending.
    """
    return restore_exam(
        db=db,
        exam_id=exam_id,
        current_user=current_user,
    )


@router.get("/{exam_id}/download")
def download_exam_file_route(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("exams:download")),
):
    """
    Retorna informações do arquivo vinculado ao exame.
    """
    return download_exam_file(
        db=db,
        exam_id=exam_id,
        current_user=current_user,
    )

@router.post("/{exam_id}/replace-file", response_model=ExamResponse)
def replace_exam_file_route(
    exam_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("exams:upload")),
):
    """
    Substitui arquivo do exame.
    """
    return replace_exam_file(
        db=db,
        exam_id=exam_id,
        file=file,
        current_user=current_user,
    )
    
    