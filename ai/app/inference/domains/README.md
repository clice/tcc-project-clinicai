# Como Adicionar um Novo Domínio de Inferência

Este guia descreve o contrato técnico para registrar um novo domínio no serviço de IA do
ClinicAI.

A inclusão de um domínio não implica validação clínica. Cada modalidade precisa de dados,
artefatos, testes, pré-processamento e explicabilidade próprios.

## 1. Mapear o tipo de exame

Cada requisição deve informar `exam_type`. O serviço resolve esse valor por meio de
`EXAM_TYPE_TO_DOMAIN`.

Tipos ausentes ou não mapeados retornam erro de validação. Não existe *fallback* silencioso para
o domínio gastrointestinal.

Em `app/config.py`, declare:

- artefatos em `MODEL_ARTIFACTS_BY_DOMAIN`;
- manifesto em `MODEL_MANIFEST_BY_DOMAIN`;
- tipos em `EXAM_TYPE_TO_DOMAIN`;
- modelo ativo em `ACTIVE_MODEL_BY_DOMAIN`;
- classes em `CLASS_LABELS_BY_DOMAIN`.

Exemplo resumido:

```python
HEAD_CT_MODEL_DIR = MODEL_DIR / "head_ct"
HEAD_CT_RESNET50_PATH = HEAD_CT_MODEL_DIR / "resnet50.pt"
HEAD_CT_MANIFEST_PATH = HEAD_CT_MODEL_DIR / "manifesto_modelos.json"

MODEL_ARTIFACTS_BY_DOMAIN["head_ct"] = (
    HEAD_CT_RESNET50_PATH,
)
MODEL_MANIFEST_BY_DOMAIN["head_ct"] = (
    HEAD_CT_MANIFEST_PATH
)
EXAM_TYPE_TO_DOMAIN["head_ct"] = "head_ct"
ACTIVE_MODEL_BY_DOMAIN["head_ct"] = "resnet50"
CLASS_LABELS_BY_DOMAIN["head_ct"] = {
    0: "normal",
    1: "abnormal",
}
```

O domínio gastrointestinal atual exige exatamente quatro artefatos: três pesos dos modelos base
e um meta-classificador. Um domínio novo pode ter outro contrato, mas a lógica de *readiness*
deve ser ajustada conscientemente.

## 2. Criar e registrar o preditor

Crie um módulo em `app/inference/domains/`, por exemplo `head_ct.py`, e registre o preditor com
o domínio correto:

```python
from app.inference.registry import register
from app.inference.timm_predictor import (
    TimmCNNPredictor,
)

resnet50 = TimmCNNPredictor(
    name="resnet50",
    domain="head_ct",
    timm_model_name="resnet50",
    weights_path=HEAD_CT_RESNET50_PATH,
)

register(resnet50)
```

Depois, importe o módulo em `app/inference/domains/__init__.py`.

O nome registrado deve coincidir com `ACTIVE_MODEL_BY_DOMAIN`.

## 3. Publicar um manifesto compatível

O manifesto deve registrar, no mínimo:

```json
{
  "schema_version": 1,
  "release_tag": "models-v1.0.0",
  "model_version": "1.0.0",
  "domain": "head_ct",
  "artifacts": [
    {
      "name": "resnet50.pt",
      "size_bytes": 123,
      "sha256": "HASH_SHA256_DE_64_CARACTERES"
    }
  ]
}
```

`release_tag` identifica a GitHub Release. `model_version` é a versão informada pelo serviço e
persistida pelo backend.

A versão da resposta é lida do manifesto, não de uma constante solta no código.

## 4. Atualizar o runtime

O runtime valida:

- presença do domínio;
- catálogo de classes;
- lista de artefatos;
- manifesto;
- nomes dos artefatos descritos;
- carregamento do preditor ativo;
- correspondência entre o preditor e os artefatos declarados.

A inicialização deve permanecer observável pelos endpoints de saúde e catálogo do serviço.

## 5. Atualizar backend e frontend

O valor persistido em `Exam.exam_type` precisa corresponder a uma chave de
`EXAM_TYPE_TO_DOMAIN`.

O backend envia esse valor ao serviço de IA e valida se `exam_type` e `exam_domain` retornados
correspondem ao pedido.

O frontend deve apresentar apenas tipos suportados pelo fluxo acadêmico implementado.

## 6. Pré-processamento

O pipeline gastrointestinal não deve ser reutilizado automaticamente em outra modalidade.

O novo domínio precisa definir, testar e documentar:

- decodificação da entrada;
- tamanho esperado;
- normalização;
- região de interesse;
- transformações específicas;
- ordem das classes.

## 7. Explicabilidade

O domínio gastrointestinal utiliza atribuição combinada das três arquiteturas do
`ensemble_stacking`.

Um novo domínio deve implementar explicitamente o próprio mecanismo de atribuição ou informar
que o recurso não está disponível. Não apresente um mapa produzido por arquitetura ou camada
incompatível como explicação válida para outro domínio.

A resposta deve manter coerência entre:

- classe final;
- mapa gerado;
- camada alvo;
- método de atribuição;
- motivo de indisponibilidade, quando aplicável.

## 8. Testes mínimos

Adicione testes para:

- resolução de `exam_type`;
- rejeição de tipo desconhecido;
- carregamento do manifesto;
- ausência ou adulteração de artefatos;
- catálogo de classes;
- formato das probabilidades;
- classe e confiança;
- contrato de atribuição;
- *readiness* e catálogo do runtime;
- integração do backend com o novo domínio.

Somente registre o novo domínio como ativo depois que os artefatos e o contrato correspondente
estiverem disponíveis.
