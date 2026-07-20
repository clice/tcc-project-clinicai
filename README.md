# 📌 ClinicAI: Sistema Web Inteligente para Clínicas com IA Aplicada a Exames Endoscópicos

Projeto de Trabalho de Conclusão de Curso (TCC) voltado ao desenvolvimento de um sistema web para gestão clínica com módulo integrado de Inteligência Artificial para análise de exames gastrointestinais.

---

## 🧠 Objetivo Geral

Desenvolver um sistema web para clínicas e profissionais da saúde, integrando gestão administrativa com um módulo de análise automatizada de exames endoscópicos utilizando técnicas de Inteligência Artificial.

---

## 🎯 Objetivos Específicos

- **Desenvolver Backend:** API REST em FastAPI, com arquitetura modular.
- **Implementar Autenticação Segura:** JWT (_access_ + _refresh token_) para controle de acesso.
- **Gerenciar Estrutura Administrativa:** usuários, clínicas, pacientes, perfis e permissões.
- **Organizar Dados Clínicos:** exames endoscópicos, com fluxo de status e revisão médica.
- **Aplicar Inteligência Artificial:** classificação binária de imagens endoscópicas por
  _Ensemble Stacking_, combinando ResNet-50, EfficientNet-B4 e PVTv2-B2, com explicabilidade
  visual post-hoc por Grad-CAM.
- **Aplicar Boas Práticas de Engenharia de Software:** separação de camadas, Docker, migrations
  e organização modular.

---

## 📈 Status Atual do Projeto

- **Status geral:** Protótipo acadêmico funcional em fase de finalização
- **Fase atual:** Validação final do fluxo de exames, segurança, massa de demonstração e documentação
- **Próxima etapa:** Testes de falha e reprocessamento, consolidação da demonstração e conclusão da monografia

> Este README reflete o estado real do código. Módulos listados como "implementados" abaixo já
> funcionam de ponta a ponta; "em desenvolvimento" indica que existe implementação parcial.

---

## 👩‍💻 Autoria

| Nome | Função | Contato |
|------|--------|---------|
| Luana Batista da Cruz | Orientadora | luana.batista@ufca.edu.br |
| Clice Bezerra Brito Romão | Autora | clice.romao@aluno.ufca.edu.br |

---

## 🧪 Tecnologias Utilizadas

### 🔧 Backend

- FastAPI, SQLAlchemy, PostgreSQL, Alembic, Pydantic
- Autenticação JWT (_access_ + _refresh token_)

### 💻 Frontend

- React, CoreUI React Admin Template, Vite, React Router, Axios, Context API

### 🧠 Inteligência Artificial

- PyTorch e torchvision (ResNet-50, EfficientNet-B4 e PVTv2-B2 integrados ao serviço de inferência)
- OpenCV (pré-processamento: ROI e remoção de _Specular Highlights_)
- Grad-CAM (explicabilidade visual post-hoc)
- Scikit-learn (meta-classificador de regressão logística do _Ensemble Stacking_)

### ⚙️ Infraestrutura

- Docker / Docker Compose (GPU opcional via `docker-compose.gpu.yml`)

---

## 🏗️ Arquitetura do Sistema

```text
Frontend (React) → API REST (FastAPI) → PostgreSQL
                          ↓
                 Serviço de IA (FastAPI + PyTorch)
```

---

## 📁 Estrutura do Projeto

    tcc-project-clinicai/
    ├── backend/        -> API FastAPI e lógica de negócio
    ├── frontend/       -> Interface web React
    ├── ai/             -> Serviço de inferência + scripts de treino do modelo
    ├── docs/           -> Documentação técnica
    ├── scripts/        -> Download e geração do manifesto dos modelos
    ├── docker-compose.yml
    ├── docker-compose.gpu.yml  -> override opcional para GPU NVIDIA
    └── README.md

---

## ⚙️ Como Executar o Projeto

### 1. Pré-requisitos

- Docker e Docker Compose instalados
- (Opcional) NVIDIA Container Toolkit, só se for usar GPU no serviço de IA

### 2. Clonar o repositório

```bash
git clone https://github.com/clice/tcc-project-clinicai.git
cd tcc-project-clinicai
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Confira principalmente `DATABASE_URL` e `SECRET_KEY` em `backend/.env`. Eles não possuem valores padrão
no código, então o backend não sobe sem essas variáveis definidas.

O `.env` da raiz define o repositório, a tag da release e o nome do manifesto usados para
baixar os modelos. A tag padrão é `models-v0.1.1`.

### 4. Baixar os modelos treinados

Os pesos e o meta-classificador não são armazenados diretamente no Git. Antes de subir o
sistema pela primeira vez, baixe os artefatos da GitHub Release configurada em `.env`:

```bash
docker compose --profile models run --rm model-downloader
```

O comando baixa e verifica os seguintes arquivos em
`ai/models/exported/gastrointestinal/`:

- `resnet50.pt`;
- `efficientnet_b4.pt`;
- `pvt_v2_b2.pt`;
- `meta_classificador.joblib`;
- `manifesto_modelos.json`.

O download valida o tamanho e o hash SHA-256 de cada artefato. Arquivos já existentes e
válidos são preservados; arquivos incompletos ou com hash divergente não são instalados.

### 5. Validar dependências e configuração

Antes do primeiro build ou após alterar arquivos de dependências:

```bash
python3 scripts/check_dependency_locks.py
docker compose config --quiet
```

### 6. Subir os containers

```bash
docker compose up --build -d
```

Para usar GPU NVIDIA no serviço de IA (opcional):

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
```

### 7. Banco de dados: migrations e dados iniciais

**Isso acontece automaticamente.** O container do backend, ao subir, executa nesta ordem
(veja `backend/entrypoint.sh`):

1. aguarda o PostgreSQL aceitar conexões;
2. aplica as migrations pendentes (`alembic upgrade head`);
3. executa os seeds no modo definido por `SEED_MODE`.

Os modos são separados:

| `SEED_MODE` | Resultado |
|---|---|
| `bootstrap` | cria statuses, roles, permissions, a matriz inicial de role-permissions e um único Administrador Master |
| `academic_demo` | executa o bootstrap e acrescenta somente clínicas, profissionais, pacientes, exames e análises fictícios |

O padrão seguro do backend é `bootstrap`. O `backend/.env.example` usa
`academic_demo` porque o Compose principal é destinado ao desenvolvimento acadêmico local.
Nunca habilite esse modo em um banco com dados reais.

No modo `bootstrap`, o primeiro acesso utiliza as variáveis
`BOOTSTRAP_ADMIN_NAME`, `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_CPF` e
`BOOTSTRAP_ADMIN_PASSWORD`. Os valores do `.env.example` são destinados somente
ao ambiente acadêmico e devem ser alterados em qualquer outro ambiente.

Os seeds são idempotentes e não apagam registros existentes. Alterar
`SEED_MODE` de `academic_demo` para `bootstrap` não remove dados de demonstração
já persistidos; uma validação realmente limpa deve usar um banco novo.

Comandos manuais equivalentes:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.modules.seeds --mode bootstrap
docker compose exec backend python -m app.modules.seeds --mode academic_demo
```

Os seeds não atualizam registros existentes e não reconciliam customizações administrativas.
As fases de bootstrap e demonstração possuem transações separadas para impedir dados parciais.

A integridade das migrations, dos seeds e dos contratos do banco é protegida pela suíte
automatizada do backend. Para executá-la:

```bash
docker compose run --rm --no-deps --entrypoint python backend -m pytest -q
```

Para validar todo o Bloco 1 em uma única execução — migration, backend,
contratos do frontend, navegação e build — use o script correspondente ao
seu sistema operacional a partir da raiz do projeto:

```bash
# Linux, macOS, Git Bash ou WSL
./scripts/test-bloco-1.sh
```

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\scripts\test-bloco-1.ps1
```

Os scripts iniciam apenas o banco de dados e criam contêineres temporários
para os testes. Ao final, exibem claramente a primeira etapa que falhar ou a
mensagem de sucesso do bloco completo.

---

## 🔑 Credenciais iniciais e acadêmicas

O Administrador Master é criado pelo modo `bootstrap` e também é reutilizado pelo
`academic_demo`. No arquivo `backend/.env.example`, os valores acadêmicos locais são:

| Perfil | E-mail padrão | Senha padrão |
|---|---|---|
| Administrador _Master_ | valor de `BOOTSTRAP_ADMIN_EMAIL` (`admin@clinicai.com`) | valor de `BOOTSTRAP_ADMIN_PASSWORD` (`clinicai123`) |

O modo `academic_demo` acrescenta as contas fictícias abaixo:

| Perfil | E-mail | Senha |
|---|---|---|
| Médico — Clínica Primária | doctor@clinicai.com | clinicai123 |
| Gestor — Clínica Primária | clinic_manager@clinicai.com | clinicai123 |
| Médico — Hospital Regional Cariri | doctor.cariri@clinicai.com | clinicai123 |
| Gestor — Hospital Regional Cariri | manager.cariri@clinicai.com | clinicai123 |
| Médico — Centro Endoscópico Cariri | doctor.endoscopia@clinicai.com | clinicai123 |
| Gestor — Centro Endoscópico Cariri | manager@clinicai.com | clinicai123 |

Essas credenciais existem apenas para reprodutibilidade acadêmica e não devem
ser reutilizadas em ambiente real. O seed não redefine a senha nem os dados de
um usuário que já exista.

O `academic_demo` consolidado cria três clínicas, seis contas de acesso,
30 pacientes fictícios e 90 exames, sendo 30 por clínica. A massa contempla
`pending`, `awaiting_review`, `completed`, `completed_with_divergence`, `failed`
e `canceled`, além de 72 análises concluídas pelo `ensemble_stacking` versão
`0.1.1`, todas com mapas Grad-CAM.

As 90 imagens acadêmicas — 45 normais e 45 anormais segundo seus rótulos de
origem — têm procedência, licença, hashes, vínculos e resultados registrados em
`backend/demo_assets/manifest.json`. Esse conjunto serve exclusivamente à
demonstração acadêmica e não representa uma avaliação formal ou validação
clínica do modelo.

---

## 🌐 Acesso Local

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Documentação Backend API | http://localhost:8000/docs |
| Documentação IA API | http://localhost:8001/docs |

---

## 🧩 Módulos do Sistema

### ✔ Implementados

- Autenticação (JWT com access + refresh token, invalidação de sessão)
- Usuários, Clínicas, Pacientes
- Perfis (Roles) e Permissões, com controle de acesso por escopo de clínica
- Status (motor de fluxo de estados por entidade)
- Logs de Auditoria
- Exames: upload, download, análise por IA, revisão médica, cancelamento e restauração
- Integração automática entre backend e serviço de IA
- Classificação binária pelo _Ensemble Stacking_ com ResNet-50, EfficientNet-B4 e PVTv2-B2
- Revisão médica com confirmação ou divergência e histórico auditável
- Disponibilização autenticada do mapa Grad-CAM
- Massa `academic_demo` reproduzível com três clínicas, 30 pacientes, 90 exames e 72 análises com Grad-CAM

### 🔄 Em validação e finalização

- Verificação manual do percurso completo do médico pela interface
- Fechamento da documentação técnica e da monografia

### 🚧 Planejados

- Dashboard clínico
- Bloqueio automático de conta por tentativas de login inválidas

---

## 🧠 Inteligência Artificial no Projeto

O diferencial do ClinicAI é a integração com visão computacional para exames endoscópicos.

### Pipeline de pré-processamento

- Extração de ROI (_Region of Interest_)
- Remoção de _Specular Highlights_
- _Data Augmentation_ (treino)

### Modelo

- _Ensemble Stacking_ operacional, combinando ResNet-50, EfficientNet-B4 e PVTv2-B2
- Meta-classificador de regressão logística, baseado na reprodução operacional adaptada
  do método de Viana
- Artefatos operacionais distribuídos pela GitHub Release `models-v0.1.1`
- Protocolo de treinamento dos artefatos: `viana_codigo_kfold3_roi_sh_da`
- Fold operacional 3, selecionado como execução representativa por proximidade do
  resultado à média agregada dos três folds, sem alegação de superioridade estatística

### Explicabilidade

- Grad-CAM

### Métricas de avaliação

- Accuracy, Precision, Recall, F1-Score, Matriz de Confusão

---

## 📦 Publicação dos Modelos no GitHub Releases

Esta seção é destinada à manutenção dos artefatos de IA. Quem deseja apenas executar o sistema
deve seguir a seção **Como Executar o Projeto**.

### 1. Preparar os artefatos

Os quatro arquivos finais devem estar em `ai/models/exported/gastrointestinal/` com estes nomes:

```text
resnet50.pt
efficientnet_b4.pt
pvt_v2_b2.pt
meta_classificador.joblib
```

A ordem das meta-features do meta-classificador deve ser ResNet-50, EfficientNet-B4 e PVTv2-B2,
a mesma definida em `ai/app/inference/domains/gastrointestinal.py`.

### 2. Gerar o manifesto

Na raiz do projeto, execute:

```bash
python scripts/generate_model_manifest.py \
  --release-tag models-v0.1.1 \
  --model-version 0.1.1
```

O comando gera `manifesto_modelos.json` com o tamanho e o hash SHA-256 de cada artefato. Os
modelos e o manifesto são ignorados pelo Git e devem ser anexados manualmente à release.

### 3. Criar a release

No GitHub, abra **Releases** e selecione **Draft a new release**. Use:

- tag: `models-v0.1.1`;
- título: `Modelos ClinicAI v0.1.1`;
- opção **This is a pre-release**, enquanto o sistema estiver em desenvolvimento.

Anexe exatamente os cinco arquivos:

```text
resnet50.pt
efficientnet_b4.pt
pvt_v2_b2.pt
meta_classificador.joblib
manifesto_modelos.json
```

Salve primeiro como rascunho, confira os nomes dos arquivos e somente depois publique.

### 4. Versionar atualizações futuras

A tag configurada em `.env` é fixa. Alterações posteriores no frontend, backend, README ou RBAC
não modificam os artefatos da release `models-v0.1.1`.

Se algum peso, meta-classificador, classe ou etapa de pré-processamento mudar, publique uma nova
release, por exemplo `models-v0.1.2` ou `models-v0.2.0`, e atualize `MODEL_RELEASE_TAG` em
`.env.example`. Não substitua os arquivos de uma versão já publicada, pois as releases antigas
devem continuar disponíveis para reprodutibilidade. A release `models-v0.1.0`
permanece preservada como versão histórica anterior ao conjunto operacional do fold 3.

O download atual usa assets públicos. Repositórios privados exigem um mecanismo de autenticação
específico; tokens não devem ser armazenados no Compose, no README ou em arquivos versionados.

---

## 📚 Contribuição Acadêmica

O projeto contribui com:

- Aplicação de Engenharia de Software em sistemas reais
- Integração entre sistemas web e Inteligência Artificial
- Estruturação de dados clínicos com fluxo de revisão médica
- Base para pesquisa em diagnóstico assistido por IA (CADx) em endoscopia gastrointestinal

---

## Bootstrap e evolução da matriz RBAC

No modo `bootstrap`, o executor `python -m app.modules.seeds`, chamado pelo
entrypoint do backend, cria o bootstrap estrutural e garante um único
Administrador Master inicial. O campo
`roles.permissions_initialized`
distingue uma role nunca inicializada de uma role configurada sem permissões.
Depois do primeiro bootstrap, reinícios não alteram a matriz e as edições
administrativas permanecem como fonte da verdade.

A baseline `0001clinicai` já contém o marcador de bootstrap e o catálogo
estrutural atual. Na matriz padrão, `clinic_manager` possui acesso operacional
à própria clínica, sem receber `exams:read` ou `ai_analysis:read`. Mudanças
oficiais futuras em bancos existentes devem ser implementadas por novas
migrations de dados do Alembic.

Somente quando houver intenção de descartar customizações e restaurar toda a
matriz padrão, execute manualmente:

```bash
docker compose exec backend python -m app.modules.role_permissions.reconcile \
  --confirm RECONCILE_RBAC
```

O comando registra quantos vínculos foram adicionados e removidos por role e
não é executado automaticamente pelo entrypoint.

---

## 📄 Observações

Este projeto está em desenvolvimento contínuo como parte do Trabalho de Conclusão de Curso e
será evoluído progressivamente até sua versão final. Ainda não foi validado em ambiente clínico
real. OBS:. é um protótipo funcional para fins acadêmicos.

---

## 📄 Licença

Projeto acadêmico desenvolvido para fins educacionais.
