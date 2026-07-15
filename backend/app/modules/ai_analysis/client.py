"""Cliente HTTP e validação do contrato do serviço de IA."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class AIServiceError(Exception):
    """Erro base de comunicação ou contrato com o serviço de IA."""


class AIServiceTimeoutError(AIServiceError):
    """O serviço de IA não respondeu dentro do tempo configurado."""


class AIServiceUnavailableError(AIServiceError):
    """Não foi possível estabelecer comunicação com o serviço de IA."""


class AIServiceResponseError(AIServiceError):
    """O serviço respondeu com erro ou violou o contrato esperado."""


EXPECTED_DOMAIN_BY_EXAM_TYPE = {
    "endoscopy": "gastrointestinal",
    "colonoscopy": "gastrointestinal",
}
EXPECTED_CLASSES_BY_DOMAIN = {
    "gastrointestinal": {0: "normal", 1: "abnormal"},
}

_REQUIRED_FIELDS = {
    "exam_type",
    "exam_domain",
    "prediction_class",
    "label",
    "confidence",
    "model_name",
    "model_version",
    "gradcam_available",
    "gradcam_path",
    "device",
}


def _validate_prediction_contract(payload: Any, *, exam_type: str) -> dict:
    if not isinstance(payload, dict):
        raise AIServiceResponseError("Resposta da IA deve ser um objeto JSON.")

    missing = sorted(_REQUIRED_FIELDS - payload.keys())
    if missing:
        raise AIServiceResponseError(
            f"Resposta da IA não contém os campos obrigatórios: {', '.join(missing)}."
        )

    response_exam_type = str(payload["exam_type"] or "").strip().lower()
    if response_exam_type != exam_type:
        raise AIServiceResponseError(
            f"A IA respondeu para exam_type '{response_exam_type}', esperado '{exam_type}'."
        )

    domain = str(payload["exam_domain"] or "").strip().lower()
    expected_domain = EXPECTED_DOMAIN_BY_EXAM_TYPE.get(exam_type)
    if expected_domain and domain != expected_domain:
        raise AIServiceResponseError(
            f"Domínio retornado '{domain}' não corresponde ao esperado '{expected_domain}'."
        )

    prediction_class = payload["prediction_class"]
    if isinstance(prediction_class, bool) or not isinstance(prediction_class, int):
        raise AIServiceResponseError("prediction_class deve ser um número inteiro.")
    if prediction_class < 0:
        raise AIServiceResponseError("prediction_class não pode ser negativo.")

    expected_classes = EXPECTED_CLASSES_BY_DOMAIN.get(domain)
    if expected_classes is not None:
        expected_label = expected_classes.get(prediction_class)
        if expected_label is None or payload["label"] != expected_label:
            raise AIServiceResponseError(
                "A classe e o rótulo retornados não correspondem ao catálogo do domínio."
            )

    confidence = payload["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise AIServiceResponseError("confidence deve ser numérico.")
    if not 0 <= float(confidence) <= 1:
        raise AIServiceResponseError("confidence deve estar entre 0 e 1.")

    for field in ("label", "model_name", "model_version", "device"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise AIServiceResponseError(f"{field} deve ser uma string não vazia.")

    gradcam_available = payload["gradcam_available"]
    if not isinstance(gradcam_available, bool):
        raise AIServiceResponseError("gradcam_available deve ser booleano.")
    gradcam_path = payload["gradcam_path"]
    if gradcam_available and (not isinstance(gradcam_path, str) or not gradcam_path.strip()):
        raise AIServiceResponseError(
            "gradcam_path deve ser informado quando gradcam_available for verdadeiro."
        )
    if not gradcam_available and gradcam_path not in (None, ""):
        raise AIServiceResponseError(
            "gradcam_path deve ser nulo quando gradcam_available for falso."
        )
    if domain == "gastrointestinal" and not gradcam_available:
        raise AIServiceResponseError(
            "O domínio gastrointestinal deve retornar o Grad-CAM da ResNet-50."
        )

    return payload


async def request_prediction(
    image_bytes: bytes,
    filename: str,
    content_type: str,
    exam_type: str,
) -> dict:
    """Envia imagem e exam_type, diferenciando timeout e indisponibilidade."""
    normalized_exam_type = (exam_type or "").strip().lower()
    if not normalized_exam_type:
        raise AIServiceResponseError("exam_type é obrigatório para consultar a IA.")

    url = f"{settings.ai_service_url}/predict"
    try:
        async with httpx.AsyncClient(
            timeout=settings.ai_service_timeout_seconds,
        ) as client:
            response = await client.post(
                url,
                data={"exam_type": normalized_exam_type},
                files={"file": (filename, image_bytes, content_type)},
            )
    except httpx.TimeoutException as exc:
        raise AIServiceTimeoutError(
            "O serviço de IA excedeu o tempo máximo de resposta."
        ) from exc
    except httpx.RequestError as exc:
        raise AIServiceUnavailableError(
            "O serviço de IA está indisponível ou recusou a conexão."
        ) from exc

    if response.status_code != 200:
        detail = response.text[:500]
        raise AIServiceResponseError(
            f"Serviço de IA retornou status {response.status_code}: {detail}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise AIServiceResponseError("Resposta do serviço de IA não é JSON válido.") from exc

    return _validate_prediction_contract(payload, exam_type=normalized_exam_type)
