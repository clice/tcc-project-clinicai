"""
Configurações centrais do serviço de IA.
"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

AI_ROOT_DIR = BASE_DIR.parent

MODEL_DIR = AI_ROOT_DIR / "models" / "exported"

MODEL_NAME = "model.pt"

MODEL_PATH = MODEL_DIR / MODEL_NAME

STORAGE_DIR = AI_ROOT_DIR / "storage"

GRADCAM_DIR = STORAGE_DIR / "gradcam"

PREDICTIONS_DIR = STORAGE_DIR / "predictions"

TEMP_DIR = STORAGE_DIR / "temp"

TARGET_IMAGE_SIZE = (224, 224)

CLASS_LABELS = {
    0: "normal",
    1: "abnormal",
}
