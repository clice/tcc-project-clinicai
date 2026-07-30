# Módulo de Inteligência Artificial

Este diretório contém o serviço de Inteligência Artificial integrado ao ClinicAI, além dos
componentes de inferência, treinamento e verificação dos modelos utilizados no protótipo
acadêmico.

## Finalidade

O módulo realiza classificação binária de imagens gastrointestinais nas classes `normal` e
`abnormal`.

A resposta inclui:

- tipo e domínio do exame;
- classe predita;
- confiança;
- nome e versão do modelo;
- dispositivo utilizado;
- mapa Grad-CAM quando disponível;
- metadados do método de atribuição.

A saída é um recurso computacional de apoio à análise médica. Ela não constitui diagnóstico,
validação clínica, localização confirmada de lesão ou recomendação terapêutica.

## Domínio implementado

O domínio ativo é `gastrointestinal`, associado aos tipos de exame:

- `endoscopy`;
- `colonoscopy`.

Não existe *fallback* silencioso para esse domínio. Tipos ausentes ou não mapeados são
rejeitados.

## Modelo operacional

O serviço utiliza um *Ensemble Stacking* composto por:

- ResNet-50;
- EfficientNet-B4;
- PVTv2-B2;
- meta-classificador de Regressão Logística.

A ordem das entradas do meta-classificador é ResNet-50, EfficientNet-B4 e PVTv2-B2.

Os artefatos operacionais atuais correspondem a:

- versão: `0.1.2`;
- GitHub Release: `models-v0.1.2`;
- protocolo: `viana_codigo_kfold3_roi_sh_da`;
- fold operacional: `1`;
- critério: melhor desempenho entre os três folds em acurácia e F1-*Score*.

Os pesos não são armazenados no histórico do Git. A instalação e a atualização estão descritas
em [`../docs/model-release-guide.md`](../docs/model-release-guide.md).

## Artefatos necessários

```text
ai/models/exported/gastrointestinal/
├── resnet50.pt
├── efficientnet_b4.pt
├── pvt_v2_b2.pt
├── meta_classificador.joblib
└── manifesto_modelos.json
```

O serviço somente fica pronto quando os quatro artefatos declarados e o manifesto compatível
estão disponíveis. A versão informada nas respostas é lida do manifesto.

## Fluxo de inferência

```text
Imagem + exam_type
        ↓
Validação da entrada
        ↓
Resolução explícita do domínio
        ↓
Pré-processamento gastrointestinal
        ↓
ResNet-50 + EfficientNet-B4 + PVTv2-B2
        ↓
Meta-classificador do Ensemble Stacking
        ↓
Classe, confiança e metadados
        ↓
Grad-CAM combinado
        ↓
Backend, persistência e frontend
```

## Pré-processamento

O pipeline gastrointestinal aplica:

- extração da região de interesse;
- remoção de reflexos especulares;
- redimensionamento para `224 × 224`;
- normalização com média e desvio padrão da ImageNet.

A entrada aceita JPEG e PNG dentro dos limites de tamanho, dimensões e quantidade de pixels
definidos em `app/config.py`.

## Explicabilidade

Para o `ensemble_stacking` gastrointestinal, o serviço gera um mapa de atribuição a partir das
três arquiteturas base.

O método combina os mapas da ResNet-50, EfficientNet-B4 e PVTv2-B2 com pesos orientados pela
evidência local fornecida ao meta-classificador para a predição específica.

A resposta inclui, quando disponíveis:

- `attribution_method`;
- `attribution_target_layers`;
- `attribution_local_evidence`;
- `attribution_branch_weights`;
- `attribution_branch_cam_raw_maxima`;
- `attribution_unavailable_reason`.

O mapa é retornado em Base64, com MIME e SHA-256, para validação e persistência pelo backend.

## Organização

```text
ai/
├── app/
│   ├── explainability/        # geração dos mapas de atribuição
│   ├── inference/             # registro, preditores, runtime e domínios
│   ├── config.py              # artefatos, classes, tipos e limites
│   └── main.py                # aplicação FastAPI
├── models/exported/           # artefatos instalados localmente
├── training/                  # treinamento e avaliação experimental
├── tests/                     # testes automatizados
├── Dockerfile
├── requirements.txt
└── README.md
```

Datasets completos e artefatos pesados permanecem fora do Git por tamanho, licença e
reprodutibilidade. Não devem ser utilizados dados clínicos reais neste protótipo.

## Execução

A partir da raiz:

```bash
docker compose --profile models run --rm model-downloader
docker compose up --build -d ai
```

A API fica disponível em:

```text
http://localhost:8001
http://localhost:8001/docs
```

## Verificação

```bash
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  ai -m unittest discover -s tests -p 'test_*.py' -v
```

Para verificar a distribuição dos modelos:

```bash
python3 -m unittest tests.test_model_distribution
```

## Tecnologias

- Python e FastAPI;
- PyTorch, torchvision e timm;
- OpenCV, Pillow e NumPy;
- scikit-learn e joblib;
- pytorch-grad-cam.

## Novos domínios

A estrutura admite o registro explícito de novos domínios, mas cada modalidade exige classes,
artefatos, pré-processamento, validação e explicabilidade próprios.

Consulte
[`app/inference/domains/README.md`](app/inference/domains/README.md).

## Limitações

O módulo foi desenvolvido exclusivamente para fins acadêmicos e demonstrativos. O desempenho
experimental não representa desempenho diagnóstico em pacientes reais nem autorização para
uso assistencial.
