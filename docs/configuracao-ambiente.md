# Configuração de Ambiente

Este documento registra a configuração reproduzível do ambiente local do ClinicAI.

O `docker-compose.yml` foi preparado para desenvolvimento e demonstração acadêmica. As portas
são publicadas no host pelas associações padrão do Docker Compose. Portanto, a configuração não
deve ser tratada como pronta para hospedagem pública ou uso clínico.

## Arquivos de configuração

| Arquivo | Consumidor | Versionado? |
|---|---|---|
| `.env` | serviço auxiliar de distribuição dos modelos | Não |
| `.env.example` | exemplo da configuração dos modelos | Sim |
| `backend/.env` | backend FastAPI | Não |
| `backend/.env.example` | exemplo da configuração do backend | Sim |
| `frontend/.env` | frontend Vite | Não |
| `frontend/.env.example` | exemplo da configuração do frontend | Sim |

Crie os arquivos locais:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Arquivos `.env` locais não devem ser versionados.

## Variáveis da raiz

O `.env` da raiz controla a distribuição dos artefatos de IA:

| Variável | Finalidade |
|---|---|
| `MODEL_RELEASE_REPOSITORY` | repositório que hospeda os anexos da release |
| `MODEL_RELEASE_TAG` | tag imutável dos modelos |
| `MODEL_RELEASE_MANIFEST` | nome do manifesto de integridade |

A configuração acadêmica atual utiliza:

```dotenv
MODEL_RELEASE_REPOSITORY=clice/tcc-project-clinicai
MODEL_RELEASE_TAG=models-v0.1.2
MODEL_RELEASE_MANIFEST=manifesto_modelos.json
```

O serviço `model-downloader` também possui esses valores como *fallback* no
`docker-compose.yml`.

## Variáveis do backend

O arquivo `backend/.env` reúne:

- identificação do ambiente;
- host e porta da API;
- modo de seed;
- credenciais do Administrador Master inicial;
- conexão com PostgreSQL;
- segredo e tempos de expiração dos tokens JWT;
- origens CORS;
- raiz do armazenamento operacional;
- limites de tamanho e dimensões das imagens.

`DATABASE_URL` e `SECRET_KEY` são obrigatórias. Os valores de
`backend/.env.example` servem apenas à reprodução acadêmica local e devem ser substituídos em
qualquer ambiente exposto.

O modo seguro padrão é:

```dotenv
SEED_MODE=bootstrap
```

Para carregar a massa acadêmica em um banco novo:

```dotenv
SEED_MODE=academic_demo
```

Nunca use `academic_demo` em um banco com dados reais.

## Variáveis do frontend

O arquivo `frontend/.env` define:

- nome e ambiente da aplicação;
- host e porta do Vite;
- endereço da API principal;
- chaves usadas para armazenar a sessão no navegador;
- tema e idioma padrão.

A URL local padrão do backend é:

```dotenv
VITE_API_URL=http://localhost:8000
```

Variáveis com prefixo `VITE_` são incorporadas ao código entregue ao navegador. Não armazene
segredos nelas.

## Instalação limpa

```bash
git clone https://github.com/clice/tcc-project-clinicai.git
cd tcc-project-clinicai

cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

python3 scripts/check_dependency_locks.py
docker compose config --quiet
docker compose --profile models run --rm model-downloader
docker compose up --build -d
docker compose ps
```

## Portas e volumes

| Recurso | Porta local padrão | Armazenamento ou montagem |
|---|---:|---|
| PostgreSQL | 5432 | volume `postgres_data` |
| Backend | 8000 | `./backend:/app` e `./data:/clinicai-data` |
| Serviço de IA | 8001 | `./ai:/app`, modelos locais e volume `torch_cache` |
| Frontend | 3000 | `./frontend:/app` e volume interno de `node_modules` |

Por padrão, associações como `3000:3000` e `8000:8000` podem escutar nas interfaces do host.
Para restringir uma execução estritamente local, ajuste as portas para o formato
`127.0.0.1:PORTA:PORTA`, utilize regras de firewall ou uma configuração Compose específica.

## GPU opcional

O serviço de IA utiliza CPU quando CUDA não está disponível. Para habilitar GPU NVIDIA:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.gpu.yml \
  up --build -d
```

Esse modo exige NVIDIA Container Toolkit corretamente instalado.

## Inicialização do banco

Ao iniciar, o backend:

1. aguarda o PostgreSQL aceitar conexões;
2. aplica `alembic upgrade head`;
3. executa os seeds no modo definido por `SEED_MODE`;
4. inicia a API.

O modo `bootstrap` cria os catálogos estruturais, a matriz inicial de permissões e um
Administrador Master. O modo `academic_demo` acrescenta a massa acadêmica determinística.

## Dados de demonstração

Em um banco novo, a massa consolidada possui:

- quatro clínicas, sendo três ativas e uma inativa;
- 13 usuários no total, incluindo o Administrador Master e contas inativas de teste;
- 30 pacientes fictícios;
- 90 exames, sendo 30 por clínica ativa;
- 72 análises concluídas pelo `ensemble_stacking` versão `0.1.2`;
- 72 mapas Grad-CAM;
- 464 registros de auditoria.

Os exames cobrem os estados `pending`, `awaiting_review`, `completed`,
`completed_with_divergence`, `failed` e `canceled`.

As imagens e os mapas são instalados em:

```text
data/exams/<clinic_id>/<patient_id>/<exam_id>/original/
data/exams/<clinic_id>/<patient_id>/<exam_id>/attribution/
```

A fonte versionada da massa permanece em `backend/demo_assets/`.

## Validação

```bash
python3 scripts/check_dependency_locks.py
docker compose config --quiet

docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m pytest -q

docker compose run --rm --no-deps frontend npm run lint
docker compose run --rm --no-deps frontend npm run build

docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  ai -m unittest discover -s tests -p 'test_*.py' -v
```

## Limitações

Essa configuração é destinada ao desenvolvimento e à demonstração local. Uma eventual
hospedagem pública exigiria planejamento separado, incluindo HTTPS, gestão segura de segredos,
banco não publicado diretamente, imagens imutáveis, política de backups, observabilidade,
endurecimento dos containers e revisão profissional de segurança.
