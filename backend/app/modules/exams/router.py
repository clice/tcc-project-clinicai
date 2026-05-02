"""
Rotas do módulo de exames.

Expõe os endpoints relacionados ao cadastro e gerenciamento dos exames.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.modules.exams.schema import (
    ExamCreate,
    ExamResponse,
    ExamUpdate,
)
from app.modules.exams.service import (
    create_exam,
    delete_exam,
    download_exam_file,
    get_exam_by_id,
    list_exams,
    update_exam,
    upload_exam_file,
)


router = APIRouter(prefix="/exams", tags=["Exams"])


@router.post(
    "/",
    response_model=ExamResponse,
    status_code=201,
    dependencies=[Depends(require_permission("exams:create"))],
)
def create_exam_route(
    payload: ExamCreate,
    db: Session = Depends(get_db),
):
    """
    Cria um novo exame.
    """
    return create_exam(db=db, payload=payload)


@router.get(
    "/",
    response_model=list[ExamResponse],
    dependencies=[Depends(require_permission("exams:read"))],
)
def list_exams_route(
    search: str | None = Query(default=None),
    clinic_id: int | None = Query(default=None),
    patient_id: int | None = Query(default=None),
    doctor_id: int | None = Query(default=None),
    status_id: int | None = Query(default=None),
    include_inactive: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    """
    Lista exames cadastrados.
    """
    return list_exams(
        db=db,
        search=search,
        clinic_id=clinic_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status_id=status_id,
        include_inactive=include_inactive,
    )


@router.get(
    "/{exam_id}",
    response_model=ExamResponse,
    dependencies=[Depends(require_permission("exams:read"))],
)
def get_exam_route(
    exam_id: int,
    db: Session = Depends(get_db),
):
    """
    Busca um exame específico pelo ID.
    """
    return get_exam_by_id(db=db, exam_id=exam_id)


@router.patch(
    "/{exam_id}",
    response_model=ExamResponse,
    dependencies=[Depends(require_permission("exams:update"))],
)
def update_exam_route(
    exam_id: int,
    payload: ExamUpdate,
    db: Session = Depends(get_db),
):
    """
    Atualiza parcialmente um exame.
    """
    return update_exam(
        db=db,
        exam_id=exam_id,
        payload=payload,
    )


@router.patch(
    "/{exam_id}/delete",
    response_model=ExamResponse,
    dependencies=[Depends(require_permission("exams:delete"))],
)
def delete_exam_route(
    exam_id: int,
    db: Session = Depends(get_db),
):
    """
    Remove logicamente um exame.
    """
    return delete_exam(db=db, exam_id=exam_id)


@router.post(
    "/{exam_id}/upload-file",
    response_model=ExamResponse,
    dependencies=[Depends(require_permission("exams:upload_file"))],
)
def upload_exam_file_route(
    exam_id: int,
    file_path: str,
    file_name: str,
    file_mime_type: str,
    db: Session = Depends(get_db),
):
    """
    Vincula informações de arquivo ao exame.

    Upload físico do arquivo pode ser implementado depois com UploadFile.
    """
    return upload_exam_file(
        db=db,
        exam_id=exam_id,
        file_path=file_path,
        file_name=file_name,
        file_mime_type=file_mime_type,
    )


@router.get(
    "/{exam_id}/download-file",
    dependencies=[Depends(require_permission("exams:download_file"))],
)
def download_exam_file_route(
    exam_id: int,
    db: Session = Depends(get_db),
):
    """
    Retorna informações do arquivo vinculado ao exame.
    """
    return download_exam_file(db=db, exam_id=exam_id)