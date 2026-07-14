"""
Instancia e registra todos os modelos preditivos disponíveis no ClinicAI.

Importado uma única vez, em `app.main`, na subida do serviço — isso
popula o registro (`registry.py`) antes de qualquer requisição chegar.

Para adicionar um modelo novo no futuro:
1. Se for uma arquitetura disponível no `timm`, instancie um
   `TimmCNNPredictor` novo (só precisa do nome do timm + caminho dos
   pesos) e registre com `register(...)`.
2. Se for uma arquitetura fora do `timm`, implemente `BasePredictor` num
   arquivo novo e registre do mesmo jeito.
3. Nenhum outro arquivo do sistema (`predictor.py`, `main.py`) precisa
   mudar — eles só conhecem `ACTIVE_MODEL_NAME` e o registro.
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

resnet50 = TimmCNNPredictor(
    name="resnet50",
    timm_model_name=TIMM_MODEL_NAMES["resnet50"],
    weights_path=RESNET50_WEIGHTS_PATH,
)

efficientnet_b4 = TimmCNNPredictor(
    name="efficientnet_b4",
    timm_model_name=TIMM_MODEL_NAMES["efficientnet_b4"],
    weights_path=EFFICIENTNET_B4_WEIGHTS_PATH,
)

pvt_v2_b2 = TimmCNNPredictor(
    name="pvt_v2_b2",
    timm_model_name=TIMM_MODEL_NAMES["pvt_v2_b2"],
    weights_path=PVT_V2_B2_WEIGHTS_PATH,
)

# ORDEM IMPORTA: precisa bater com `ordem_dos_modelos` do
# manifesto_inferencia.json gerado pelo notebook de treino.
ensemble_stacking = EnsembleStackingPredictor(
    base_predictors=[resnet50, efficientnet_b4, pvt_v2_b2],
    meta_classifier_path=META_CLASSIFIER_PATH,
)

register("resnet50", resnet50)
register("efficientnet_b4", efficientnet_b4)
register("pvt_v2_b2", pvt_v2_b2)
register("ensemble_stacking", ensemble_stacking)
