"""
Cliente HTTP para o serviço de IA do ClinicAI.

O serviço de IA roda em um container separado (ver docker-compose.yml,
serviço `ai`), expondo `POST /predict`. Este módulo isola toda a
comunicação com ele — se amanhã o serviço de IA mudar de protocolo
(REST para fila assíncrona, por exemplo), só este arquivo muda.
"""

import httpx

from app.core.config import settings


class AIServiceError(Exception):
    """
    Levantada quando o serviço de IA não responde, responde com erro, ou
    devolve um formato inesperado. Quem chama decide o que fazer (em
    geral, marcar o exame como falha — ver `exams.service.analyze_exam`).
    """


async def request_prediction(
    image_bytes: bytes,
    filename: str,
    content_type: str,
) -> dict:
    """
    Envia uma imagem ao serviço de IA e retorna a predição.

    Returns:
        O JSON de resposta do serviço de IA (ver `PredictionResponse` em
        `ai/app/schemas.py`): label, confidence, model_name,
        model_version, gradcam_path, etc.

    Raises:
        AIServiceError: se a requisição falhar por qualquer motivo
            (timeout, conexão recusada, status HTTP de erro, corpo
            inesperado).
    """
    url = f"{settings.ai_service_url}/predict"

    try:
        async with httpx.AsyncClient(timeout=settings.ai_service_timeout_seconds) as client:
            response = await client.post(
                url,
                files={"file": (filename, image_bytes, content_type)},
            )
    except httpx.RequestError as exc:
        raise AIServiceError(f"Falha de conexão com o serviço de IA ({url}): {exc}") from exc

    if response.status_code != 200:
        raise AIServiceError(
            f"Serviço de IA retornou status {response.status_code}: {response.text[:500]}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise AIServiceError(f"Resposta do serviço de IA não é um JSON válido: {exc}") from exc
    