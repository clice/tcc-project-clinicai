# Estratégia automatizada de testes RBAC

A conclusão da rodada de RBAC do ClinicAI é protegida por testes de backend e
verificadores estáticos/comportamentais do frontend. A suíte foi organizada
para que uma rota nova sem política explícita ou uma permissão visual sem
barreira equivalente no backend interrompa a integração contínua.

## Cobertura do backend

| Risco | Evidência automatizada |
| --- | --- |
| Rota protegida sem dependência | `test_rbac_authorization_matrix.py` inspeciona todas as `APIRoute` não públicas |
| Perfil autorizado incorretamente | A matriz executa `admin_master`, `doctor` e `clinic_staff` contra cada política registrada |
| Permissão fora do catálogo | Cada `require_permission` e `require_doctor_permission` é confrontado com o catálogo oficial |
| Concessão ou revogação perdida no reinício | `test_role_permissions_seed.py` repete o bootstrap após uma matriz personalizada |
| Sincronização parcial | `test_role_permission_sync.py` força falha após modificar vínculos e confirma rollback integral |
| Acesso entre clínicas | `test_tenant_isolation.py` cobre clínica, paciente, exame e vínculo exclusivo do médico |
| Revisão clínica delegada | `test_medical_review_authorization.py` exige role médica e `exams:review` |
| Usuário inativo | `test_session_authorization.py` confirma HTTP 403 mesmo com JWT válido |
| Token antigo após logout | O mesmo arquivo confirma HTTP 401 para access e refresh token com `token_version` antigo |
| Campo desconhecido | `test_strict_request_schemas.py` exige `extra='forbid'` e resposta HTTP 422 |

Os testes utilizam SQLite em memória e valores de configuração descartáveis,
definidos em `tests/conftest.py`. Variáveis fornecidas explicitamente pelo
ambiente continuam tendo prioridade. Nenhum `.env` de teste ou segredo precisa
ser versionado.

## Cobertura do frontend

O comando único abaixo executa todos os verificadores de RBAC:

```bash
npm run check:rbac
```

Além das verificações específicas de catálogo, navegação, ações e propagação
para sessões ativas, `check-rbac-contract.mjs` confronta:

- permissões declaradas nas rotas React;
- permissões usadas pelo menu lateral;
- permissões que habilitam botões e ações;
- dependências `require_permission` e `require_doctor_permission` do backend;
- módulos cuja barreira deliberada é `require_admin`.

## Execução antes de commit ou implantação

```bash
cd backend
python -m pytest -q

cd ../frontend
npm run check:rbac
npm run build
```

O banco em memória comprova regras e transações de forma determinística. A
homologação com PostgreSQL, Docker e duas sessões reais continua necessária no
plano de testes de implantação, pois valida integração de infraestrutura e não
substitui esta suíte unitária/contratual.
