"""API multi-domínio de Inteligência Artificial do ClinicAI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.config import MAX_INFERENCE_IMAGE_BYTES
from app.inference import domains  # noqa: F401
from app.inference.predictor import predict_image
from app.inference.preprocess import InvalidImageError
from app.inference.registry import (
    ModelConfigurationError,
    UnsupportedExamTypeError,
    resolve_exam_domain,
)
from app.inference.runtime import (
    initialize_runtime,
    is_runtime_ready,
    model_catalog,
    runtime_snapshot,
)
from app.schemas import PredictionResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_runtime(force=True)
    yield


app = FastAPI(
    title="ClinicAI AI Service",
    description="Serviço de inferência multi-domínio para imagens médicas.",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "message": "ClinicAI AI Service is running",
        "version": "0.2.0",
        "ready": is_runtime_ready(),
    }


@app.get("/health")
def health_check():
    snapshot = runtime_snapshot()
    return JSONResponse(
        content=snapshot,
        status_code=status.HTTP_200_OK if snapshot["ready"] else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@app.get("/models")
def list_models():
    return model_catalog()


@app.post("/predict", response_model=PredictionResponse)
async def predict_exam_image(
    file: UploadFile = File(...),
    exam_type: str = Form(...),
):
    if not is_runtime_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O serviço de IA ainda não carregou todos os artefatos.",
        )

    try:
        resolve_exam_domain(exam_type)
    except UnsupportedExamTypeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    image_bytes = await file.read(MAX_INFERENCE_IMAGE_BYTES + 1)
    if len(image_bytes) > MAX_INFERENCE_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Imagem acima do limite permitido.")

    try:
        prediction = predict_image(image_bytes, exam_type=exam_type)
    except InvalidImageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except UnsupportedExamTypeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (FileNotFoundError, ModelConfigurationError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O modelo solicitado não está disponível para inferência.",
        ) from exc

    return PredictionResponse(**prediction)
