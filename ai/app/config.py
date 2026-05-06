"""
Configurações centrais do serviço de IA.
"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = BASE_DIR / "models"

MODEL_NAME = "model.pt"

MODEL_PATH = MODEL_DIR / MODEL_NAME

TARGET_IMAGE_SIZE = (224, 224)

CLASS_LABELS = {
    0: "normal",
    1: "abnormal",
}
