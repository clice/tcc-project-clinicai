# Como adicionar um novo domínio clínico (ex: tomografia de cabeça, mamografia)

Hoje só existe o domínio `gastrointestinal` (endoscopia/colonoscopia).
Estes são os passos para adicionar um domínio novo, sem precisar mudar
nenhum código já existente — `predictor.py`, `main.py` e o backend
principal não sabem nada sobre domínios específicos, só sobre a
resolução via `registry.resolve_active_predictor()`.

## 1. Crie a pasta de pesos do domínio

```
ai/models/exported/head_ct/
    resnet50.pt              (ou o(s) modelo(s) que você treinar)
    meta_classificador.joblib  (se for um ensemble)
```

## 2. Adicione os caminhos em `app/config.py`

```python
HEAD_CT_MODEL_DIR = MODEL_DIR / "head_ct"
HEAD_CT_RESNET50_WEIGHTS_PATH = HEAD_CT_MODEL_DIR / "resnet50.pt"
```

## 3. Crie `app/inference/domains/head_ct.py`

Copie a estrutura de `gastrointestinal.py` como referência. O mínimo:

```python
from app.config import HEAD_CT_RESNET50_WEIGHTS_PATH, TIMM_MODEL_NAMES
from app.inference.registry import register
from app.inference.timm_predictor import TimmCNNPredictor

DOMAIN = "head_ct"

resnet50 = TimmCNNPredictor(
    name="resnet50",
    domain=DOMAIN,
    timm_model_name=TIMM_MODEL_NAMES["resnet50"],
    weights_path=HEAD_CT_RESNET50_WEIGHTS_PATH,
)

register(resnet50)
```

Se for um Ensemble Stacking como o gastrointestinal, siga o mesmo padrão
com `EnsembleStackingPredictor` — a interface é a mesma, independente do
domínio.

## 4. Registre o import em `app/inference/domains/__init__.py`

```python
from app.inference.domains import head_ct  # noqa: F401
```

## 5. Mapeie o(s) tipo(s) de exame e o modelo ativo em `app/config.py`

```python
EXAM_TYPE_TO_DOMAIN = {
    "endoscopy": "gastrointestinal",
    "colonoscopy": "gastrointestinal",
    "head_ct": "head_ct",  # <- novo
}

ACTIVE_MODEL_BY_DOMAIN = {
    "gastrointestinal": "ensemble_stacking",
    "head_ct": "resnet50",  # <- novo
}
```

## 6. Confirme que o `exam_type` existe no frontend/backend

O valor usado em `EXAM_TYPE_TO_DOMAIN` precisa bater com o que o
backend envia (`Exam.exam_type`) — hoje isso é validado em
`frontend/src/utils/constants.js` (`examTypeOptions`). Adicionar um tipo
de exame novo no sistema é uma mudança separada, no backend/frontend
principal, não neste módulo de IA.

## Atenção — coisas que PODEM precisar mudar para um domínio muito diferente

- **Classes diferentes de "normal"/"abnormal"**: `app.config.CLASS_LABELS`
  hoje é fixo para classificação binária. Um domínio com categorias
  diferentes (ex: BI-RADS em mamografia, com várias classes) vai precisar
  de um mapa de classes por domínio, não um único `CLASS_LABELS` global —
  isso ainda não foi implementado, é um ponto de atenção para quando
  chegar a hora.
- **Pré-processamento diferente**: hoje `app/inference/preprocess.py`
  usa um único pipeline (ROI + remoção de reflexo especular), pensado
  para imagens endoscópicas. Um domínio de imagem muito diferente (ex:
  tomografia, com outro formato/contraste) provavelmente precisa do
  próprio pipeline de pré-processamento — nesse caso, `preprocess_image()`
  também precisaria aceitar um `domain` e escolher o pipeline certo.
- **Grad-CAM**: `app/explainability/gradcam.py` hoje está amarrado à
  ResNet-50 do domínio gastrointestinal. Para gerar Grad-CAM de outro
  domínio, essa função precisa ser generalizada para receber qual modelo
  usar como base (qualquer CNN registrada, do domínio correspondente).
  