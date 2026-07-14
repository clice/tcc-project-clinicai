# CHK-03 — Banco, migrations e seeds

**Objetivo:** comprovar que o ClinicAI parte de um PostgreSQL vazio, aplica uma única árvore de migrations, mantém um contrato explícito de chaves/índices/cascatas e reinicia sem duplicar dados ou sobrescrever configurações administrativas.

## 1. Decisões aplicadas

### 1.1 Alembic é a única fonte do schema

O código da aplicação não chama `Base.metadata.create_all()`. Em instalação limpa, o schema público permanece sem tabelas do ClinicAI até a execução de:

```bash
alembic upgrade head
```

O teste `test_application_never_calls_create_all` impede a reintrodução de criação paralela do schema.

### 1.2 Head único e migration reversível do CHK-03

A árvore possui um único head:

```text
d3e5f7a9b102
```

A migration `d3e5f7a9b102_add_clinic_status_index.py` cria o índice de `clinics.status_id`, a única FK operacional principal que ainda não tinha índice explícito. O `downgrade()` remove somente esse índice.

O verificador também faz round-trip das migrations recentes de RBAC, voltando até `a1b2c3d4e5f6` e retornando ao head antes de criar os dados.

### 1.3 Política de cascata

A política foi mantida conservadora para dados clínicos:

| Relação | ON DELETE | Motivo |
|---|---|---|
| `role_permissions.role_id → roles.id` | `CASCADE` | vínculo associativo sem existência independente |
| `role_permissions.permission_id → permissions.id` | `CASCADE` | vínculo associativo sem existência independente |
| clínicas, usuários, pacientes, exames, análises e auditoria | `RESTRICT/NO ACTION` | impedir exclusões físicas que deixem histórico clínico ou de auditoria incompleto |

O relacionamento ORM `Exam.ai_analysis` continua responsável pelo ciclo de vida da análise quando uma exclusão controlada ocorrer pela aplicação. O banco, por padrão, não permite exclusão direta que viole integridade.

### 1.4 Bootstrap separado da massa acadêmica

A variável `SEED_MODE` aceita dois valores:

| Modo | Conteúdo |
|---|---|
| `bootstrap` | statuses, roles, catálogo oficial de permissions e bootstrap inicial de role-permissions |
| `academic_demo` | executa o bootstrap e acrescenta clínicas, usuários, pacientes, exames e análises inteiramente fictícios |

O padrão interno seguro é `bootstrap`. O arquivo `backend/.env.example`, destinado ao desenvolvimento acadêmico local, usa `academic_demo` explicitamente.

Comandos equivalentes:

```bash
python -m app.modules.seeds --mode bootstrap
python -m app.modules.seeds --mode academic_demo
```

### 1.5 Transações dos seeds

As funções dos módulos usam `flush()` para obter IDs e não realizam commits parciais. O executor central controla duas transações:

1. bootstrap estrutural;
2. massa acadêmica opcional.

Se a massa demo falhar depois de criar clínicas, toda a fase demo sofre rollback; o bootstrap estrutural já concluído continua válido.

### 1.6 Preservação de configuração administrativa

Em registros já existentes, os seeds não atualizam textos, senhas ou vínculos. O teste de aceite altera deliberadamente:

- `roles.display_name` do médico;
- `statuses.display_name` de exame pendente;
- revoga `exams:download` do médico;
- concede `audit_logs:read` ao médico.

Três novas execuções completas do startup precisam produzir snapshots idênticos à configuração alterada.

### 1.7 Dados de demonstração previsíveis

Os pacientes deixaram de usar a “primeira clínica ativa” e o “primeiro médico ativo” encontrados no banco. Os vínculos agora são resolvidos pelas chaves conhecidas da massa acadêmica (`clinic_primary` e `doctor_primary`).

Também foi corrigido o exame de processamento que estava ligado à clínica primária, mas ao médico da clínica secundária. Todos os pacientes e exames demo agora possuem clínica e médico coerentes.

As análises simuladas usam apenas os rótulos binários `normal` e `anormal`, e o nome do modelo deixa explícito que se trata de resultado demo.

## 2. Credenciais acadêmicas

As contas abaixo só são criadas com `SEED_MODE=academic_demo`:

| Perfil | E-mail | Senha |
|---|---|---|
| Administrador Master | `admin@clinicai.com` | `clinicai123` |
| Médico primário | `doctor@clinicai.com` | `clinicai123` |
| Médico secundário | `doctor2@clinicai.com` | `clinicai123` |
| Funcionário | `staff@clinicai.com` | `clinicai123` |
| Usuário inativo | `inactive@clinicai.com` | `clinicai123` |

Essas credenciais são padronizadas para reprodutibilidade acadêmica, vinculadas apenas a dados fictícios e proibidas em qualquer ambiente com dados reais. Em outro ambiente, use `SEED_MODE=bootstrap` e um procedimento separado de provisionamento administrativo.

## 3. Contagens esperadas

### Bootstrap

| Tabela | Quantidade |
|---|---:|
| `statuses` | 17 |
| `roles` | 3 |
| `permissions` | catálogo oficial atual |
| `role_permissions` | matriz inicial oficial |
| tabelas demo | 0 |

### Academic demo

| Tabela | Quantidade |
|---|---:|
| `clinics` | 8 |
| `users` | 5 |
| `patients` | 8 |
| `exams` | 3 |
| `ai_analysis` | 2 |
| `audit_logs` | 0 |

Os snapshots não incluem IDs, timestamps nem hashes bcrypt, pois esses valores não devem ser usados para medir idempotência semântica.

## 4. Verificação automatizada

### Windows/PowerShell

Na raiz do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_chk03_database.ps1
```

Para manter os containers após a execução:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_chk03_database.ps1 -KeepEnvironment
```

### Linux/macOS/WSL

```bash
sh scripts/verify_chk03_database.sh
```

Para manter o ambiente:

```bash
CHK03_KEEP_ENVIRONMENT=1 sh scripts/verify_chk03_database.sh
```

O procedimento usa `docker-compose.chk03.yml`, um PostgreSQL 16 e um volume próprios. O banco de desenvolvimento e o volume `postgres_data` do Compose principal não são tocados.

## 5. Etapas executadas pelo verificador

1. remove um ambiente CHK-03 antigo;
2. inicia PostgreSQL descartável;
3. confirma que não existem tabelas da aplicação;
4. executa `alembic upgrade head`;
5. executa `alembic check`;
6. inventaria uniques, FKs, cascatas e índices;
7. testa downgrade/upgrade da migration do índice;
8. faz round-trip das migrations recentes de RBAC;
9. executa startup em modo `bootstrap`;
10. confirma ausência de dados demo;
11. aplica customização administrativa e executa três startups;
12. compara os quatro snapshots;
13. habilita `academic_demo` e valida credenciais/vínculos;
14. executa mais três startups e compara snapshots.

## 6. Evidências

Quando aprovado, os arquivos ficam em `reports/chk-03/`:

- `schema-inventory.json`;
- `schema-after-roundtrip.json`;
- `bootstrap-customized-reference.json`;
- `bootstrap-restart-1.json` a `bootstrap-restart-3.json`;
- `academic-demo-reference.json`;
- `academic-demo-restart-1.json` a `academic-demo-restart-3.json`;
- `result.txt`.

`reports/` é ignorado pelo Git. Para a monografia, preserve uma cópia externa das evidências associada ao commit testado.

## 7. Critério de conclusão

O CHK-03 só deve ser marcado como concluído quando `reports/chk-03/result.txt` contiver:

```text
CHK-03 aprovado.
```

Sem a execução Docker/PostgreSQL, as alterações podem ser consideradas implementadas e revisadas estaticamente, mas não homologadas.
