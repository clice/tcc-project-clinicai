"""Configurações centrais do serviço de IA do ClinicAI."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AI_ROOT_DIR = BASE_DIR.parent

# =========================================================
# ARTEFATOS DOS MODELOS — organizados por domínio clínico
# =========================================================

MODEL_DIR = AI_ROOT_DIR / "models" / "exported"
GASTROINTESTINAL_MODEL_DIR = MODEL_DIR / "gastrointestinal"

RESNET50_WEIGHTS_PATH = GASTROINTESTINAL_MODEL_DIR / "resnet50.pt"
EFFICIENTNET_B4_WEIGHTS_PATH = GASTROINTESTINAL_MODEL_DIR / "efficientnet_b4.pt"
PVT_V2_B2_WEIGHTS_PATH = GASTROINTESTINAL_MODEL_DIR / "pvt_v2_b2.pt"
META_CLASSIFIER_PATH = GASTROINTESTINAL_MODEL_DIR / "meta_classificador.joblib"
MODEL_MANIFEST_PATH = GASTROINTESTINAL_MODEL_DIR / "manifesto_modelos.json"

MODEL_ARTIFACTS_BY_DOMAIN: dict[str, tuple[Path, ...]] = {
    "gastrointestinal": (
        RESNET50_WEIGHTS_PATH,
        EFFICIENTNET_B4_WEIGHTS_PATH,
        PVT_V2_B2_WEIGHTS_PATH,
        META_CLASSIFIER_PATH,
    ),
}
MODEL_MANIFEST_BY_DOMAIN: dict[str, Path] = {
    "gastrointestinal": MODEL_MANIFEST_PATH,
}

TIMM_MODEL_NAMES = {
    "resnet50": "resnet50",
    "efficientnet_b4": "efficientnet_b4",
    "pvt_v2_b2": "pvt_v2_b2",
}

# =========================================================
# DOMÍNIOS, TIPOS DE EXAME E CLASSES
# =========================================================

EXAM_TYPE_TO_DOMAIN = {
    "endoscopy": "gastrointestinal",
    "colonoscopy": "gastrointestinal",
}

ACTIVE_MODEL_BY_DOMAIN = {
    "gastrointestinal": "ensemble_stacking",
}

# Domínio padrão usado pelos metadados do modelo ativo.
DEFAULT_DOMAIN = "gastrointestinal"

CLASS_LABELS_BY_DOMAIN: dict[str, dict[int, str]] = {
    "gastrointestinal": {
        0: "normal",
        1: "abnormal",
    },
}

# Atalho para as classes do domínio atualmente ativo.
CLASS_LABELS = CLASS_LABELS_BY_DOMAIN[DEFAULT_DOMAIN]
MODEL_VERSION_FALLBACK = "0.1.0"
MODEL_VERSION = MODEL_VERSION_FALLBACK

# =========================================================
# LIMITES DE ENTRADA
# =========================================================

MAX_INFERENCE_IMAGE_BYTES = 10 * 1024 * 1024
MAX_INFERENCE_IMAGE_WIDTH = 12_000
MAX_INFERENCE_IMAGE_HEIGHT = 12_000
MAX_INFERENCE_IMAGE_PIXELS = 40_000_000
ALLOWED_INFERENCE_IMAGE_FORMATS = frozenset({"JPEG", "PNG"})

# =========================================================
# PRÉ-PROCESSAMENTO
# =========================================================

TARGET_IMAGE_SIZE = (224, 224)
NORMALIZE_MEAN = [0.485, 0.456, 0.406]
NORMALIZE_STD = [0.229, 0.224, 0.225]
