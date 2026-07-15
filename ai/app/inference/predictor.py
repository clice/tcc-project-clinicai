"""Orquestra a inferência conforme o domínio explicitamente selecionado."""

import numpy as np

from app.config import CLASS_LABELS_BY_DOMAIN
from app.explainability.gradcam import generate_gradcam_from_bytes
from app.inference import domains  # noqa: F401
from app.inference.model_loader import DEVICE
from app.inference.preprocess import preprocess_image
from app.inference.registry import normalize_exam_type, resolve_active_predictor
from app.inference.runtime import model_version_for_domain


def predict_image(image_bytes: bytes, exam_type: str) -> dict:
    normalized_exam_type = normalize_exam_type(exam_type)
    predictor = resolve_active_predictor(normalized_exam_type)
    labels = CLASS_LABELS_BY_DOMAIN.get(predictor.domain)
    if not labels:
        raise RuntimeError(f"Domínio '{predictor.domain}' não possui classes configuradas.")

    image_tensor = preprocess_image(image_bytes)
    probabilities = np.asarray(predictor.predict_proba(image_tensor), dtype=float)
    if probabilities.ndim != 1 or len(probabilities) != len(labels):
        raise RuntimeError(
            f"Modelo '{predictor.name}' retornou {len(probabilities)} probabilidades, "
            f"mas o domínio '{predictor.domain}' possui {len(labels)} classes."
        )
    if not np.isfinite(probabilities).all():
        raise RuntimeError("O modelo retornou probabilidades não finitas.")

    predicted_class = int(np.argmax(probabilities))
    if predicted_class not in labels:
        raise RuntimeError("O índice previsto não existe no catálogo de classes do domínio.")

    confidence = float(probabilities[predicted_class])
    gradcam_path = generate_gradcam_from_bytes(
        image_bytes,
        domain=predictor.domain,
    )

    return {
        "exam_type": normalized_exam_type,
        "exam_domain": predictor.domain,
        "prediction_class": predicted_class,
        "label": labels[predicted_class],
        "confidence": round(confidence, 4),
        "model_name": predictor.name,
        "model_version": model_version_for_domain(predictor.domain),
        "device": str(DEVICE),
        "gradcam_available": gradcam_path is not None,
        "gradcam_path": gradcam_path,
    }
