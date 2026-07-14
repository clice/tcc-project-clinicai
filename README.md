# ClinicAI

Sistema web acadêmico para gestão de clínicas e apoio à análise de imagens de exames
gastrointestinais. O projeto integra uma interface React, uma API FastAPI, PostgreSQL e um
serviço de inteligência artificial com Ensemble Stacking e Grad-CAM.

> **Estado:** protótipo em desenvolvimento. O sistema ainda possui pendências funcionais, de
> segurança e de integração e não foi validado para uso clínico ou diagnóstico.

## Autoria

| Nome | Função | Contato |
|---|---|---|
| Clice Bezerra Brito Romão | Autora | clice.romao@aluno.ufca.edu.br |
| Luana Batista da Cruz | Orientadora | luana.batista@ufca.edu.br |

## Funcionalidades

- autenticação JWT com tokens de acesso e renovação;
- usuários, clínicas, pacientes, perfis e permissões;
- controle de acesso por permissão e escopo de clínica;
- exames, upload de imagens, fluxo de status e revisão médica;
- logs de auditoria;
- classificação binária de imagens gastrointestinais;
- Ensemble Stacking com ResNet-50, EfficientNet-B4, PVTv2-B2 e regressão logística;
- geração de Grad-CAM para apoio à explicabilidade.

## Tecnologias

| Componente | Tecnologias principais |
|---|---|
| Frontend | React, Vite, CoreUI, React Router e Axios |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic e JWT |
| Banco de dados | PostgreSQL 16 |
| Inteligência artificial | PyTorch, timm, OpenCV, Pillow e scikit-learn |
| Infraestrutura local | Docker e Docker Compose |

## Arquitetura

```text
Frontend (React) → Backend (FastAPI) → PostgreSQL
                          ↓
                 Serviço de IA (FastAPI)
                          ↓
          Pesos + meta-classificador + Grad-CAM
```

## Estrutura do repositório

```text
tcc-project-clinicai/
├── ai/                       # Inferência, modelos e treinamento
├── backend/                  # API, regras de negócio e migrations
├── frontend/                 # Interface React
├── scripts/                  # Distribuição dos artefatos de IA
├── tests/                    # Testes da distribuição dos modelos
├── docker-compose.yml        # Ambiente local com CPU
├── docker-compose.gpu.yml    # Override opcional para GPU NVIDIA
├── .env.example              # Versão da release dos modelos
└── README.md
```

## Instalação local com Docker

### 1. Pré-requisitos

- Git;
- Docker Engine com Docker Compose Plugin, ou Docker Desktop;
- pelo menos 8 GB de RAM recomendados para carregar o conjunto completo em CPU;
- acesso à internet no primeiro download dos modelos;
- opcionalmente, NVIDIA Container Toolkit para executar a IA com GPU NVIDIA.

Não é necessário instalar Python, Node.js ou PostgreSQL na máquina que executará o sistema.

### 2. Clonar o repositório

```bash
git clone https://github.com/clice/tcc-project-clinicai.git
cd tcc-project-clinicai
```

### 3. Criar os arquivos de ambiente

No Linux, macOS ou Git Bash:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

No PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Defina uma `SECRET_KEY` própria em `backend/.env`, confira se `DATABASE_URL` usa o host Docker
`db` e confirme em `.env` a tag publicada em `MODEL_RELEASE_TAG`.

### 4. Baixar e validar os modelos

```bash
docker compose --profile models run --rm model-downloader
```

O inicializador baixa `manifesto_modelos.json`, valida domínio, tag e lista de artefatos, baixa
somente arquivos ausentes ou inválidos e verifica tamanho e SHA-256 antes de instalá-los em
`ai/models/exported/gastrointestinal/`.

Artefatos esperados:

```text
resnet50.pt
efficientnet_b4.pt
pvt_v2_b2.pt
meta_classificador.joblib
manifesto_modelos.json
```

Se a conexão cair ou um hash não corresponder, o comando termina com erro e não instala o
arquivo parcial. Execute novamente depois de corrigir a causa; arquivos válidos são preservados.

### 5. Subir o sistema

Com CPU:

```bash
docker compose up --build -d
```

Com GPU NVIDIA:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
```

O backend aguarda o PostgreSQL, aplica as migrations do Alembic e executa os seeds idempotentes.

### 6. Verificar a inicialização

```bash
docker compose ps
docker compose logs -f ai backend
```

| Serviço | Endereço local |
|---|---|
| Frontend | http://localhost:3000 |
| API do backend | http://localhost:8000 |
| Swagger do backend | http://localhost:8000/docs |
| API de IA | http://localhost:8001 |
| Swagger da IA | http://localhost:8001/docs |

Depois da subida, valide `GET /health` e `GET /models` no serviço de IA antes de testar
`POST /predict` com uma imagem autorizada e anonimizada.

### 7. Encerrar o ambiente

```bash
docker compose down
```

`docker compose down -v` também apaga os volumes e é uma ação destrutiva.

## Publicação dos modelos em uma GitHub Release

### 1. Preparar os artefatos

Coloque os arquivos finais, sem adicioná-los ao Git, em:

```text
ai/models/exported/gastrointestinal/resnet50.pt
ai/models/exported/gastrointestinal/efficientnet_b4.pt
ai/models/exported/gastrointestinal/pvt_v2_b2.pt
ai/models/exported/gastrointestinal/meta_classificador.joblib
```

Confirme que a ordem das meta-features é ResNet-50, EfficientNet-B4 e PVTv2-B2, a mesma usada
por `ai/app/inference/domains/gastrointestinal.py`.

### 2. Gerar o manifesto

```bash
python scripts/generate_model_manifest.py \
  --release-tag models-v0.1.0 \
  --model-version 0.1.0
```

O comando gera `manifesto_modelos.json` com tamanho e SHA-256 dos quatro arquivos.

### 3. Criar a release

1. Abra **Releases** no GitHub e escolha **Draft a new release**.
2. Crie a tag `models-v0.1.0` ou a tag indicada no manifesto.
3. Anexe os quatro modelos e `manifesto_modelos.json`.
4. Confira os cinco nomes e publique a release.

Se qualquer peso, pré-processamento, classe ou meta-classificador mudar, publique uma nova tag.
Cada asset precisa ter menos de 2 GiB.

### 4. Testar a distribuição

Atualize `.env.example` com a tag publicada e execute em uma cópia limpa:

```bash
docker compose --profile models run --rm model-downloader
python -m unittest discover -s tests -v
```

O fluxo atual usa assets públicos. Para repositório privado, implemente download autenticado
separadamente e nunca coloque tokens no Compose ou no README.

## Credenciais de demonstração

| Perfil | E-mail | Senha inicial |
|---|---|---|
| Administrador master | admin@clinicai.com | clinicai123 |
| Médico | doctor@clinicai.com | clinicai123 |
| Médico | doctor2@clinicai.com | clinicai123 |
| Funcionário da clínica | staff@clinicai.com | clinicai123 |
| Funcionário inativo | inactive@clinicai.com | clinicai123 |

Troque essas senhas antes de qualquer demonstração fora de um ambiente local controlado.

## Testes

```bash
python -m unittest discover -s tests -v
docker compose exec backend pytest -q
```

## Administração da matriz RBAC

O executor `python -m app.modules.seeds` realiza apenas o bootstrap inicial. Depois disso, as
edições administrativas permanecem como fonte da verdade. Mudanças oficiais devem ser feitas
por migrations de dados do Alembic.

Para descartar customizações e restaurar toda a matriz padrão:

```bash
docker compose exec backend python -m app.modules.role_permissions.reconcile \
  --confirm RECONCILE_RBAC
```

## Limitações e responsabilidade de uso

- o projeto ainda não está pronto para implantação pública;
- não utilize dados reais de pacientes nem imagens sem autorização e anonimização;
- a saída da IA é experimental e não substitui avaliação médica;
- o Compose atual é destinado ao desenvolvimento local;
- a produção será tratada depois das correções e testes pendentes.

## Licença

Projeto acadêmico desenvolvido para fins educacionais. A licença de distribuição ainda deve ser
formalizada antes da disponibilização pública definitiva.
