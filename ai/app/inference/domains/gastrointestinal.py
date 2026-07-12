"""
Modelos preditivos do domínio gastrointestinal (endoscopia, colonoscopia).

Importado uma única vez por `app.inference.domains` (o pacote), na subida
do serviço — isso registra os modelos antes de qualquer requisição
chegar. Ver `README.md` nesta pasta para o passo a passo de como
adicionar um domínio clínico novo.
"""

from app.config import (
    EFFICIENTNET_B4_WEIGHTS_PATH,
    META_CLASSIFIER_PATH,
    PVT_V2_B2_WEIGHTS_PATH,
    RESNET50_WEIGHTS_PATH,
    TIMM_MODEL_NAMES,
)
from app.inference.ensemble_stacking import EnsembleStackingPredictor
from app.inference.registry import register
from app.inference.timm_predictor import TimmCNNPredictor

DOMAIN = "gastrointestinal"

resnet50 = TimmCNNPredictor(
    name="resnet50",
    domain=DOMAIN,
    timm_model_name=TIMM_MODEL_NAMES["resnet50"],
    weights_path=RESNET50_WEIGHTS_PATH,
)

efficientnet_b4 = TimmCNNPredictor(
    name="efficientnet_b4",
    domain=DOMAIN,
    timm_model_name=TIMM_MODEL_NAMES["efficientnet_b4"],
    weights_path=EFFICIENTNET_B4_WEIGHTS_PATH,
)

pvt_v2_b2 = TimmCNNPredictor(
    name="pvt_v2_b2",
    domain=DOMAIN,
    timm_model_name=TIMM_MODEL_NAMES["pvt_v2_b2"],
    weights_path=PVT_V2_B2_WEIGHTS_PATH,
)

# ORDEM IMPORTA: precisa bater com `ordem_dos_modelos` do
# manifesto_inferencia.json gerado pelo notebook de treino.
ensemble_stacking = EnsembleStackingPredictor(
    name="ensemble_stacking",
    domain=DOMAIN,
    base_predictors=[resnet50, efficientnet_b4, pvt_v2_b2],
    meta_classifier_path=META_CLASSIFIER_PATH,
)

register(resnet50)
register(efficientnet_b4)
register(pvt_v2_b2)
register(ensemble_stacking)
