"""
Schemas da API de Inteligência Artificial do ClinicAI.

Este arquivo define os formatos de entrada e saída usados pelo serviço
de inferência da IA.
"""

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """
    Resposta retornada pela IA após analisar uma imagem de exame.
    """

    exam_domain: str = Field(
        ...,
        description="Domínio médico do modelo utilizado.",
    )

    label: str = Field(
        ...,
        description="Classe prevista pela IA. Exemplo: normal ou abnormal.",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confiança da predição, variando de 0 a 1.",
    )

    model_name: str = Field(
        ...,
        description="Nome do modelo utilizado na inferência (ex: 'ensemble_stacking').",
    )

    model_version: str = Field(
        ...,
        description="Versão do modelo utilizado.",
    )

    gradcam_available: bool = Field(
        default=False,
        description="Indica se o GradCAM foi gerado para a imagem.",
    )

    gradcam_path: str | None = Field(
        default=None,
        description="Caminho local do GradCAM gerado.",
    )

    device: str = Field(
        ...,
        description="Dispositivo usado durante a inferência (ex: 'cuda' ou 'cpu').",
    )
    