"""Cliente HTTP e validação do contrato do serviço de IA."""

from __future__ import annotations

import base64
import binascii
import hashlib
import math
import re
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
    "gastrointestinal": {
        0: "normal",
        1: "abnormal",
    },
}

EXPECTED_ATTRIBUTION_METHOD = (
    "weighted_base_gradcam_oriented_by_"
    "ensemble_stacking_v1"
)

EXPECTED_ATTRIBUTION_MODELS = frozenset(
    {
        "resnet50",
        "efficientnet_b4",
        "pvt_v2_b2",
    }
)

_ATTRIBUTION_FIELDS = {
    "attribution_method",
    "attribution_target_layers",
    "attribution_local_evidence",
    "attribution_branch_weights",
    "attribution_branch_cam_raw_maxima",
    "attribution_unavailable_reason",
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
    "gradcam_base64",
    "gradcam_mime_type",
    "gradcam_sha256",
    "device",
    *_ATTRIBUTION_FIELDS,
}


def _validate_model_keys(
    value: dict,
    *,
    field: str,
) -> None:
    keys = set(value)

    if keys != EXPECTED_ATTRIBUTION_MODELS:
        raise AIServiceResponseError(
            f"{field} deve conter exatamente os modelos "
            "resnet50, efficientnet_b4 e pvt_v2_b2."
        )


def _validate_target_layers(
    value: Any,
) -> dict[str, str]:
    field = "attribution_target_layers"

    if not isinstance(value, dict):
        raise AIServiceResponseError(
            f"{field} deve ser um objeto."
        )

    _validate_model_keys(
        value,
        field=field,
    )

    for model_name, layer_name in value.items():
        if (
            not isinstance(model_name, str)
            or not isinstance(layer_name, str)
            or not layer_name.strip()
        ):
            raise AIServiceResponseError(
                f"{field} deve associar cada modelo "
                "a uma camada não vazia."
            )

    return value


def _validate_numeric_model_mapping(
    value: Any,
    *,
    field: str,
) -> dict[str, float]:
    if not isinstance(value, dict):
        raise AIServiceResponseError(
            f"{field} deve ser um objeto."
        )

    _validate_model_keys(
        value,
        field=field,
    )

    normalized: dict[str, float] = {}

    for model_name, raw_value in value.items():
        if (
            isinstance(raw_value, bool)
            or not isinstance(
                raw_value,
                (int, float),
            )
        ):
            raise AIServiceResponseError(
                f"{field}.{model_name} deve ser numérico."
            )

        numeric_value = float(raw_value)

        if (
            not math.isfinite(numeric_value)
            or numeric_value < 0.0
        ):
            raise AIServiceResponseError(
                f"{field}.{model_name} deve ser "
                "finito e não negativo."
            )

        normalized[model_name] = numeric_value

    return normalized


def _validate_attribution_contract(
    payload: dict,
    *,
    domain: str,
    model_name: str,
    gradcam_available: bool,
) -> None:
    method = payload["attribution_method"]
    target_layers = payload[
        "attribution_target_layers"
    ]
    local_evidence = payload[
        "attribution_local_evidence"
    ]
    branch_weights = payload[
        "attribution_branch_weights"
    ]
    raw_maxima = payload[
        "attribution_branch_cam_raw_maxima"
    ]
    unavailable_reason = payload[
        "attribution_unavailable_reason"
    ]

    is_ensemble_attribution = (
        domain == "gastrointestinal"
        and model_name == "ensemble_stacking"
    )

    if not is_ensemble_attribution:
        non_null_fields = [
            field
            for field in _ATTRIBUTION_FIELDS
            if payload[field] is not None
        ]

        if non_null_fields:
            raise AIServiceResponseError(
                "Metadados de atribuição não eram esperados "
                f"para o modelo {model_name}: "
                + ", ".join(sorted(non_null_fields))
                + "."
            )

        return

    if method != EXPECTED_ATTRIBUTION_METHOD:
        raise AIServiceResponseError(
            "attribution_method não corresponde ao "
            "método configurado para o Ensemble Stacking."
        )

    _validate_target_layers(
        target_layers
    )

    _validate_numeric_model_mapping(
        local_evidence,
        field="attribution_local_evidence",
    )

    normalized_weights = None

    if branch_weights is not None:
        normalized_weights = (
            _validate_numeric_model_mapping(
                branch_weights,
                field="attribution_branch_weights",
            )
        )

        if not math.isclose(
            sum(normalized_weights.values()),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            raise AIServiceResponseError(
                "Os pesos locais da atribuição devem somar 1."
            )

    if raw_maxima is not None:
        _validate_numeric_model_mapping(
            raw_maxima,
            field=(
                "attribution_branch_cam_raw_maxima"
            ),
        )

    if unavailable_reason is not None and (
        not isinstance(unavailable_reason, str)
        or not unavailable_reason.strip()
    ):
        raise AIServiceResponseError(
            "attribution_unavailable_reason deve ser "
            "uma string não vazia ou nulo."
        )

    if gradcam_available:
        if normalized_weights is None:
            raise AIServiceResponseError(
                "Os pesos locais são obrigatórios quando "
                "o mapa composto está disponível."
            )

        if raw_maxima is None:
            raise AIServiceResponseError(
                "Os máximos brutos dos ramos são "
                "obrigatórios quando o mapa está disponível."
            )

        if unavailable_reason is not None:
            raise AIServiceResponseError(
                "O motivo de indisponibilidade deve ser nulo "
                "quando o mapa está disponível."
            )

    elif unavailable_reason is None:
        raise AIServiceResponseError(
            "O motivo da indisponibilidade deve ser informado "
            "quando o mapa composto não for gerado."
        )


def _validate_prediction_contract(
    payload: Any,
    *,
    exam_type: str,
) -> dict:
    if not isinstance(payload, dict):
        raise AIServiceResponseError(
            "Resposta da IA deve ser um objeto JSON."
        )

    missing = sorted(
        _REQUIRED_FIELDS - payload.keys()
    )

    if missing:
        raise AIServiceResponseError(
            "Resposta da IA não contém os campos "
            "obrigatórios: "
            + ", ".join(missing)
            + "."
        )

    response_exam_type = str(
        payload["exam_type"] or ""
    ).strip().lower()

    if response_exam_type != exam_type:
        raise AIServiceResponseError(
            "A IA respondeu para exam_type "
            f"'{response_exam_type}', esperado "
            f"'{exam_type}'."
        )

    domain = str(
        payload["exam_domain"] or ""
    ).strip().lower()

    expected_domain = (
        EXPECTED_DOMAIN_BY_EXAM_TYPE.get(
            exam_type
        )
    )

    if (
        expected_domain
        and domain != expected_domain
    ):
        raise AIServiceResponseError(
            f"Domínio retornado '{domain}' não "
            "corresponde ao esperado "
            f"'{expected_domain}'."
        )

    prediction_class = payload[
        "prediction_class"
    ]

    if (
        isinstance(prediction_class, bool)
        or not isinstance(
            prediction_class,
            int,
        )
    ):
        raise AIServiceResponseError(
            "prediction_class deve ser um "
            "número inteiro."
        )

    if prediction_class < 0:
        raise AIServiceResponseError(
            "prediction_class não pode ser negativo."
        )

    expected_classes = (
        EXPECTED_CLASSES_BY_DOMAIN.get(
            domain
        )
    )

    if expected_classes is not None:
        expected_label = expected_classes.get(
            prediction_class
        )

        if (
            expected_label is None
            or payload["label"]
            != expected_label
        ):
            raise AIServiceResponseError(
                "A classe e o rótulo retornados não "
                "correspondem ao catálogo do domínio."
            )

    confidence = payload["confidence"]

    if (
        isinstance(confidence, bool)
        or not isinstance(
            confidence,
            (int, float),
        )
    ):
        raise AIServiceResponseError(
            "confidence deve ser numérico."
        )

    if (
        not math.isfinite(float(confidence))
        or not 0 <= float(confidence) <= 1
    ):
        raise AIServiceResponseError(
            "confidence deve ser finito e estar "
            "entre 0 e 1."
        )

    for field in (
        "label",
        "model_name",
        "model_version",
        "device",
    ):
        if (
            not isinstance(
                payload[field],
                str,
            )
            or not payload[field].strip()
        ):
            raise AIServiceResponseError(
                f"{field} deve ser uma string "
                "não vazia."
            )

    model_name = payload[
        "model_name"
    ].strip()

    gradcam_available = payload[
        "gradcam_available"
    ]

    if not isinstance(
        gradcam_available,
        bool,
    ):
        raise AIServiceResponseError(
            "gradcam_available deve ser booleano."
        )

    gradcam_base64 = payload[
        "gradcam_base64"
    ]
    gradcam_mime_type = payload[
        "gradcam_mime_type"
    ]
    gradcam_sha256 = payload[
        "gradcam_sha256"
    ]

    if gradcam_available:
        if (
            not isinstance(
                gradcam_base64,
                str,
            )
            or not gradcam_base64
        ):
            raise AIServiceResponseError(
                "gradcam_base64 deve ser informado "
                "quando o mapa estiver disponível."
            )

        if gradcam_mime_type not in {
            "image/jpeg",
            "image/png",
        }:
            raise AIServiceResponseError(
                "gradcam_mime_type deve informar "
                "image/jpeg ou image/png."
            )

        if (
            not isinstance(
                gradcam_sha256,
                str,
            )
            or re.fullmatch(
                r"[0-9a-f]{64}",
                gradcam_sha256,
            )
            is None
        ):
            raise AIServiceResponseError(
                "gradcam_sha256 deve ser um hash "
                "SHA-256 hexadecimal válido."
            )

        try:
            decoded_gradcam = (
                base64.b64decode(
                    gradcam_base64,
                    validate=True,
                )
            )
        except (
            binascii.Error,
            ValueError,
        ) as exc:
            raise AIServiceResponseError(
                "gradcam_base64 não contém "
                "Base64 válido."
            ) from exc

        if not decoded_gradcam:
            raise AIServiceResponseError(
                "O mapa de atribuição retornado "
                "está vazio."
            )

        if (
            hashlib.sha256(
                decoded_gradcam
            ).hexdigest()
            != gradcam_sha256
        ):
            raise AIServiceResponseError(
                "O hash do mapa de atribuição "
                "não corresponde ao conteúdo."
            )
    elif any(
        value not in (None, "")
        for value in (
            gradcam_base64,
            gradcam_mime_type,
            gradcam_sha256,
        )
    ):
        raise AIServiceResponseError(
            "Os campos do mapa devem ser nulos "
            "quando ele não estiver disponível."
        )

    _validate_attribution_contract(
        payload,
        domain=domain,
        model_name=model_name,
        gradcam_available=gradcam_available,
    )

    if (
        domain == "gastrointestinal"
        and model_name != "ensemble_stacking"
        and not gradcam_available
    ):
        raise AIServiceResponseError(
            "O domínio gastrointestinal deve retornar "
            "o mapa visual configurado."
        )

    return payload


async def request_prediction(
    image_bytes: bytes,
    filename: str,
    content_type: str,
    exam_type: str,
) -> dict:
    """Envia imagem e diferencia falhas de comunicação."""

    normalized_exam_type = (
        exam_type or ""
    ).strip().lower()

    if not normalized_exam_type:
        raise AIServiceResponseError(
            "exam_type é obrigatório para "
            "consultar a IA."
        )

    url = (
        f"{settings.ai_service_url}/predict"
    )

    try:
        async with httpx.AsyncClient(
            timeout=(
                settings
                .ai_service_timeout_seconds
            ),
        ) as client:
            response = await client.post(
                url,
                data={
                    "exam_type":
                    normalized_exam_type
                },
                files={
                    "file": (
                        filename,
                        image_bytes,
                        content_type,
                    )
                },
            )

    except httpx.TimeoutException as exc:
        raise AIServiceTimeoutError(
            "O serviço de IA excedeu o "
            "tempo máximo de resposta."
        ) from exc

    except httpx.RequestError as exc:
        raise AIServiceUnavailableError(
            "O serviço de IA está indisponível "
            "ou recusou a conexão."
        ) from exc

    if response.status_code != 200:
        detail = response.text[:500]

        raise AIServiceResponseError(
            "Serviço de IA retornou status "
            f"{response.status_code}: {detail}"
        )

    try:
        payload = response.json()

    except ValueError as exc:
        raise AIServiceResponseError(
            "Resposta do serviço de IA não é "
            "JSON válido."
        ) from exc

    return _validate_prediction_contract(
        payload,
        exam_type=normalized_exam_type,
    )
