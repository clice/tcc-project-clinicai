"""
Configurações centrais do serviço de IA.

Fonte única de verdade para todos os caminhos usados pelo módulo —
antes, `MODEL_PATH` era calculado de forma independente aqui e em
`model_loader.py` (duplicação sem necessidade); agora só existe aqui.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AI_ROOT_DIR = BASE_DIR.parent

# =========================================================
# PESOS DOS MODELOS
# =========================================================

MODEL_DIR = AI_ROOT_DIR / "models" / "exported"

RESNET50_WEIGHTS_PATH = MODEL_DIR / "resnet50.pt"
EFFICIENTNET_B4_WEIGHTS_PATH = MODEL_DIR / "efficientnet_b4.pt"
PVT_V2_B2_WEIGHTS_PATH = MODEL_DIR / "pvt_v2_b2.pt"
META_CLASSIFIER_PATH = MODEL_DIR / "meta_classificador.joblib"

# Nome do timm exato de cada arquitetura — usado por TimmCNNPredictor.
TIMM_MODEL_NAMES = {
    "resnet50": "resnet50",
    "efficientnet_b4": "efficientnet_b4",
    "pvt_v2_b2": "pvt_v2_b2",
}

# =========================================================
# ARMAZENAMENTO (Grad-CAM, predições, temporários)
# =========================================================

STORAGE_DIR = AI_ROOT_DIR / "storage"
GRADCAM_DIR = STORAGE_DIR / "gradcam"
PREDICTIONS_DIR = STORAGE_DIR / "predictions"
TEMP_DIR = STORAGE_DIR / "temp"

# =========================================================
# PRÉ-PROCESSAMENTO / CLASSES
# =========================================================

TARGET_IMAGE_SIZE = (224, 224)

NORMALIZE_MEAN = [0.485, 0.456, 0.406]
NORMALIZE_STD = [0.229, 0.224, 0.225]

CLASS_LABELS = {
    0: "normal",
    1: "abnormal",
}

# =========================================================
# MODELO ATIVO
# =========================================================

# Nome do modelo (já registrado em app.inference.models_config) usado de
# fato pelo endpoint /predict. Trocar para "resnet50" (ou outro nome já
# registrado) volta o serviço a usar um único modelo, sem mexer em mais
# nada — é exatamente o "recuo para ResNet-50" previsto no plano de
# execução do treino, caso o ensemble não fique pronto a tempo.
ACTIVE_MODEL_NAME = "ensemble_stacking"

MODEL_VERSION = "0.1.0"

EXAM_DOMAIN = "gastrointestinal"