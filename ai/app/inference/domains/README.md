# Como adicionar um novo domínio clínico

O contrato da CHK-12 exige que cada requisição informe `exam_type`. O serviço
resolve esse valor para um domínio, escolhe o modelo ativo e usa o catálogo de
classes daquele domínio. Tipos ausentes ou não mapeados retornam HTTP 422; não
há fallback silencioso para gastrointestinal.

## 1. Declare artefatos, manifesto e classes em `app/config.py`

Cada domínio precisa informar:

- caminhos de todos os artefatos em `MODEL_ARTIFACTS_BY_DOMAIN`;
- caminho do manifesto em `MODEL_MANIFEST_BY_DOMAIN`;
- tipos de exame em `EXAM_TYPE_TO_DOMAIN`;
- modelo ativo em `ACTIVE_MODEL_BY_DOMAIN`;
- mapa de classes em `CLASS_LABELS_BY_DOMAIN`.

Exemplo resumido:

```python
HEAD_CT_MODEL_DIR = MODEL_DIR / "head_ct"
HEAD_CT_RESNET50_PATH = HEAD_CT_MODEL_DIR / "resnet50.pt"
HEAD_CT_MANIFEST_PATH = HEAD_CT_MODEL_DIR / "manifesto_modelos.json"

MODEL_ARTIFACTS_BY_DOMAIN["head_ct"] = (HEAD_CT_RESNET50_PATH,)
MODEL_MANIFEST_BY_DOMAIN["head_ct"] = HEAD_CT_MANIFEST_PATH
EXAM_TYPE_TO_DOMAIN["head_ct"] = "head_ct"
ACTIVE_MODEL_BY_DOMAIN["head_ct"] = "resnet50"
CLASS_LABELS_BY_DOMAIN["head_ct"] = {0: "normal", 1: "abnormal"}
```

O domínio gastrointestinal atual possui exatamente quatro artefatos: três
`state_dict` e um meta-classificador. Um domínio novo pode ter outra quantidade,
mas a regra de readiness deve ser ajustada de forma consciente caso não use o
mesmo contrato de ensemble.

## 2. Crie e registre o preditor

Crie `app/inference/domains/head_ct.py` e registre o preditor com namespace de
domínio:

```python
from app.inference.registry import register
from app.inference.timm_predictor import TimmCNNPredictor

resnet50 = TimmCNNPredictor(
    name="resnet50",
    domain="head_ct",
    timm_model_name="resnet50",
    weights_path=HEAD_CT_RESNET50_PATH,
    num_classes=len(CLASS_LABELS_BY_DOMAIN["head_ct"]),
)
register(resnet50)
```

Depois importe o módulo em `app/inference/domains/__init__.py`.

## 3. Publique um manifesto compatível

O manifesto deve conter ao menos:

```json
{
  "domain": "head_ct",
  "model_version": "models-v1.0.0",
  "artifacts": [{"name": "resnet50.pt"}]
}
```

A versão gravada no banco vem desse manifesto, não de uma constante solta no
código.

## 4. Atualize backend e frontend

O valor persistido em `Exam.exam_type` precisa corresponder exatamente a uma
chave de `EXAM_TYPE_TO_DOMAIN`. O cliente backend envia esse campo no multipart
e valida que `exam_type` e `exam_domain` retornados correspondem ao pedido.

## 5. Pré-processamento e explicabilidade

O pipeline atual ainda é específico para imagens gastrointestinais. Um domínio
com modalidade diferente deve selecionar seu próprio pré-processamento. O
Grad-CAM clássico está habilitado apenas para `gastrointestinal` e usa a
ResNet-50 como explicador parcial do ensemble; outros domínios retornam
`gradcam_available=false` até possuírem explicador próprio.
