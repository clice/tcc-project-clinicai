"""
Configurações centrais do serviço de IA.

Fonte única de verdade para todos os caminhos usados pelo módulo.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AI_ROOT_DIR = BASE_DIR.parent

# =========================================================
# PESOS DOS MODELOS — organizados por domínio clínico
# =========================================================

MODEL_DIR = AI_ROOT_DIR / "models" / "exported"

# Cada domínio clínico tem sua própria subpasta de pesos dentro de
# MODEL_DIR — deixa claro no disco qual modelo pertence a qual domínio, e
# evita colisão de nomes (ex: um "resnet50.pt" gastrointestinal e outro
# de tomografia de cabeça, ambos existindo ao mesmo tempo sem conflito).
GASTROINTESTINAL_MODEL_DIR = MODEL_DIR / "gastrointestinal"

RESNET50_WEIGHTS_PATH = GASTROINTESTINAL_MODEL_DIR / "resnet50.pt"
EFFICIENTNET_B4_WEIGHTS_PATH = GASTROINTESTINAL_MODEL_DIR / "efficientnet_b4.pt"
PVT_V2_B2_WEIGHTS_PATH = GASTROINTESTINAL_MODEL_DIR / "pvt_v2_b2.pt"
META_CLASSIFIER_PATH = GASTROINTESTINAL_MODEL_DIR / "meta_classificador.joblib"

# Nome do timm exato de cada arquitetura — usado por TimmCNNPredictor.
TIMM_MODEL_NAMES = {
    "resnet50": "resnet50",
    "efficientnet_b4": "efficientnet_b4",
    "pvt_v2_b2": "pvt_v2_b2",
}

# =========================================================
# DOMÍNIOS CLÍNICOS E ROTEAMENTO POR TIPO DE EXAME
# =========================================================

# Mapeia o `exam_type` do backend (o que o médico escolhe ao submeter o
# exame) para o domínio clínico correspondente no módulo de IA. Vários
# tipos de exame podem cair no mesmo domínio — endoscopia e colonoscopia,
# por exemplo, usam o mesmo conjunto de modelos gastrointestinais.
#
# Para adicionar um novo tipo de exame a um domínio já existente, basta
# uma linha nova aqui. Para adicionar um domínio inteiramente novo (ex:
# tomografia de cabeça), ver `app/inference/domains/README.md`.
EXAM_TYPE_TO_DOMAIN = {
    "endoscopy": "gastrointestinal",
    "colonoscopy": "gastrointestinal",
}

# Modelo ativo (já registrado em `app.inference.domains`) usado por
# padrão em cada domínio. Trocar aqui volta um domínio para um modelo
# isolado (ex: "resnet50" em vez de "ensemble_stacking") sem mexer em
# mais nada — é o "recuo" previsto no plano de execução do treino, caso
# o ensemble de algum domínio não fique pronto a tempo.
ACTIVE_MODEL_BY_DOMAIN = {
    "gastrointestinal": "ensemble_stacking",
}

# Domínio assumido quando o backend não informa `exam_type`, ou informa
# um tipo ainda não mapeado em EXAM_TYPE_TO_DOMAIN.
DEFAULT_DOMAIN = "gastrointestinal"

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

# Válido hoje para o domínio gastrointestinal (triagem binária). Um
# domínio novo com categorias diferentes (ex: BI-RADS em mamografia)
# precisará de seu próprio mapa de classes — ver nota em
# `app/inference/domains/README.md`.
CLASS_LABELS = {
    0: "normal",
    1: "abnormal",
}

MODEL_VERSION = "0.1.0"
