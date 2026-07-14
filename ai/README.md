# ClinicAI — Módulo de Inteligência Artificial

Este diretório contém o serviço de inferência do ClinicAI para imagens de endoscopia e
colonoscopia. O módulo implementa pré-processamento, três modelos base, Ensemble Stacking e
Grad-CAM. O resultado é um apoio à decisão médica e não substitui o diagnóstico profissional.

## Componentes atuais

- `app/main.py`: API, health check e rota de predição;
- `app/config.py`: caminhos, domínio clínico e modelo ativo;
- `app/inference/domains/gastrointestinal.py`: registro dos modelos gastrointestinais;
- `app/inference/timm_predictor.py`: inferência dos modelos base;
- `app/inference/ensemble_stacking.py`: combinação pelo meta-classificador;
- `app/explainability/gradcam.py`: mapa de explicabilidade;
- `training/preprocessing/`: ROI, remoção de reflexos e CLAHE.

O modelo ativo do domínio gastrointestinal é `ensemble_stacking`, formado por ResNet-50,
EfficientNet-B4 e PVTv2-B2, seguido por um meta-classificador de regressão logística.

## Artefatos dos modelos

Os pesos não são versionados no Git. Eles são distribuídos pela Release configurada no `.env`
da raiz e instalados com:

```bash
docker compose --profile models run --rm model-downloader
```

O diretório final contém:

```text
ai/models/exported/gastrointestinal/
├── resnet50.pt
├── efficientnet_b4.pt
├── pvt_v2_b2.pt
├── meta_classificador.joblib
└── manifesto_modelos.json
```

O downloader valida tamanho e SHA-256 e só substitui a instalação depois que o conjunto
completo é validado. A ordem dos três modelos deve permanecer igual à usada no treinamento do
meta-classificador.

## API

Com o Docker Compose em execução:

- documentação: `http://localhost:8001/docs`;
- saúde: `GET http://localhost:8001/health`;
- modelos registrados: `GET http://localhost:8001/models`;
- inferência: `POST http://localhost:8001/predict` com `file` e `exam_type`.

Os tipos `endoscopy` e `colonoscopy` são direcionados ao domínio `gastrointestinal`.

## Execução isolada

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Consulte `app/inference/domains/README.md` para registrar outro domínio clínico e
`../docs/model-release-guide.md` para publicar ou atualizar os artefatos.

## Aviso importante

Este módulo tem finalidade acadêmica e experimental. Não foi validado como dispositivo médico
e não deve ser usado de forma autônoma para diagnóstico ou conduta clínica.
