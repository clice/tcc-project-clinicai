"""
API de Inteligência Artificial do ClinicAI.

Este serviço recebe imagens de exames, executa o modelo de IA configurado
como ativo (Ensemble Stacking, por padrão) e retorna o resultado da
análise.
"""

from fastapi import FastAPI, File, UploadFile

from app.config import ACTIVE_MODEL_NAME
from app.schemas import PredictionResponse
from app.inference import models_config  # registra os modelos disponíveis
from ai.app.inference.timm_predictor import predict_image
from app.inference.registry import available_models


app = FastAPI(
    title="ClinicAI AI Service",
    description="Serviço de inferência de IA para análise de exames endoscópicos e colonoscópicos.",
    version="0.1.0",
)


@app.get("/")
def root():
    """
    Rota inicial da API de IA.
    """
    return {
        "message": "ClinicAI AI Service is running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    """
    Rota de verificação de saúde do serviço.
    """
    return {
        "status": "ok",
        "service": "clinicai-ai",
    }


@app.get("/models")
def list_models():
    """
    Lista os modelos preditivos registrados e qual está ativo — útil
    para conferir rapidamente se o serviço subiu com o Ensemble Stacking
    ou recuou para um modelo isolado (ver `app.config.ACTIVE_MODEL_NAME`).
    """
    return {
        "active_model": ACTIVE_MODEL_NAME,
        "available_models": available_models(),
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict_exam_image(file: UploadFile = File(...)):
    """
    Recebe uma imagem de exame e retorna a predição do modelo ativo.
    """
    image_bytes = await file.read()

    prediction = predict_image(image_bytes)

    return PredictionResponse(**prediction)