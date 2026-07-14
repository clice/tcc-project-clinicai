# Plano de branches e commits — CHK-03

## Branch de base

O CHK-03 depende dos locks e Dockerfiles produzidos no CHK-02. A ordem recomendada é:

```text
feature-fix
└── chore/chk-02-reproducible-builds   (merge primeiro)
    └── chore/chk-03-database-migrations-seeds
```

Se o CHK-02 já estiver incorporado em `feature-fix`, crie o CHK-03 diretamente dela:

```bash
git switch feature-fix
git pull --ff-only
git switch -c chore/chk-03-database-migrations-seeds
```

Não crie a branch a partir de `main` se `main` ainda não contém as correções RBAC e CHK-02.

## Commits recomendados

### Commit 1 — migration e contrato do schema

```text
fix(db): add missing clinic status index and schema contract
```

Arquivos principais:

- `backend/app/modules/clinics/model.py`;
- `backend/alembic/versions/d3e5f7a9b102_add_clinic_status_index.py`;
- `backend/app/maintenance/database_contract.py`;
- `backend/tests/test_database_contract.py`.

Teste antes do commit:

```bash
python -m compileall backend/app backend/alembic backend/tests
```

### Commit 2 — separação e atomicidade dos seeds

```text
refactor(seeds): separate structural bootstrap from academic demo data
```

Arquivos principais:

- `backend/app/core/config.py`;
- `backend/app/modules/seeds.py`;
- `backend/app/modules/*/seed.py`;
- `backend/entrypoint.sh`;
- `backend/.env.example`;
- `backend/tests/test_seed_modes.py`.

### Commit 3 — verificação de reinícios e migrations

```text
test(db): verify migrations and seed idempotency on PostgreSQL
```

Arquivos principais:

- `docker-compose.chk03.yml`;
- `scripts/verify_chk03_database.ps1`;
- `scripts/verify_chk03_database.sh`;
- `.gitignore`.

Teste antes do commit:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_chk03_database.ps1
```

### Commit 4 — documentação

```text
docs(db): document CHK-03 workflow and academic credentials
```

Arquivos principais:

- `README.md`;
- `docs/chk-03-database-migrations-seeds.md`;
- `docs/chk-03-commit-plan.md`.

## Integração

Depois de todos os testes:

```bash
git push -u origin chore/chk-03-database-migrations-seeds
```

Abra PR para `feature-fix` com o título:

```text
CHK-03: banco, migrations e seeds reproduzíveis
```

No PR, anexe ou resuma:

- resultado de `alembic check`;
- `reports/chk-03/result.txt`;
- revisão testada;
- contagens bootstrap/demo;
- confirmação dos três reinícios;
- confirmação de que o banco de desenvolvimento não foi usado.

Após o merge:

```bash
git switch feature-fix
git pull --ff-only
git branch -d chore/chk-03-database-migrations-seeds
```

A branch seguinte do plano unificado deve nascer da `feature-fix` já atualizada, por exemplo:

```bash
git switch -c fix/chk-04-authentication-session
```
