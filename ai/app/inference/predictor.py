"""
Módulo responsável pela inferência da IA.
"""

import random

from app.inference.preprocess import preprocess_image


def predict_image(image_bytes: bytes) -> dict:
    """
    Executa uma predição simulada.

    Nesta etapa:
    - faz preprocessamento;
    - simula uma inferência;
    - retorna resultado estruturado.
    """

    processed_image = preprocess_image(image_bytes)

    # Apenas para validar fluxo
    _ = processed_image.shape

    labels = ["normal", "abnormal"]

    predicted_label = random.choice(labels)

    confidence = round(random.uniform(0.75, 0.99), 2)

    return {
        "label": predicted_label,
        "confidence": confidence,
        "model_name": "mock_cnn",
        "model_version": "0.1.0",
        "gradcam_available": False,
    }
