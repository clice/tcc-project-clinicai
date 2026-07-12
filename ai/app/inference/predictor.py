"""
Módulo responsável pela inferência da IA do ClinicAI.

Este arquivo não sabe mais qual arquitetura está por trás da predição —
ele só pede ao registro (`registry.py`) o modelo configurado como ativo
(`app.config.ACTIVE_MODEL_NAME`) e usa a interface comum `BasePredictor`.
Trocar de modelo (ex: recuar do Ensemble Stacking para a ResNet-50
isolada, ou adicionar um modelo novo no futuro) é uma mudança de
configuração, não de código.
"""

import numpy as np

from app.config import ACTIVE_MODEL_NAME, CLASS_LABELS, EXAM_DOMAIN, MODEL_VERSION
from app.explainability.gradcam import generate_gradcam_from_bytes
from app.inference.model_loader import DEVICE
from app.inference.preprocess import preprocess_image
from app.inference.registry import get_predictor
from app.inference import models_config  # noqa: F401  (garante que os modelos foram registrados)


def predict_image(image_bytes: bytes, model_name: str | None = None) -> dict:
    """
    Executa inferência da IA sobre uma imagem médica.

    Args:
        image_bytes: Bytes da imagem enviada.
        model_name: Nome de um modelo específico já registrado (ex:
            "resnet50"), para uso pontual (debug, comparação manual).
            Se omitido, usa `app.config.ACTIVE_MODEL_NAME` — o
            comportamento normal do serviço.
    """
    predictor = get_predictor(model_name or ACTIVE_MODEL_NAME)

    image_tensor = preprocess_image(image_bytes)

    probabilities = predictor.predict_proba(image_tensor)

    predicted_class_index = int(np.argmax(probabilities))
    confidence = float(probabilities[predicted_class_index])
    predicted_label = CLASS_LABELS[predicted_class_index]

    gradcam_path = generate_gradcam_from_bytes(image_bytes)

    return {
        "label": predicted_label,
        "confidence": round(confidence, 4),
        "model_name": predictor.name,
        "model_version": MODEL_VERSION,
        "exam_domain": EXAM_DOMAIN,
        "device": str(DEVICE),
        "gradcam_available": True,
        "gradcam_path": gradcam_path,
    }
    