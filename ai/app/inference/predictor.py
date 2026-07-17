"""Orquestra a inferência conforme o domínio explicitamente selecionado."""

import numpy as np

from app.config import CLASS_LABELS_BY_DOMAIN
from app.explainability.gradcam import (
    generate_ensemble_attribution_from_bytes,
    generate_gradcam_from_bytes,
)
from app.inference import domains  # noqa: F401
from app.inference.model_loader import DEVICE
from app.inference.preprocess import preprocess_image
from app.inference.registry import (
    normalize_exam_type,
    resolve_active_predictor,
)
from app.inference.runtime import model_version_for_domain


def predict_image(
    image_bytes: bytes,
    exam_type: str,
) -> dict:
    """Executa a classificação e a explicabilidade configuradas."""

    normalized_exam_type = normalize_exam_type(
        exam_type
    )

    predictor = resolve_active_predictor(
        normalized_exam_type
    )

    labels = CLASS_LABELS_BY_DOMAIN.get(
        predictor.domain
    )

    if not labels:
        raise RuntimeError(
            f"Domínio '{predictor.domain}' "
            "não possui classes configuradas."
        )

    attribution = None

    use_ensemble_attribution = (
        predictor.name == "ensemble_stacking"
        and predictor.domain == "gastrointestinal"
        and hasattr(
            predictor,
            "predict_differentiable",
        )
    )

    if use_ensemble_attribution:
        attribution = (
            generate_ensemble_attribution_from_bytes(
                image_bytes,
                domain=predictor.domain,
            )
        )

        if attribution is None:
            raise RuntimeError(
                "O domínio gastrointestinal não "
                "produziu resultado de atribuição."
            )

        probabilities = np.asarray(
            attribution.final_probabilities,
            dtype=float,
        )

        gradcam_path = attribution.path

    else:
        image_tensor = preprocess_image(
            image_bytes
        )

        probabilities = np.asarray(
            predictor.predict_proba(
                image_tensor
            ),
            dtype=float,
        )

        gradcam_path = generate_gradcam_from_bytes(
            image_bytes,
            domain=predictor.domain,
        )

    if (
        probabilities.ndim != 1
        or len(probabilities) != len(labels)
    ):
        raise RuntimeError(
            f"Modelo '{predictor.name}' retornou "
            f"{len(probabilities)} probabilidades, "
            f"mas o domínio '{predictor.domain}' "
            f"possui {len(labels)} classes."
        )

    if not np.isfinite(
        probabilities
    ).all():
        raise RuntimeError(
            "O modelo retornou probabilidades "
            "não finitas."
        )

    predicted_class = int(
        np.argmax(probabilities)
    )

    if (
        attribution is not None
        and attribution.predicted_class
        != predicted_class
    ):
        raise RuntimeError(
            "A classe do mapa de atribuição não "
            "corresponde à classificação final."
        )

    if predicted_class not in labels:
        raise RuntimeError(
            "O índice previsto não existe no "
            "catálogo de classes do domínio."
        )

    confidence = float(
        probabilities[predicted_class]
    )

    return {
        "exam_type": normalized_exam_type,
        "exam_domain": predictor.domain,
        "prediction_class": predicted_class,
        "label": labels[predicted_class],
        "confidence": round(
            confidence,
            4,
        ),
        "model_name": predictor.name,
        "model_version": (
            model_version_for_domain(
                predictor.domain
            )
        ),
        "device": str(DEVICE),
        "gradcam_available": (
            gradcam_path is not None
        ),
        "gradcam_path": gradcam_path,
        "attribution_method": (
            attribution.method
            if attribution is not None
            else None
        ),
        "attribution_target_layers": (
            dict(attribution.target_layers)
            if attribution is not None
            else None
        ),
        "attribution_local_evidence": (
            dict(attribution.local_evidence)
            if attribution is not None
            else None
        ),
        "attribution_branch_weights": (
            dict(attribution.branch_weights)
            if (
                attribution is not None
                and attribution.branch_weights
                is not None
            )
            else None
        ),
        "attribution_branch_cam_raw_maxima": (
            dict(
                attribution
                .branch_cam_raw_maxima
            )
            if (
                attribution is not None
                and attribution
                .branch_cam_raw_maxima
                is not None
            )
            else None
        ),
        "attribution_unavailable_reason": (
            attribution.unavailable_reason
            if attribution is not None
            else None
        ),
    }
