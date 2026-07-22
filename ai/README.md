# ClinicAI — Módulo de Inteligência Artificial

Este diretório contém o serviço de Inteligência Artificial integrado ao ClinicAI, além dos componentes de inferência, treinamento e verificação dos modelos usados no protótipo acadêmico.

## Finalidade

O módulo realiza a classificação binária de imagens endoscópicas gastrointestinais nas classes `normal` e `abnormal`. O resultado inclui a classe predita, a confiança associada, metadados do modelo e, quando disponível, um mapa de atribuição Grad-CAM.

A saída é apresentada como apoio computacional à revisão médica. Ela não constitui diagnóstico definitivo, validação clínica nem recomendação terapêutica.

## Modelo operacional

O serviço utiliza um *Ensemble Stacking* composto por:

- ResNet-50;
- EfficientNet-B4;
- PVTv2-B2;
- meta-classificador de regressão logística.

Os artefatos operacionais pertencem à versão `0.1.1`, distribuída pela GitHub Release `models-v0.1.1`. Eles correspondem ao fold 3 do protocolo `viana_codigo_kfold3_roi_sh_da`, selecionado como execução representativa pela proximidade de seu resultado à média agregada dos três folds, sem alegação de superioridade estatística.

Os pesos não são versionados no repositório. A instalação, o manifesto de integridade e o processo de atualização estão descritos em [`../docs/model-release-guide.md`](../docs/model-release-guide.md).

## Fluxo de inferência

```text
Imagem e tipo de exame
        ↓
Validação e resolução do domínio
        ↓
Pré-processamento gastrointestinal
        ↓
Modelos base e Ensemble Stacking
        ↓
Classe, confiança e metadados
        ↓
Grad-CAM
        ↓
Backend, banco de dados e frontend
```

O pipeline gastrointestinal aplica extração da região de interesse (ROI) e remoção de reflexos especulares de forma compatível com o protocolo de treinamento. A explicabilidade utiliza a ResNet-50 como explicador parcial do ensemble e não representa uma justificativa causal da decisão.

## Organização

```text
ai/
├── app/                  # API, configuração e inferência
│   ├── inference/        # preditores, registro de domínios e Grad-CAM
│   └── main.py           # aplicação FastAPI
├── models/exported/      # artefatos instalados localmente e ignorados pelo Git
├── training/             # treinamento e avaliação experimental
├── tests/                # testes automatizados do módulo
├── Dockerfile
├── requirements.txt
└── README.md
```

Datasets e artefatos pesados permanecem fora do Git por tamanho, licença e privacidade. Não devem ser utilizados dados clínicos reais neste protótipo.

## Execução

A partir da raiz do projeto, instale os modelos e suba o serviço:

```bash
docker compose --profile models run --rm model-downloader
docker compose up --build -d ai
```

A documentação interativa fica disponível em <http://localhost:8001/docs>. Para verificar o módulo:

```bash
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  ai -m unittest discover -s tests -p 'test_*.py' -v
```

## Tecnologias

- Python e FastAPI;
- PyTorch, torchvision e timm;
- OpenCV, Pillow e NumPy;
- scikit-learn e joblib;
- Grad-CAM.

## Limitações

O domínio implementado é o gastrointestinal. A estrutura admite o registro explícito de novos domínios, mas cada modalidade exige artefatos, classes, pré-processamento e explicabilidade próprios. As orientações técnicas estão em [`app/inference/domains/README.md`](app/inference/domains/README.md).

Este módulo foi desenvolvido exclusivamente para fins acadêmicos e demonstrativos no Trabalho de Conclusão de Curso.
