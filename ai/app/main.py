"""
API de Inteligência Artificial do ClinicAI.

Este serviço recebe imagens de exames, resolve automaticamente qual
modelo usar (conforme o tipo de exame informado) e retorna o resultado
da análise. Ver `app/inference/domains/README.md` para como adicionar
um domínio clínico novo (ex: tomografia de cabeça, mamografia).
"""

from fastapi import FastAPI, File, Form, UploadFile

from app.schemas import PredictionResponse
from app.inference import domains  # noqa: F401  (registra os modelos disponíveis)
from app.inference.predictor import predict_image
from app.inference.registry import available_domains, available_models

app = FastAPI(
    title="ClinicAI AI Service",
    description="Serviço de inferência de IA para análise de exames médicos.",
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
    Lista os domínios clínicos e modelos preditivos registrados — útil
    para conferir rapidamente quais modelos o serviço tem disponíveis e
    de qual domínio, sem precisar consultar o código.
    """
    from app.config import ACTIVE_MODEL_BY_DOMAIN, EXAM_TYPE_TO_DOMAIN

    return {
        "domains": {
            domain: {
                "active_model": ACTIVE_MODEL_BY_DOMAIN.get(domain),
                "available_models": available_models(domain),
            }
            for domain in available_domains()
        },
        "exam_type_to_domain": EXAM_TYPE_TO_DOMAIN,
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict_exam_image(
    file: UploadFile = File(...),
    exam_type: str | None = Form(default=None),
):
    """
    Recebe uma imagem de exame e retorna a predição do modelo
    correspondente ao tipo de exame informado.

    `exam_type` é opcional — se omitido, usa `app.config.DEFAULT_DOMAIN`.
    Isso mantém a rota funcionando mesmo para chamadas antigas/manuais
    que não enviam o campo, mas o backend principal sempre deve enviá-lo.
    """
    image_bytes = await file.read()

    prediction = predict_image(image_bytes, exam_type=exam_type)

    return PredictionResponse(**prediction)
