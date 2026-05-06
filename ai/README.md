# ClinicAI — Módulo de Inteligência Artificial

Este diretório contém a estrutura inicial da parte de Inteligência Artificial do projeto **ClinicAI**.

O objetivo deste módulo é organizar os códigos, modelos, experimentos e futuras APIs responsáveis pela análise automatizada de imagens de exames endoscópicos e colonoscópicos.

---

## Objetivo da IA

A proposta inicial da IA no ClinicAI é realizar uma classificação binária de imagens médicas, indicando se uma imagem de exame apresenta características:

- normais;
- suspeitas ou anormais.

O resultado da IA será utilizado como ferramenta de apoio à decisão médica, não substituindo a avaliação de um profissional de saúde.

---

## Estrutura do diretório

```txt
ai/
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── inference/
│   │   ├── predictor.py
│   │   ├── preprocess.py
│   │   └── gradcam.py
│   └── models/
├── notebooks/
├── training/
├── datasets/
├── requirements.txt
├── Dockerfile
└── README.md
```

### Descrição das pastas

#### `app/`

Contém a futura API de inferência da IA.

Essa API será responsável por receber imagens de exames, executar o modelo treinado e retornar o resultado da análise.

#### `app/inference/`

Contém os arquivos relacionados ao fluxo de inferência.

- `preprocess.py`: preparação da imagem antes da predição.
- `predictor.py`: carregamento do modelo e execução da classificação.
- `gradcam.py`: geração futura do mapa de explicabilidade GradCAM.

#### `app/models/`

Diretório reservado para armazenar os modelos treinados exportados, como arquivos `.pt`, `.pth` ou formatos equivalentes.

Por segurança e organização, os modelos pesados não devem ser versionados diretamente no GitHub sem necessidade.

#### `notebooks/`

Contém notebooks utilizados para exploração, testes, treinamento inicial e análise dos datasets.

#### `training/`

Contém scripts de treinamento, avaliação e comparação entre modelos.

#### `datasets/`

Diretório reservado para organização local dos datasets usados nos experimentos.

Os datasets não devem ser enviados ao GitHub, principalmente por tamanho, licença e privacidade.

---

## Fluxo futuro da IA

O fluxo planejado para integração da IA ao ClinicAI será:

Imagem do exame
→ Pré-processamento
→ Modelo de classificação
→ Resultado da predição
→ Confiança da predição
→ GradCAM
→ API de IA
→ Backend principal
→ Banco de dados
→ Frontend

---

## Tecnologias previstas

- Python
- FastAPI
- PyTorch
- OpenCV
- Pillow
- NumPy
- scikit-learn
- Matplotlib
- GradCAM

---

## Aviso importante

Este módulo tem finalidade acadêmica e experimental dentro do contexto do Trabalho de Conclusão de Curso.

Os resultados gerados pela IA devem ser interpretados como apoio à decisão médica e não como diagnóstico definitivo.

