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
- **Aplicar Inteligência Artificial:** classificação de imagens endoscópicas (atualmente ResNet-50,
  com _Ensemble Stacking_ em desenvolvimento), com explicabilidade via Grad-CAM.
- **Aplicar Boas Práticas de Engenharia de Software:** separação de camadas, Docker, migrations
  e organização modular.

---

## 📈 Status Atual do Projeto

- **Status geral:** Em desenvolvimento — protótipo funcional
- **Fase atual:** Correção de bugs e fechamento do fluxo de análise de exames (IA + revisão médica)
- **Próxima etapa:** _Ensemble Stacking_ (EfficientNet-B4 + ResNet-50 + PVTv2-B2) e telas de resultado de IA

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

- PyTorch, torchvision (ResNet-50 em produção; EfficientNet-B4 e PVTv2-B2 em desenvolvimento)
- OpenCV (pré-processamento: ROI, remoção de _Specular Highlights_)
- Grad-CAM (explicabilidade)
- Scikit-learn (métricas de avaliação; meta-classificador do _Ensemble Stacking_)

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
baixar os modelos. A tag padrão é `models-v0.1.0`.

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

### 5. Subir os containers

```bash
docker compose up --build -d
```

Para usar GPU NVIDIA no serviço de IA (opcional):

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
```

### 6. Banco de dados: migrations e dados iniciais

**Isso acontece automaticamente.** O container do backend, ao subir, executa nesta ordem
(veja `backend/entrypoint.sh`):

1. Aguarda o PostgreSQL aceitar conexões;
2. Aplica as migrations pendentes (`alembic upgrade head`);
3. Roda os seeds do sistema (`python -m app.modules.seeds`): cria status, perfis, permissões
   e usuários iniciais, caso ainda não existam.

Você não precisa rodar nenhum comando manual no primeiro `docker compose up`. Se precisar
repetir esse processo manualmente (ex: depurar um problema), pode rodar:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.modules.seeds
```

Os seeds são idempotentes, ou seja, rodar de novo não duplica dados.

---

## 🔑 Credenciais de Acesso

Os seeds criam os seguintes usuários de demonstração. **OBS:. troque essas senhas antes de qualquer
uso fora do ambiente de desenvolvimento**:

| Perfil | E-mail | Senha |
|---|---|---|
| Administrador _Master_ | admin@clinicai.com | clinicai123 |
| Médico | doctor@clinicai.com | clinicai123 |
| Médico | doctor2@clinicai.com | clinicai123 |
| Funcionário da Clínica | staff@clinicai.com | clinicai123 |
| Funcionário da Clínica (inativo, para testar bloqueio) | inactive@clinicai.com | clinicai123 |

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
- Exames (upload, download, cancelamento, restauração)
- Módulo de IA: classificação de imagens endoscópicas com ResNet-50, pré-processamento
  (ROI, remoção de _Specular Highlights_) e explicabilidade via Grad-CAM

### 🔄 Em desenvolvimento

- Fluxo de revisão médica do resultado da IA (status intermediário + tela dedicada)
- Integração automática entre backend e serviço de IA (hoje a criação da análise ainda depende
  de um payload montado externamente)
- _Ensemble Stacking_ (EfficientNet-B4 + ResNet-50 + PVTv2-B2), conforme Viana (2026)
- Tela de resultado de IA no frontend (predição, confiança, Grad-CAM)

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

- Em produção: ResNet-50 (_Transfer Learning_)
- Em desenvolvimento: _Ensemble Stacking_ (EfficientNet-B4 + ResNet-50 + PVTv2-B2 com
  meta-classificador de _Logistic Regression_), baseado em Viana (2026)

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
  --release-tag models-v0.1.0 \
  --model-version 0.1.0
```

O comando gera `manifesto_modelos.json` com o tamanho e o hash SHA-256 de cada artefato. Os
modelos e o manifesto são ignorados pelo Git e devem ser anexados manualmente à release.

### 3. Criar a release

No GitHub, abra **Releases** e selecione **Draft a new release**. Use:

- tag: `models-v0.1.0`;
- título: `Modelos ClinicAI v0.1.0`;
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
não modificam os artefatos da release `models-v0.1.0`.

Se algum peso, meta-classificador, classe ou etapa de pré-processamento mudar, publique uma nova
release, por exemplo `models-v0.1.1` ou `models-v0.2.0`, e atualize `MODEL_RELEASE_TAG` em
`.env.example`. Não substitua os arquivos de uma versão já publicada, pois as releases antigas
devem continuar disponíveis para reprodutibilidade.

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

O executor `python -m app.modules.seeds`, chamado pelo entrypoint do backend,
faz apenas o bootstrap inicial. O campo `roles.permissions_initialized`
distingue uma role nunca inicializada de uma role configurada sem permissões.
Depois do primeiro bootstrap, reinícios não alteram a matriz e as edições
administrativas permanecem como fonte da verdade.

Mudanças oficiais de permissões em bancos existentes são implementadas por
migrations de dados do Alembic. A migration `b7c1d4e2f901` introduz o marcador
de bootstrap e revoga os privilégios legados `exams:read` e
`ai_analysis:read` de `clinic_staff`.

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