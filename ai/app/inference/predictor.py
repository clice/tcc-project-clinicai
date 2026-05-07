"""
Módulo responsável pela inferência da IA do ClinicAI.
"""

import torch

from app.config import CLASS_LABELS
from app.inference.gradcam import generate_gradcam_from_bytes
from app.inference.model_loader import DEVICE, model
from app.inference.preprocess import preprocess_image


def predict_image(image_bytes: bytes) -> dict:
    """
    Executa a predição da imagem enviada para a API.
    """

    image_tensor = preprocess_image(image_bytes)

    image_tensor = image_tensor.to(DEVICE)

    with torch.no_grad():
        outputs = model(image_tensor)

        probabilities = torch.softmax(outputs, dim=1)

        confidence, predicted_class = torch.max(probabilities, dim=1)

    predicted_class_index = predicted_class.item()

    predicted_label = CLASS_LABELS[predicted_class_index]

    gradcam_path = generate_gradcam_from_bytes(image_bytes)

    return {
        "label": predicted_label,
        "confidence": round(confidence.item(), 4),
        "model_name": "resnet50_binary_classifier",
        "model_version": "0.1.0",
        "gradcam_available": True,
        "gradcam_path": gradcam_path,
    }
    