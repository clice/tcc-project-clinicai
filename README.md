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
- OpenCV (pré-processamento: ROI, remoção de reflexo especular, CLAHE)
- Grad-CAM (explicabilidade)
- Scikit-learn (métricas de avaliação; meta-classificador do Ensemble Stacking)

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
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Confira principalmente `DATABASE_URL` e `SECRET_KEY` em `backend/.env`. Eles não possuem valores padrão
no código, então o backend não sobe sem essas variáveis definidas.

### 4. Subir os containers

```bash
docker compose up --build -d
```

Para usar GPU NVIDIA no serviço de IA (opcional):

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
```

### 5. Banco de dados: migrations e dados iniciais

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

### 6. Modelo de IA treinado

O serviço de IA (`ai/`) espera encontrar um modelo treinado em `ai/models/exported/model.pt`.
Esse arquivo **não vai para o Git** (é um artefato binário grande). Enquanto a distribuição
automática não estiver pronta, copie manualmente o arquivo `.pt` treinado para essa pasta antes
de subir o serviço de IA, sem ele, o container `ai` falha ao iniciar.

---

## 🔑 Credenciais de acesso (ambiente de desenvolvimento)

Os seeds criam os seguintes usuários de demonstração. **OBS:. troque essas senhas antes de qualquer
uso fora do ambiente de desenvolvimento**:

| Perfil | E-mail | Senha |
|---|---|---|
| admin_master | admin@clinicai.com | clinicai123 |
| doctor | doctor@clinicai.com | clinicai123 |
| doctor | doctor2@clinicai.com | clinicai123 |
| clinic_staff | staff@clinicai.com | clinicai123 |
| clinic_staff (inativo, para testar bloqueio) | inactive@clinicai.com | clinicai123 |

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
  (ROI, remoção de reflexo especular, CLAHE) e explicabilidade via Grad-CAM

### 🔄 Em desenvolvimento

- Fluxo de revisão médica do resultado da IA (status intermediário + tela dedicada)
- Integração automática entre backend e serviço de IA (hoje a criação da análise ainda depende
  de um payload montado externamente)
- Ensemble Stacking (EfficientNet-B4 + ResNet-50 + PVTv2-B2), conforme Viana (2026)
- Tela de resultado de IA no frontend (predição, confiança, Grad-CAM)

### 🚧 Planejados

- Dashboard clínico
- Bloqueio automático de conta por tentativas de login inválidas

---

## 🧠 Inteligência Artificial no Projeto

O diferencial do ClinicAI é a integração com visão computacional para exames endoscópicos.

### Pipeline de pré-processamento

- Extração de ROI (região de interesse)
- Remoção de reflexo especular
- Realce de contraste (CLAHE)
- Data augmentation (treino)

### Modelo

- Em produção: ResNet-50 (transfer learning)
- Em desenvolvimento: Ensemble Stacking (EfficientNet-B4 + ResNet-50 + PVTv2-B2 com
  meta-classificador de regressão logística), baseado em Viana (2026)

### Explicabilidade

- Grad-CAM

### Métricas de avaliação

- Accuracy, Precision, Recall, F1-Score, Matriz de Confusão

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
