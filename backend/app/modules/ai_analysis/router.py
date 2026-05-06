"""
Rotas do módulo de análises de IA.

Expõe os endpoints relacionados aos resultados gerados por IA.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.modules.ai_analysis.schema import (
    AIAnalysisCreate,
    AIAnalysisResponse,
    AIAnalysisUpdate,
)
from app.modules.ai_analysis.service import (
    create_ai_analysis,
    get_ai_analysis_by_exam_id,
    get_ai_analysis_by_id,
    list_ai_analysis,
    update_ai_analysis,
)
from app.modules.users.model import User


router = APIRouter(prefix="/ai-analysis", tags=["AI Analysis"])


@router.post("/", response_model=AIAnalysisResponse, status_code=201)
def create_ai_analysis_route(
    payload: AIAnalysisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ai_analysis:create")),
):
    """
    Cria uma análise de IA para um exame.
    """
    return create_ai_analysis(
        db=db,
        payload=payload,
        current_user=current_user,
    )


@router.get("/", response_model=list[AIAnalysisResponse])
def list_ai_analysis_route(
    exam_id: int | None = Query(default=None),
    status_id: int | None = Query(default=None),
    model_name: str | None = Query(default=None),
    model_version: str | None = Query(default=None),
    prediction_label: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ai_analysis:read")),
):
    """
    Lista análises de IA.
    """
    return list_ai_analysis(
        db=db,
        current_user=current_user,
        exam_id=exam_id,
        status_id=status_id,
        model_name=model_name,
        model_version=model_version,
        prediction_label=prediction_label,
    )


@router.get("/exam/{exam_id}", response_model=AIAnalysisResponse)
def get_ai_analysis_by_exam_route(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ai_analysis:read")),
):
    """
    Busca a análise de IA vinculada a um exame.
    """
    return get_ai_analysis_by_exam_id(
        db=db,
        exam_id=exam_id,
        current_user=current_user,
    )


@router.get("/{ai_analysis_id}", response_model=AIAnalysisResponse)
def get_ai_analysis_route(
    ai_analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ai_analysis:read")),
):
    """
    Busca uma análise de IA específica pelo ID.
    """
    return get_ai_analysis_by_id(
        db=db,
        ai_analysis_id=ai_analysis_id,
        current_user=current_user,
    )


@router.patch("/{ai_analysis_id}", response_model=AIAnalysisResponse)
def update_ai_analysis_route(
    ai_analysis_id: int,
    payload: AIAnalysisUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ai_analysis:update")),
):
    """
    Atualiza parcialmente uma análise de IA.
    """
    return update_ai_analysis(
        db=db,
        ai_analysis_id=ai_analysis_id,
        payload=payload,
        current_user=current_user,
    )
