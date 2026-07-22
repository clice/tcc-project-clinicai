# ClinicAI Backend

API principal do ClinicAI, desenvolvida em FastAPI para integrar a gestão administrativa do protótipo, o fluxo de exames endoscópicos, o banco de dados PostgreSQL e o serviço de Inteligência Artificial.

## Finalidade

O backend concentra as regras de negócio e é a fonte autoritativa para autenticação, autorização, escopo institucional, persistência e transições de estado. O frontend apresenta essas operações ao usuário, enquanto o serviço de IA realiza a inferência sobre as imagens encaminhadas pela API principal.

O módulo foi concluído dentro do escopo acadêmico do Trabalho de Conclusão de Curso. Sua verificação técnica não representa validação clínica, auditoria profissional de segurança ou autorização para uso em produção.

## Escopo implementado

- autenticação JWT com tokens de acesso e atualização;
- rotação de *refresh tokens* e invalidação de sessões;
- gestão de usuários, clínicas e pacientes;
- perfis, permissões e matriz RBAC;
- isolamento de dados por clínica e por responsabilidade médica;
- catálogos controlados de perfis, permissões e status;
- logs de auditoria;
- cadastro, consulta, atualização, download, cancelamento e restauração de exames;
- envio de imagens ao serviço de IA;
- persistência do resultado, da confiança e dos metadados da análise;
- disponibilização autenticada de imagens e mapas Grad-CAM;
- revisão médica com confirmação ou registro de divergência;
- histórico e máquina de estados do fluxo de exames;
- migrations e seeds reproduzíveis para bootstrap e demonstração acadêmica.

## Tecnologias

- Python;
- FastAPI e Uvicorn;
- SQLAlchemy;
- PostgreSQL;
- Alembic;
- Pydantic;
- JWT;
- Pytest;
- Docker e Docker Compose.

## Organização

```text
backend/
├── alembic/                 # migrations e configuração do banco
├── app/
│   ├── common/              # validações, schemas e utilitários compartilhados
│   ├── core/                # configuração, banco, segurança e dependências
│   ├── maintenance/         # verificações e contratos estruturais
│   ├── modules/             # módulos de negócio e rotas da API
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

Os módulos de negócio seguem uma separação por responsabilidade, com arquivos de modelo, schema, serviço, router e seed quando aplicável. O conjunto inclui autenticação, usuários, clínicas, pacientes, perfis, permissões, associações entre perfis e permissões, status, auditoria, exames e análises de IA.

## Integração

```text
Frontend React
      ↓
Backend FastAPI ↔ PostgreSQL
      ↓
Serviço de IA FastAPI
```

O backend valida a identidade e as permissões do usuário, registra o exame, controla seu estado e encaminha a imagem ao serviço de IA. Depois da inferência, persiste o resultado e disponibiliza os dados necessários à revisão médica no frontend.

## Configuração

A execução integrada por Docker Compose é a forma recomendada. A partir da raiz do repositório:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

O arquivo `backend/.env` deve conter as configurações indicadas em `.env.example`. `DATABASE_URL` e `SECRET_KEY` são obrigatórias e não possuem valores padrão no código.

Os arquivos `.env` locais não devem ser versionados. Os valores disponibilizados nos exemplos servem apenas à reprodução acadêmica em ambiente local.

Para subir o banco, o backend e suas dependências:

```bash
docker compose up --build -d
```

O backend fica disponível em <http://localhost:8000> e a documentação interativa da API em <http://localhost:8000/docs>.

## Inicialização do banco

O `entrypoint.sh` executa automaticamente:

1. espera pelo PostgreSQL;
2. aplica as migrations pendentes com `alembic upgrade head`;
3. executa os seeds conforme `SEED_MODE`;
4. inicia a API.

Os modos de seed são:

| `SEED_MODE` | Resultado |
|---|---|
| `bootstrap` | cria os catálogos estruturais, a matriz inicial de permissões e um Administrador Master |
| `academic_demo` | executa o bootstrap e acrescenta dados fictícios para a demonstração acadêmica |

O modo `bootstrap` é o padrão do backend e do arquivo `backend/.env.example`. Para facilitar a demonstração local em um banco novo, defina explicitamente `SEED_MODE=academic_demo` no arquivo local `backend/.env` antes de subir os containers.

Os seeds são idempotentes: não apagam registros existentes nem restauram automaticamente customizações administrativas. A troca de `academic_demo` para `bootstrap` também não remove dados demonstrativos já persistidos.

Comandos manuais equivalentes:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.modules.seeds --mode bootstrap
docker compose exec backend python -m app.modules.seeds --mode academic_demo
```

## Massa demonstrativa

Em um banco novo, o modo `academic_demo` consolidado produz:

- três clínicas;
- um Administrador Master criado pelo bootstrap;
- seis contas demonstrativas;
- 30 pacientes fictícios;
- 90 exames, sendo 30 por clínica;
- 72 análises concluídas pelo `ensemble_stacking` versão `0.1.1`, com mapas Grad-CAM.

A massa contempla os estados `pending`, `awaiting_review`, `completed`, `completed_with_divergence`, `failed` e `canceled`.

As imagens acadêmicas, sua procedência, licenças, hashes, vínculos e resultados estão documentados em [`demo_assets/manifest.json`](demo_assets/manifest.json) e [`demo_assets/README.md`](demo_assets/README.md). Esses ativos são destinados exclusivamente à demonstração do protótipo.

## Controle de acesso

O backend aplica as regras de acesso independentemente da visibilidade de menus e botões no frontend.

- o Administrador Master gerencia os módulos estruturais;
- o gestor permanece restrito à própria clínica;
- o médico permanece restrito aos pacientes e exames sob sua responsabilidade;
- filtros recebidos pela API não ampliam o escopo institucional;
- a revisão médica exige o perfil de médico e a permissão correspondente;
- imagens originais e Grad-CAMs são entregues por rotas autenticadas, com validação de vínculo e caminho.

A descrição completa está em [`../docs/access-control-and-security.md`](../docs/access-control-and-security.md).

## Armazenamento de arquivos

As imagens enviadas são persistidas em `data/exams/`, por meio do diretório operacional montado como `/app/data` no container. O volume `uploads_data`, montado como `/app/uploads`, permanece somente para compatibilidade com o armazenamento legado. Os ativos demonstrativos versionados permanecem em `demo_assets/`. O acesso a imagens de exame e mapas de atribuição ocorre por meio da API, sujeito às regras de autenticação e escopo.

O backend valida o vínculo do arquivo com o exame, a existência do arquivo e a resolução segura de seu caminho antes de disponibilizá-lo.

## Verificação técnica

A suíte automatizada pode ser executada a partir da raiz do projeto:

```bash
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m pytest -q
```

Na consolidação documental do protótipo, a suíte registrou 219 testes aprovados e dois ignorados. O número pode mudar conforme a evolução do repositório; o resultado atual do comando é a referência válida.

Os testes cobrem, entre outros pontos, autenticação, sessões, RBAC, isolamento entre clínicas, arquivos de exames, máquina de estados, revisão médica, integração com a IA, migrations, seeds e auditoria.

Essa suíte fornece regressão técnica proporcional ao protótipo acadêmico. Não se pretende reproduzir uma auditoria de produção, certificação de segurança ou validação clínica.

## RBAC e manutenção

O bootstrap inicializa a matriz padrão de perfis e permissões sem sobrescrever edições administrativas em reinicializações posteriores.

Somente quando houver intenção explícita de descartar customizações e restaurar a matriz padrão, execute:

```bash
docker compose exec backend python -m app.modules.role_permissions.reconcile \
  --confirm RECONCILE_RBAC
```

O comando não é chamado automaticamente pelo entrypoint.

## Limites do protótipo

O backend sustenta o fluxo acadêmico definido para o ClinicAI, mas não constitui prontuário eletrônico completo e não inclui agenda médica, faturamento, integrações hospitalares ou controles de produção em larga escala.

O resultado da IA é um apoio computacional à detecção e à triagem de achados em imagens endoscópicas. Ele não substitui a avaliação médica e não deve ser apresentado como diagnóstico definitivo.

## Autoria

Desenvolvido por **Clice Bezerra Brito Romão** como parte do Trabalho de Conclusão de Curso do ClinicAI.
