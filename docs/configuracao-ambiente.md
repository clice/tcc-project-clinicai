# Configuração de Ambiente do ClinicAI

Este documento registra a configuração reproduzível do ambiente local do ClinicAI. O
`docker-compose.yml` é voltado ao desenvolvimento e publica portas somente em `127.0.0.1`.
O ClinicAI é um protótipo acadêmico: esta é sua configuração oficial de demonstração local,
não uma configuração para uso clínico ou hospedagem pública.

## Arquivos locais

| Arquivo | Consumidor | Versionado? |
|---|---|---|
| `.env` | Docker Compose e distribuidor dos modelos | Não |
| `.env.example` | Modelo da configuração da raiz | Sim |
| `backend/.env` | Backend FastAPI | Não |
| `backend/.env.example` | Modelo da configuração do backend | Sim |
| `frontend/.env` | Frontend Vite | Não |
| `frontend/.env.example` | Modelo da configuração do frontend | Sim |

Crie os arquivos locais com:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

## Variáveis da raiz

| Variável | Finalidade |
|---|---|
| `COMPOSE_PROJECT_NAME` | Prefixo dos recursos do Compose |
| `POSTGRES_DB` | Nome do banco PostgreSQL |
| `POSTGRES_USER` | Usuário do PostgreSQL |
| `POSTGRES_PASSWORD` | Senha técnica do PostgreSQL |
| `POSTGRES_PORT` | Porta local do banco |
| `BACKEND_PORT` | Porta local da API principal |
| `AI_PORT` | Porta local do serviço de IA |
| `FRONTEND_PORT` | Porta local do frontend |
| `MODEL_RELEASE_REPOSITORY` | Repositório dos artefatos de IA |
| `MODEL_RELEASE_TAG` | Versão imutável dos modelos |
| `MODEL_RELEASE_MANIFEST` | Nome do manifesto de integridade |

`POSTGRES_PASSWORD` não é a senha dos usuários do sistema. Ela autentica exclusivamente a
conexão entre PostgreSQL e backend. O Compose usa as variáveis da raiz para injetar a
`DATABASE_URL` no container do backend. O valor `clinicai123` é uma credencial local
padronizada para facilitar a reprodução do protótipo; não representa uma credencial real.

## Instalação limpa

```bash
git clone https://github.com/clice/tcc-project-clinicai.git
cd tcc-project-clinicai
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Os arquivos copiados já são funcionais para a demonstração local. Antes de subir os serviços:

1. mantenha os três arquivos `.env` fora do Git;
2. baixe e valide os modelos conforme `model-release-guide.md`;
3. altere `POSTGRES_PASSWORD` e `SECRET_KEY` somente se o sistema for exposto fora da
   máquina local.

```bash
docker compose --profile models run --rm model-downloader
docker compose config
docker compose up --build -d
docker compose ps
```

## Portas e volumes

| Recurso | Porta local padrão | Volume persistente |
|---|---:|---|
| PostgreSQL | 5432 | `postgres_data` |
| Backend | 8000 | `uploads_data` |
| Serviço de IA | 8001 | `torch_cache`, `ai_storage` |
| Frontend | 3000 | — |

O código-fonte é montado nos containers para recarga automática em desenvolvimento. A
demonstração acadêmica utiliza essa configuração simples. Uma eventual hospedagem pública
deverá ser planejada separadamente, com imagens imutáveis, HTTPS, credenciais próprias e banco
não publicado diretamente.

## Dados de demonstração

O entrypoint aplica migrations e executa seeds conforme `SEED_MODE`. O modo `bootstrap`
cria os catálogos estruturais e um único Administrador Master inicial; `academic_demo`
executa esse bootstrap e acrescenta dados acadêmicos para a demonstração local.

Em um banco novo, a massa final contém 8 clínicas, 5 usuários, 8 pacientes, 7 exames e
4 análises. Os exames cobrem `processing`, `awaiting_review` com predição normal e abnormal,
`completed`, `completed_with_divergence`, `failed` e `canceled`. Os ativos versionados ficam
em `backend/demo_assets/`; origem, licença, hashes e predições estão em `manifest.json`.

As imagens de exame são copiadas para `uploads_data`. Os Grad-CAMs acadêmicos permanecem
no diretório versionado do backend e continuam sujeitos à autenticação, ao escopo de clínica
e à resolução segura de caminhos.

Os seeds são idempotentes e não devem sobrescrever usuários, registros existentes ou
customizações administrativas. Alterar o modo não remove dados já persistidos; a validação
das contagens finais deve usar um banco novo.
