"""
Módulo responsável pela inferência da IA do ClinicAI.
"""

import torch

from app.config import CLASS_LABELS

from app.inference.gradcam import (
    generate_gradcam_from_bytes,
)

from app.inference.model_loader import (
    DEVICE,
    MODEL_PATH,
    model,
)

from app.inference.preprocess import (
    preprocess_image,
)

# =========================================================
# CONFIGURAÇÕES
# =========================================================

MODEL_NAME = "resnet50"

MODEL_VERSION = "0.1.0"

EXAM_DOMAIN = "gastrointestinal"


# =========================================================
# INFERÊNCIA
# =========================================================


def predict_image(
    image_bytes: bytes,
) -> dict:
    """
    Executa inferência da IA sobre uma imagem médica.
    """

    # =====================================================
    # PREPROCESSAMENTO
    # =====================================================

    image_tensor = preprocess_image(
        image_bytes
    )

    image_tensor = image_tensor.to(
        DEVICE
    )

    # =====================================================
    # PREDIÇÃO
    # =====================================================

    with torch.no_grad():

        outputs = model(image_tensor)

        probabilities = torch.softmax(
            outputs,
            dim=1,
        )

        confidence, predicted_class = torch.max(
            probabilities,
            dim=1,
        )

    predicted_class_index = (
        predicted_class.item()
    )

    predicted_label = CLASS_LABELS[
        predicted_class_index
    ]

    # =====================================================
    # GRADCAM
    # =====================================================

    gradcam_path = (
        generate_gradcam_from_bytes(
            image_bytes
        )
    )

    # =====================================================
    # RESPONSE
    # =====================================================

    return {
        "label": predicted_label,
        "confidence": round(
            confidence.item(),
            4,
        ),
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "exam_domain": EXAM_DOMAIN,
        "device": str(DEVICE),
        "model_path": str(MODEL_PATH),
        "gradcam_available": True,
        "gradcam_path": gradcam_path,
    }
    