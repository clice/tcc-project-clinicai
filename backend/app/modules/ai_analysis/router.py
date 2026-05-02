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
    review_ai_analysis,
    update_ai_analysis,
)


router = APIRouter(prefix="/ai-analysis", tags=["AI Analysis"])


@router.post(
    "/",
    response_model=AIAnalysisResponse,
    status_code=201,
    dependencies=[Depends(require_permission("ai_analysis:create"))],
)
def create_ai_analysis_route(
    payload: AIAnalysisCreate,
    db: Session = Depends(get_db),
):
    """
    Cria uma análise de IA para um exame.
    """
    return create_ai_analysis(db=db, payload=payload)


@router.get(
    "/",
    response_model=list[AIAnalysisResponse],
    dependencies=[Depends(require_permission("ai_analysis:read"))],
)
def list_ai_analysis_route(
    exam_id: int | None = Query(default=None),
    model_name: str | None = Query(default=None),
    model_version: str | None = Query(default=None),
    prediction_label: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Lista análises de IA.
    """
    return list_ai_analysis(
        db=db,
        exam_id=exam_id,
        model_name=model_name,
        model_version=model_version,
        prediction_label=prediction_label,
    )


@router.get(
    "/exam/{exam_id}",
    response_model=AIAnalysisResponse,
    dependencies=[Depends(require_permission("ai_analysis:read"))],
)
def get_ai_analysis_by_exam_route(
    exam_id: int,
    db: Session = Depends(get_db),
):
    """
    Busca a análise de IA vinculada a um exame.
    """
    return get_ai_analysis_by_exam_id(db=db, exam_id=exam_id)


@router.get(
    "/{ai_analysis_id}",
    response_model=AIAnalysisResponse,
    dependencies=[Depends(require_permission("ai_analysis:read"))],
)
def get_ai_analysis_route(
    ai_analysis_id: int,
    db: Session = Depends(get_db),
):
    """
    Busca uma análise de IA específica pelo ID.
    """
    return get_ai_analysis_by_id(
        db=db,
        ai_analysis_id=ai_analysis_id,
    )


@router.patch(
    "/{ai_analysis_id}",
    response_model=AIAnalysisResponse,
    dependencies=[Depends(require_permission("ai_analysis:update"))],
)
def update_ai_analysis_route(
    ai_analysis_id: int,
    payload: AIAnalysisUpdate,
    db: Session = Depends(get_db),
):
    """
    Atualiza parcialmente uma análise de IA.
    """
    return update_ai_analysis(
        db=db,
        ai_analysis_id=ai_analysis_id,
        payload=payload,
    )


@router.patch(
    "/{ai_analysis_id}/review",
    response_model=AIAnalysisResponse,
    dependencies=[Depends(require_permission("ai_analysis:review"))],
)
def review_ai_analysis_route(
    ai_analysis_id: int,
    payload: AIAnalysisUpdate,
    db: Session = Depends(get_db),
):
    """
    Registra revisão médica de uma análise por IA.
    """
    return review_ai_analysis(
        db=db,
        ai_analysis_id=ai_analysis_id,
        payload=payload,
    )