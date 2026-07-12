"""
Módulo responsável pela inferência da IA do ClinicAI.

Este arquivo não sabe qual arquitetura nem qual domínio clínico está por
trás da predição — ele só pede ao registro (`registry.py`) o modelo
correto para o tipo de exame recebido, e usa a interface comum
`BasePredictor`. Adicionar um domínio novo (outro tipo de exame, outro
conjunto de modelos) não muda nada aqui — ver
`app/inference/domains/README.md`.
"""

import numpy as np

from app.config import CLASS_LABELS, MODEL_VERSION
from app.explainability.gradcam import generate_gradcam_from_bytes
from app.inference.model_loader import DEVICE
from app.inference.preprocess import preprocess_image
from app.inference.registry import resolve_active_predictor
from app.inference import domains  # noqa: F401  (garante que os modelos foram registrados)


def predict_image(image_bytes: bytes, exam_type: str | None = None) -> dict:
    """
    Executa inferência da IA sobre uma imagem médica.

    Args:
        image_bytes: Bytes da imagem enviada.
        exam_type: Tipo de exame informado pelo backend (ex: "endoscopy",
            "colonoscopy") — usado para resolver automaticamente o
            domínio clínico e o modelo ativo daquele domínio (ver
            `app.config.EXAM_TYPE_TO_DOMAIN` e `ACTIVE_MODEL_BY_DOMAIN`).
            Se omitido, usa `app.config.DEFAULT_DOMAIN`.
    """
    predictor = resolve_active_predictor(exam_type)

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
        "exam_domain": predictor.domain,
        "device": str(DEVICE),
        "gradcam_available": True,
        "gradcam_path": gradcam_path,
    }
    