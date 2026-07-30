# 📌 Protótipo de Sistema Web para Gerenciamento Clínico e Apoio à Análise Automatizada de Exames Gastrointestinais

## 🧠 Objetivo Geral

Desenvolver o ClinicAI, um protótipo de sistema web para gerenciamento clínico, integrando um
método de classificação binária automatizada de imagens de exames gastrointestinais em normais
ou anormais como recurso de apoio à análise realizada por profissionais médicos.

---

## 🎯 Objetivos Específicos

- Realizar um levantamento bibliográfico para compreender o problema investigado e identificar
  lacunas relacionadas ao uso de métodos computacionais na análise de exames gastrointestinais;
- Desenvolver uma plataforma web para gerenciamento de clínicas, usuários, médicos, pacientes e
  exames, incluindo autenticação e controle de acesso baseado em papéis;
- Projetar uma arquitetura modular para a comunicação entre o *frontend*, o *backend*, a camada
  de persistência de dados e o módulo de Inteligência Artificial;
- Reproduzir, em ambiente experimental, o método de *Ensemble Stacking* proposto por Viana
  (2026), gerando os artefatos necessários à composição e à execução do modelo preditivo;
- Integrar o modelo preditivo ao sistema, incorporando a classificação automatizada das imagens
  e a disponibilização de mapas de ativação Grad-CAM;
- Verificar tecnicamente o funcionamento dos módulos e dos principais fluxos do protótipo por
  meio de testes automatizados e funcionais.

---

## 📈 Status do Projeto

O ClinicAI está concluído como protótipo acadêmico funcional dentro do escopo definido para o
Trabalho de Conclusão de Curso. Os módulos descritos neste documento foram integrados e
verificados tecnicamente em ambiente local de demonstração.

Essa conclusão não representa implantação em produção, validação clínica, certificação de
segurança ou avaliação com profissionais e pacientes em cenário real.

---

## 👩‍💻 Autoria

| Nome | Função | Contato |
|---|---|---|
| Luana Batista da Cruz | Orientadora | luana.batista@ufca.edu.br |
| Clice Bezerra Brito Romão | Autora | clice.romao@aluno.ufca.edu.br |

---

## 🧪 Tecnologias Utilizadas

### 🔧 Backend

- **FastAPI**: *framework* Python para construção da API REST, com geração automática de
  documentação interativa;
- **Pydantic**: validação e serialização de dados;
- **SQLAlchemy**: ORM para acesso ao banco de dados relacional;
- **Alembic**: versionamento e controle histórico do esquema do banco de dados;
- **Python-JOSE**: emissão e verificação de *tokens* JWT (*access token* e *refresh token*);
- **HTTPX**: comunicação assíncrona entre o *backend* e o serviço de IA;
- **ReportLab**: geração do relatório do exame em PDF;
- **PostgreSQL**: sistema gerenciador de banco de dados relacional.

### 💻 Frontend

- **React** (v19): biblioteca para construção da interface, organizada em componentes
  reutilizáveis;
- **Vite**: ferramenta de *build* e servidor de desenvolvimento;
- **CoreUI React Admin Template**: componentes visuais padronizados, como menus, tabelas e
  formulários;
- **React Router**: navegação entre telas sem recarregamento da página;
- **Axios**: requisições HTTP ao *backend*;
- **Redux** (com React Redux): gerenciamento de estado global da interface, utilizado
  principalmente para controlar a exibição da barra lateral;
- **Context API**: gerenciamento de estados específicos, utilizado nos contextos de
  autenticação (`AuthContext`) e de notificações (`FeedbackContext`);
- **Chart.js** (via `@coreui/react-chartjs`): renderização dos gráficos do *dashboard*.

### 🧠 Inteligência Artificial

- **PyTorch** e **torchvision**: construção, treinamento e execução das arquiteturas ResNet-50,
  EfficientNet-B4 e PVTv2-B2;
- **timm**: construção da arquitetura *Vision Transformer* PVTv2-B2;
- **Scikit-learn** e **joblib**: treinamento, serialização e carregamento do
  meta-classificador de Regressão Logística do *Ensemble Stacking*;
- **OpenCV**, **Pillow** e **NumPy**: pré-processamento das imagens, incluindo extração de ROI e
  remoção de *Specular Highlights*;
- **pytorch-grad-cam**: geração dos mapas de ativação Grad-CAM combinados do *ensemble*.

### ⚙️ Infraestrutura

- **Docker** e **Docker Compose**: conteinerização e orquestração do *frontend*, do *backend*, do
  banco de dados e do módulo de IA, com suporte opcional a GPU por meio de
  `docker-compose.gpu.yml`.

### 🛠️ Ferramentas de Apoio ao Desenvolvimento

O desenvolvimento contou com o apoio de **Claude Code** e **Codex** em atividades de
implementação, revisão, depuração e elaboração de testes. As decisões de arquitetura, a
validação dos resultados e a responsabilidade pelo conteúdo permaneceram sob responsabilidade
da autora.

---

## 🏗️ Arquitetura do Sistema

O sistema é estruturado em quatro componentes principais, *frontend*, *backend*, persistência
de dados e módulo de IA, executados em *containers* Docker e orquestrados pelo Docker Compose:

```text
┌─────────────────────────────────────────────────────────┐
│                Docker Compose - ClinicAI                │
│                                                         │
│   Frontend (React)                                      │
│         │  REST API (Axios)                             │
│         ▼                                               │
│   Backend (FastAPI)                                     │
│      │              │                                   │
│      │ SQL          │ HTTP (HTTPX)                      │
│      ▼              ▼                                   │
│   Persistência    Módulo de IA (FastAPI + PyTorch)      │
│   (PostgreSQL)         ▲                                │
│                        │ artefatos compartilhados       │
│                 model-downloader (auxiliar)             │
└─────────────────────────────────────────────────────────┘
                        │ download da release
                        ▼
                 GitHub Releases
```

Essa organização separa as responsabilidades entre os componentes, facilitando a manutenção e
a evolução independente de cada camada.

O `model-downloader` é um serviço auxiliar executado sob demanda por meio do perfil `models`.
Ele não permanece ativo durante a utilização normal do sistema e tem como função baixar,
validar e instalar os artefatos versionados da GitHub Release no diretório compartilhado com o
serviço de IA.

---

## 📁 Estrutura do Projeto

```text
tcc-project-clinicai/
├── backend/        -> API FastAPI, regras de negócio e modelagem do banco
├── frontend/       -> Interface web React
├── ai/             -> Serviço de inferência e scripts de treinamento
├── data/           -> Persistência local de exames e mapas Grad-CAM do protótipo
├── docs/           -> Documentação técnica complementar
├── scripts/        -> Download e geração do manifesto dos modelos
├── docker-compose.yml
├── docker-compose.gpu.yml  -> configuração opcional para GPU NVIDIA
└── README.md
```

---

## ⚙️ Como Executar o Projeto

### 1. Pré-requisitos

- Docker e Docker Compose instalados;
- NVIDIA Container Toolkit, apenas para execução opcional do serviço de IA com GPU NVIDIA.

### 2. Clonar o repositório

```bash
git clone https://github.com/clice/tcc-project-clinicai.git
cd tcc-project-clinicai
```

### 3. Configurar as variáveis de ambiente

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Confira principalmente `DATABASE_URL` e `SECRET_KEY` em `backend/.env`. Essas variáveis não
possuem valores padrão no código, e o *backend* não inicia sem que estejam definidas.

O arquivo `.env` da raiz define o repositório, a tag da *release* e o nome do manifesto usados
para baixar os modelos.

### 4. Baixar os modelos treinados

Os pesos e o meta-classificador não são armazenados no Git. Antes de iniciar o sistema pela
primeira vez, baixe os artefatos da GitHub Release configurada no arquivo `.env`:

```bash
docker compose --profile models run --rm model-downloader
```

O comando baixa e valida o tamanho e o *hash* SHA-256 dos seguintes arquivos, instalando-os em
`ai/models/exported/gastrointestinal/`:

- `resnet50.pt`;
- `efficientnet_b4.pt`;
- `pvt_v2_b2.pt`;
- `meta_classificador.joblib`;
- `manifesto_modelos.json`.

Arquivos já existentes e válidos são preservados. Arquivos incompletos ou com *hash*
divergente não são instalados.

### 5. Validar dependências e configuração

Antes do primeiro *build* ou após alterar arquivos de dependências, execute:

```bash
python3 scripts/check_dependency_locks.py
docker compose config --quiet
```

### 6. Subir os containers

```bash
docker compose up --build -d
```

Para usar GPU NVIDIA no serviço de IA:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
```

### 7. Banco de dados, migrations e dados iniciais

O processo ocorre automaticamente quando o *container* do *backend* é iniciado. O arquivo
`backend/entrypoint.sh` executa, nesta ordem:

1. aguarda o PostgreSQL aceitar conexões;
2. aplica as *migrations* pendentes com `alembic upgrade head`;
3. executa os *seeds* no modo definido pela variável `SEED_MODE`.

| `SEED_MODE` | Resultado | Comando manual equivalente |
|---|---|---|
| `bootstrap` (padrão) | cria *statuses*, papéis, permissões, a matriz inicial de papel-permissão e um único Administrador Master | `docker compose exec backend python -m app.modules.seeds --mode bootstrap` |
| `academic_demo` | executa o *bootstrap* e acrescenta clínicas, profissionais, pacientes, exames e análises fictícios | `docker compose exec backend python -m app.modules.seeds --mode academic_demo` |

Para carregar a massa demonstrativa em um banco novo, defina
`SEED_MODE=academic_demo` em `backend/.env` antes de iniciar os *containers*.

> **Atenção:** o modo `academic_demo` é destinado exclusivamente ao ambiente acadêmico e não
> deve ser habilitado em um banco com dados reais.

Os *seeds* são idempotentes. O *bootstrap* preserva as customizações administrativas feitas
após a inicialização da matriz de permissões. O modo `academic_demo` reconcilia apenas os
registros reservados da massa demonstrativa com o manifesto atual, inclusive removendo análises
obsoletas vinculadas a exames acadêmicos quando necessário. Ele não apaga registros externos à
massa. Alterar o modo de `academic_demo` para `bootstrap` não remove os dados demonstrativos já
persistidos.

---

## 🔑 Credenciais Iniciais e Acadêmicas

O Administrador Master é criado pelo modo `bootstrap` e também é reutilizado pelo modo
`academic_demo`. No arquivo `backend/.env.example`, os valores acadêmicos locais são:

| Perfil | E-mail padrão | Senha padrão |
|---|---|---|
| Administrador *Master* | `admin@clinicai.com` | `clinicai123` |

O modo `academic_demo` acrescenta as contas fictícias abaixo. Todas utilizam a senha
`clinicai123`.

| Perfil | Nome | E-mail | Clínica |
|---|---|---|---|
| Médico | Dr. João Silva | `dr.joao@clinicai.com` | ClinicAI Endoscopia Especializada |
| Médico | Dr. Lucas Andrade | `dr.lucas@clinicai.com` | ClinicAI Endoscopia Especializada |
| Gestor | Gestor ClinicAI Endoscopia Especializada | `gestor.clinicai@clinicai.com` | ClinicAI Endoscopia Especializada |
| Médico | Dr. Marcos Lima | `dr.marcos@hospitalcariri.com` | Hospital Regional do Cariri |
| Gestor | Gestor Hospital Cariri | `gestor.hospital@hospitalcariri.com` | Hospital Regional do Cariri |
| Médico | Dra. Helena Costa | `dra.helena@cariri.com` | Centro Endoscópico Cariri |
| Gestor | Gestão Centro Endoscópico | `gestor.centro@cariri.com` | Centro Endoscópico Cariri |

Também existem contas inativas, utilizadas para validar o bloqueio de autenticação de usuários
e clínicas inativos:

| Perfil | Nome | E-mail | Situação |
|---|---|---|---|
| Médico | Dr. Renato Moura | `dr.renato@clinicai.com` | Usuário inativo vinculado à clínica inativa |
| Médica | Dra. Paula Freire | `dra.paula@clinicai.com` | Usuária inativa |
| Gestor | Gestor Inativo Hospital Cariri | `gestor.inativo@hospitalcariri.com` | Usuário inativo |
| Gestor | Gestor Inativo Centro Endoscópico | `gestor.inativo@cariri.com` | Usuário inativo |
| Administrador *Master* | Administrador Master Inativo | `admin.inativo@clinicai.com` | Usuário inativo |

Essas credenciais existem apenas para reprodutibilidade acadêmica e não devem ser reutilizadas
em ambiente real. Para contas acadêmicas já existentes, o *seed* preserva a senha armazenada,
mas reconcilia os campos reservados da demonstração, como nome, e-mail, papel, situação e
vínculo com a clínica.

A massa `academic_demo` reúne quatro clínicas (três ativas e uma inativa de teste), 13
usuários no total, 30 pacientes fictícios e 90 exames, sendo 30 por clínica ativa. A massa
contempla os estados `pending`, `awaiting_review`, `completed`,
`completed_with_divergence`, `failed` e `canceled`, além de 72 análises concluídas pelo
`ensemble_stacking` versão `0.1.2`, todas com mapas Grad-CAM, 50 exames revisados e 464 eventos
de auditoria.

As 90 imagens acadêmicas (45 normais e 45 anormais segundo seus rótulos de origem da base de imagens Kvasir V1) têm
procedência, licença, *hashes*, vínculos e resultados registrados em
`backend/demo_assets/manifest.json`. Esse conjunto serve exclusivamente à demonstração
acadêmica e não representa avaliação formal nem validação clínica do modelo.

---

## ✅ Testes

| Camada | Comando |
|---|---|
| Backend | `docker compose run --rm --no-deps --entrypoint python backend -m pytest -q` |
| Módulo de IA | `docker compose run --rm --no-deps --entrypoint python -w /app ai -m unittest discover -s tests -p 'test_*.py' -v` |
| Frontend (qualidade estática) | `docker compose run --rm --no-deps frontend npm run lint` |
| Frontend (build de produção) | `docker compose run --rm --no-deps frontend npm run build` |

A suíte automatizada do *backend* contempla testes unitários, de integração e de contrato,
incluindo isolamento de dados entre clínicas, autorização por perfil, exclusividade da revisão
médica, integridade dos registros de auditoria e comportamento da máquina de estados dos
exames.

Na validação técnica realizada antes da consolidação desta versão, foram registrados 273 testes
aprovados e 2 testes ignorados conforme a configuração existente. Essa contagem pode aumentar
com a evolução do projeto.

---

## 🌐 Acesso Local

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Documentação da API do Backend | http://localhost:8000/docs |
| Documentação da API de IA | http://localhost:8001/docs |

---

## 🧩 Módulos do Sistema

### ✔ Escopo concluído

- Autenticação com JWT, utilizando *access token*, *refresh token* e invalidação de sessão;
- Gerenciamento de usuários, clínicas e pacientes;
- Perfis e permissões com controle de acesso baseado em papéis e escopo de clínica;
- Motor de fluxo de estados por entidade;
- Registros de auditoria;
- Gerenciamento de exames, incluindo *upload*, *download*, análise por IA, revisão médica,
  cancelamento e restauração;
- Impressão do relatório do exame em PDF pelo médico responsável e pelo gestor da clínica,
  conforme as regras de autorização;
- Integração automática entre o *backend* e o serviço de IA;
- Classificação binária por *Ensemble Stacking*, combinando ResNet-50, EfficientNet-B4 e
  PVTv2-B2;
- Revisão médica com confirmação ou divergência e histórico auditável;
- Disponibilização autenticada do mapa Grad-CAM combinado;
- Apresentação do resultado da IA nas listagens médicas dos exames em estados compatíveis;
- Navegação dos cards do *dashboard* para as listas correspondentes;
- Massa `academic_demo` reproduzível com três clínicas ativas, uma clínica inativa de teste,
  30 pacientes, 90 exames e 72 análises com mapas Grad-CAM.

### Fora do escopo entregue

Não integram o escopo concluído deste protótipo:

- prontuário eletrônico completo;
- agenda médica;
- faturamento;
- bloqueio automático por tentativas inválidas de autenticação;
- implantação clínica;
- validação diagnóstica em pacientes reais;
- avaliação de usabilidade com profissionais ou pacientes;
- certificação para uso assistencial.

---

## 🧠 Inteligência Artificial no Projeto

O ClinicAI integra um método de visão computacional voltado à classificação binária de imagens
de exames gastrointestinais.

### Pipeline de pré-processamento

- Extração de ROI (*Region of Interest*);
- Remoção de *Specular Highlights*;
- Normalização com média e desvio padrão da ImageNet;
- *Data Augmentation* durante o treinamento.

### Modelo

- *Ensemble Stacking* combinando ResNet-50, EfficientNet-B4 e PVTv2-B2;
- Meta-classificador de Regressão Logística treinado sobre as predições dos três modelos-base;
- Artefatos operacionais distribuídos pela GitHub Release configurada;
- Protocolo de treinamento `viana_codigo_kfold3_roi_sh_da`;
- *Fold* operacional 1 integrado ao protótipo.

### Explicabilidade

O mapa de ativação Grad-CAM apresentado ao usuário é uma combinação ponderada dos três mapas
individuais (ResNet-50, EfficientNet-B4 e PVTv2-B2). O peso de cada modelo na combinação é
determinado pela evidência local fornecida ao meta-classificador na predição do exame
específico.

O mapa composto destaca as regiões da imagem que mais influenciaram a classificação final do
*Ensemble Stacking*. Essa visualização é um recurso de explicabilidade *post hoc* e não
constitui localização validada de lesões ou achados clínicos.

### Avaliação Experimental

Na reprodução do método, foi utilizada validação cruzada estratificada com \(k = 3\) *folds*.
Essa configuração permitiu observar a variação dos resultados entre diferentes divisões da
base de imagens, reduzindo a dependência de uma única separação entre treinamento e teste.

| Métrica | Média dos 3 *folds* | *Fold* operacional integrado ao protótipo |
|---|---:|---:|
| Acurácia | 95,97% ± 0,61% | 96,40% |
| Precisão | 96,05% ± 0,51% | 96,41% |
| Sensibilidade | 95,97% ± 0,61% | 96,40% |
| Especificidade | 96,01% ± 0,31% | 96,24% |
| F1-*Score* | 95,99% ± 0,60% | 96,40% |

O *fold* 1 foi integrado ao protótipo por apresentar o melhor desempenho entre as três
execuções tanto em acurácia quanto em F1-*Score*. Mais detalhes sobre a metodologia
experimental e a comparação com o método original são apresentados na monografia do projeto.

Essas métricas representam o desempenho experimental observado nas divisões da base de imagens
utilizada. Elas não correspondem a validação clínica, estimativa de desempenho diagnóstico em
pacientes reais nem avaliação de impacto assistencial.

---

## 📦 Publicação dos Modelos no GitHub Releases

Esta seção é destinada à manutenção dos artefatos de IA. Para apenas executar o sistema,
consulte a seção **Como Executar o Projeto**.

### Release atual

- Tag: `models-v0.1.2`;
- Domínio: `gastrointestinal`;
- Protocolo de treinamento: `viana_codigo_kfold3_roi_sh_da`;
- *Fold* operacional: `1`;
- Critério de seleção: melhor desempenho entre as três execuções da validação cruzada em
  acurácia e F1-*Score*.

As *releases* anteriores, `models-v0.1.0` e `models-v0.1.1`, permanecem preservadas para
manutenção do histórico e reprodutibilidade.

### Publicando uma nova versão

Os passos abaixo devem ser executados sempre que os pesos, o meta-classificador ou alguma
etapa do pré-processamento forem alterados.

#### 1. Preparar os artefatos

Os quatro arquivos finais devem estar em `ai/models/exported/gastrointestinal/`:

```text
resnet50.pt
efficientnet_b4.pt
pvt_v2_b2.pt
meta_classificador.joblib
```

A ordem das *meta-features* deve ser ResNet-50, EfficientNet-B4 e PVTv2-B2, a mesma definida em
`ai/app/inference/domains/gastrointestinal.py`.

#### 2. Gerar o manifesto

Na raiz do projeto, execute, ajustando a tag e a versão:

```bash
python3 scripts/generate_model_manifest.py \
  --release-tag models-v0.1.3 \
  --model-version 0.1.3
```

O comando gera `manifesto_modelos.json` com o tamanho e o *hash* SHA-256 de cada artefato. Os
modelos e o manifesto são ignorados pelo Git e devem ser anexados manualmente à *release*.

#### 3. Criar a release no GitHub

Na seção **Releases**, selecione **Draft a new release** e anexe exatamente os cinco arquivos:

```text
resnet50.pt
efficientnet_b4.pt
pvt_v2_b2.pt
meta_classificador.joblib
manifesto_modelos.json
```

Salve inicialmente como rascunho, confira os nomes dos arquivos e publique somente depois da
validação.

#### 4. Atualizar a tag padrão

Depois de validar a nova *release* conforme o procedimento descrito em
[`docs/model-release-guide.md`](docs/model-release-guide.md), atualize
`MODEL_RELEASE_TAG` em `.env.example`.

As *releases* anteriores não devem ser sobrescritas, pois precisam permanecer disponíveis para
reprodutibilidade.

O mecanismo atual utiliza *assets* públicos. Repositórios privados exigem um mecanismo
específico de autenticação. *Tokens* não devem ser armazenados no Docker Compose, no README ou
em arquivos versionados.

---

## 🔐 Bootstrap e Evolução da Matriz RBAC

No modo `bootstrap`, o executor `python -m app.modules.seeds`, chamado pelo *entrypoint* do
*backend*, cria a estrutura inicial e garante a existência de um único Administrador Master.

O campo `roles.permissions_initialized` distingue um papel nunca inicializado de um papel
configurado deliberadamente sem permissões. Depois do primeiro *bootstrap*, as reinicializações
não alteram automaticamente a matriz, e as edições administrativas permanecem como fonte da
verdade.

A *baseline* `0001initial` contém o marcador de *bootstrap* e o catálogo estrutural atual. Na
matriz padrão, `clinic_manager` possui acesso operacional à própria clínica, sem receber
`exams:read` ou `ai_analysis:read`.

O perfil `admin_master` administra os componentes estruturais e operacionais da plataforma,
mas esse privilégio administrativo não concede acesso aos resultados clínicos da IA nem às
revisões médicas.

Mudanças oficiais futuras em bancos existentes devem ser implementadas por novas *migrations*
de dados do Alembic.

Somente quando houver intenção de descartar customizações e restaurar toda a matriz padrão,
execute manualmente:

```bash
docker compose exec backend python -m app.modules.role_permissions.reconcile \
  --confirm RECONCILE_RBAC
```

O comando registra quantos vínculos foram adicionados e removidos por papel e não é executado
automaticamente pelo *entrypoint*.

Para consultar os princípios de autenticação, autorização e segurança que orientam essa matriz,
acesse [`docs/access-control-and-security.md`](docs/access-control-and-security.md).

---

## 📚 Contribuição Acadêmica

O ClinicAI reúne, em um único protótipo acadêmico:

- aplicação de práticas de Engenharia de Software em um sistema web modular;
- integração entre uma aplicação de gerenciamento clínico e um serviço de visão computacional;
- implementação de controle de acesso baseado em papéis e escopo de clínica;
- reprodução experimental de um método de *Ensemble Stacking*;
- integração de classificação binária, revisão médica e explicabilidade visual por Grad-CAM;
- disponibilização de uma massa demonstrativa sintética e reproduzível.

---

## 📄 Observações Acadêmicas

O ClinicAI é um protótipo desenvolvido para fins acadêmicos no escopo de um Trabalho de
Conclusão de Curso. O sistema foi verificado tecnicamente em ambiente local com dados
demonstrativos e não foi implantado, validado ou avaliado em ambiente clínico real.

Os resultados automatizados não constituem diagnóstico médico e não substituem a análise nem a
conclusão de um profissional qualificado.

---

## 📄 Licença

Projeto acadêmico desenvolvido para fins educacionais.
