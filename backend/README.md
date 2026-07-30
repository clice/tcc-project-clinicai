# Backend

API principal do ClinicAI, desenvolvida com FastAPI para integrar o gerenciamento administrativo
do protótipo, o fluxo de exames gastrointestinais, o banco de dados PostgreSQL e o serviço de
Inteligência Artificial.

## Finalidade

O backend concentra as regras de negócio e atua como fonte autoritativa para autenticação,
autorização, escopo institucional, persistência, auditoria e transições de estado. O frontend
apresenta essas operações ao usuário, enquanto o serviço de IA realiza a inferência sobre as
imagens encaminhadas pela API principal.

O módulo foi concluído dentro do escopo acadêmico do Trabalho de Conclusão de Curso. Sua
verificação técnica não representa validação clínica, auditoria profissional de segurança,
certificação ou autorização para uso em produção.

## Escopo implementado

- autenticação JWT com *access tokens* e *refresh tokens*;
- rotação de *refresh tokens* e invalidação de sessões;
- gerenciamento de usuários, clínicas e pacientes;
- perfis, permissões e matriz RBAC;
- isolamento de dados por clínica e por responsabilidade médica;
- catálogos controlados de perfis, permissões e estados;
- registros de auditoria;
- cadastro, consulta, atualização, *upload*, *download*, cancelamento e restauração de exames;
- envio de imagens ao serviço de IA;
- persistência do resultado, da confiança e dos metadados da análise automatizada;
- disponibilização autenticada das imagens originais e dos mapas Grad-CAM;
- revisão médica com confirmação ou registro de divergência;
- histórico e máquina de estados do fluxo de exames;
- geração do relatório final do exame em PDF, conforme as regras de autorização;
- *migrations* e *seeds* reproduzíveis para o *bootstrap* e a demonstração acadêmica.

## Tecnologias

- Python;
- FastAPI e Uvicorn;
- Pydantic;
- SQLAlchemy;
- PostgreSQL;
- Alembic;
- Python-JOSE para autenticação JWT;
- HTTPX para comunicação com o serviço de IA;
- ReportLab para geração dos relatórios em PDF;
- Pytest;
- Docker e Docker Compose.

## Organização

```text
backend/
├── alembic/                 # migrations e configuração do banco
├── app/
│   ├── common/              # constantes, validações e utilitários compartilhados
│   ├── core/                # configuração, banco, segurança e dependências
│   ├── maintenance/         # verificações e contratos estruturais
│   ├── modules/             # módulos de negócio, serviços, rotas e seeds
│   └── main.py              # aplicação FastAPI
├── demo_assets/             # ativos e manifesto da demonstração acadêmica
├── tests/                   # testes automatizados do backend
├── .env.example             # exemplo de configuração
├── alembic.ini
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
├── requirements.lock.txt
└── README.md
```

Os módulos de negócio são separados por responsabilidade e incluem arquivos de modelo, schema,
serviço, rota e *seed* quando aplicável. O conjunto abrange autenticação, usuários, clínicas,
pacientes, perfis, permissões, associações entre perfis e permissões, estados, auditoria,
exames e análises de IA.

## Integração

```text
Frontend React
      ↓
Backend FastAPI ↔ PostgreSQL
      ↓
Serviço de IA FastAPI
```

O backend valida a identidade, as permissões e o escopo do usuário, registra o exame, controla
seu estado e encaminha a imagem ao serviço de IA. Depois da inferência, valida e persiste o
resultado e o mapa de atribuição, disponibilizando os dados autorizados para a revisão médica.

## Configuração

A execução integrada com Docker Compose é a forma recomendada. A partir da raiz do
repositório, copie os arquivos de exemplo:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

O arquivo `backend/.env` deve conter as configurações indicadas em `.env.example`.
`DATABASE_URL` e `SECRET_KEY` são obrigatórias e não possuem valores padrão no código.

Os arquivos `.env` locais não devem ser versionados. Os valores disponibilizados nos exemplos
servem apenas à reprodução acadêmica em ambiente local.

Para iniciar os serviços:

```bash
docker compose up --build -d
```

O backend fica disponível em <http://localhost:8000>, e a documentação interativa da API pode
ser acessada em <http://localhost:8000/docs>.

## Inicialização do banco

O arquivo `entrypoint.sh` executa automaticamente:

1. aguarda o PostgreSQL aceitar conexões;
2. aplica as *migrations* pendentes com `alembic upgrade head`;
3. executa os *seeds* conforme o valor de `SEED_MODE`;
4. inicia a API.

Os modos disponíveis são:

| `SEED_MODE` | Resultado |
|---|---|
| `bootstrap` | cria os catálogos estruturais, a matriz inicial de permissões e um Administrador Master |
| `academic_demo` | executa o *bootstrap* e acrescenta os dados fictícios da demonstração acadêmica |

O modo `bootstrap` é o padrão do backend e de `backend/.env.example`. Para carregar a massa
acadêmica em um banco novo, defina explicitamente `SEED_MODE=academic_demo` no arquivo local
`backend/.env` antes de iniciar os *containers*.

> **Atenção:** o modo `academic_demo` é destinado exclusivamente à demonstração acadêmica e
> não deve ser executado sobre um banco com dados reais.

Os *seeds* são idempotentes em relação ao estado acadêmico esperado. O *bootstrap* não
sobrescreve automaticamente customizações posteriores da matriz RBAC. O modo `academic_demo`
reconcilia os registros reservados da demonstração e pode remover análises acadêmicas obsoletas
vinculadas aos exames demonstrativos, sem apagar indiscriminadamente registros alheios à massa.
A troca posterior para `bootstrap` não remove a massa já persistida.

Comandos manuais equivalentes:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.modules.seeds --mode bootstrap
docker compose exec backend python -m app.modules.seeds --mode academic_demo
```

## Massa demonstrativa

Em um banco novo, o modo `academic_demo` consolidado produz:

- quatro clínicas, sendo três ativas e uma inativa para cenários de teste;
- 13 usuários no total, incluindo o Administrador Master criado pelo *bootstrap*;
- 30 pacientes fictícios;
- 90 exames, sendo 30 por clínica ativa;
- 72 análises concluídas pelo modelo `ensemble_stacking` versão `0.1.2`;
- 72 mapas Grad-CAM;
- 464 registros de auditoria.

A massa contempla os estados `pending`, `awaiting_review`, `completed`,
`completed_with_divergence`, `failed` e `canceled`.

As 90 imagens acadêmicas são distribuídas igualmente entre os rótulos de origem: 45 normais e
45 anormais. O conjunto possui 50 exames revisados e serve exclusivamente para demonstração
técnica e reprodutibilidade, sem representar avaliação formal nem validação clínica do modelo.

A procedência, as licenças, os *hashes*, os vínculos e os resultados estão documentados em
[`demo_assets/manifest.json`](demo_assets/manifest.json) e
[`demo_assets/README.md`](demo_assets/README.md).

## Controle de acesso

O backend aplica as regras de acesso independentemente da visibilidade de menus e botões no
frontend.

- o Administrador Master gerencia os componentes estruturais e operacionais, mas a matriz
  padrão restringe o acesso ao conteúdo clínico dos exames e às análises de IA;
- o gestor permanece limitado à própria clínica e recebe apenas as informações operacionais
  autorizadas nas listagens;
- o gestor não recebe o rótulo da predição da IA nas listagens de exames;
- o médico permanece limitado aos pacientes e exames sob sua responsabilidade e à clínica à
  qual está vinculado;
- o rótulo da IA é incluído nas listagens apenas para o médico autorizado e nos estados
  compatíveis com a apresentação do resultado;
- filtros enviados à API não ampliam o escopo institucional;
- a revisão médica exige o perfil de médico, a permissão correspondente e o vínculo com o
  exame;
- o relatório final em PDF pode ser gerado pelo médico responsável ou pelo gestor da clínica
  somente para exames concluídos ou concluídos com divergência;
- as imagens originais e os mapas Grad-CAM são entregues por rotas autenticadas, com validação
  de vínculo, escopo e caminho.

A descrição completa das regras está em
[`../docs/access-control-and-security.md`](../docs/access-control-and-security.md).

## Armazenamento de arquivos

As imagens originais e os mapas de atribuição são persistidos na hierarquia canônica:

```text
data/exams/{clinic_id}/{patient_id}/{exam_id}/
├── original/
└── attribution/
```

No *container* do backend, a raiz operacional é montada em `/clinicai-data`. O serviço de IA
não possui acesso direto a essa raiz: ele retorna o mapa codificado em Base64, acompanhado do
tipo MIME e do *hash* SHA-256, e o backend realiza sua validação e persistência.

Os ativos demonstrativos versionados permanecem em `demo_assets/` como fontes acadêmicas,
enquanto suas cópias operacionais são instaladas na hierarquia canônica durante o *seed*.

Antes de disponibilizar um arquivo, o backend valida o vínculo com o exame, a existência do
arquivo, a extensão, a integridade e a resolução segura do caminho. O acesso ocorre somente por
rotas autenticadas e sujeito às regras de escopo.

## Verificação técnica

A suíte automatizada pode ser executada a partir da raiz do projeto:

```bash
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m pytest -q
```

Na validação técnica realizada antes da consolidação desta documentação, foram registrados 273
testes aprovados e 2 testes ignorados conforme a configuração existente. Essa contagem pode
mudar com a evolução do repositório; o resultado atual do comando é a referência válida.

Os testes abrangem autenticação, sessões, RBAC, isolamento entre clínicas, arquivos de exames,
máquina de estados, revisão médica, integração com a IA, relatórios em PDF, *migrations*,
*seeds*, massa acadêmica e auditoria.

Essa suíte fornece regressão técnica proporcional ao protótipo acadêmico. Ela não substitui uma
auditoria de produção, certificação de segurança ou validação clínica.

## RBAC e manutenção

A *baseline* `0001initial` contém o catálogo estrutural e o marcador de inicialização da matriz
de permissões. O campo `roles.permissions_initialized` diferencia um papel ainda não
inicializado de um papel configurado deliberadamente sem permissões.

O *bootstrap* inicializa a matriz padrão apenas quando o papel ainda não foi configurado. Em
reinicializações posteriores, as edições administrativas permanecem como fonte da verdade e
não são sobrescritas automaticamente.

Mudanças oficiais em bancos existentes devem ser implementadas por novas *migrations* de dados
do Alembic.

Somente quando houver intenção explícita de descartar as customizações e restaurar toda a
matriz padrão, execute:

```bash
docker compose exec backend python -m app.modules.role_permissions.reconcile \
  --confirm RECONCILE_RBAC
```

O comando registra a quantidade de vínculos adicionados e removidos por papel e não é executado
automaticamente pelo `entrypoint.sh`.

## Limites do protótipo

O backend sustenta o fluxo acadêmico definido para o ClinicAI, mas não constitui prontuário
eletrônico completo e não inclui agenda médica, faturamento, integrações hospitalares ou
controles de produção em larga escala.

A classificação automatizada e o mapa Grad-CAM são recursos de apoio computacional à análise
de imagens. Eles não constituem diagnóstico médico, não localizam lesões de forma clinicamente
validada e não substituem a avaliação ou a conclusão de um profissional qualificado.

## Autoria

Desenvolvido por **Clice Bezerra Brito Romão** como parte do Trabalho de Conclusão de Curso do
ClinicAI.
