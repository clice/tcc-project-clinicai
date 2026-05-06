"""
Módulo responsável pela inferência da IA.
"""

import torch

from app.config import CLASS_LABELS
from app.inference.model_loader import DEVICE, model
from app.inference.preprocess import preprocess_image


def predict_image(image_bytes: bytes) -> dict:
    """
    Executa uma predição simulada.

    Nesta etapa:
    - faz preprocessamento;
    - simula uma inferência;
    - retorna resultado estruturado.
    """

    image_tensor = preprocess_image(image_bytes)
    
    image_tensor = image_tensor.to(DEVICE)
    
    with torch.no_grad():
        outputs = model(image_tensor)
        
        probabilities = torch.softmax(outputs, dim=1)
        
        confidence, predicted_class = torch.max(probabilities, dim=1)

    predicted_class_index = predicted_class.item()

    predicted_label = CLASS_LABELS[predicted_class_index]

    return {
        "label": predicted_label,
        "confidence": round(confidence.item(), 4),
        "model_name": "mock_pytorch_classifier",
        "model_version": "0.1.0",
        "gradcam_available": False,
    }
