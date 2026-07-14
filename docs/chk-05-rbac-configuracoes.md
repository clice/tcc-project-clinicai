# CHK-05 — RBAC e configurações

**Data da revisão:** 14 de julho de 2026  
**Escopo:** RBAC-01 a RBAC-12, matriz rota × permissão × role e confronto dos requisitos RF31, RF34 e RF36  
**Perfil do sistema:** protótipo acadêmico e demonstrativo

### Execução no Docker

Na raiz do projeto:

```bash
chmod +x scripts/verify_chk05_rbac.sh
./scripts/verify_chk05_rbac.sh
```

## 1. Resultado executivo

A autorização do ClinicAI permanece centralizada no backend. Todas as rotas não públicas declaram exatamente uma política de acesso (`get_current_user`, `require_admin`, `require_permission` ou `require_doctor_permission`), e a suíte executa as três roles contra cada rota protegida.

A revisão confirmou que RBAC-01 a RBAC-12 já estavam majoritariamente implementados pelas rodadas anteriores. Nesta CHK foram corrigidas três lacunas que ainda permitiam divergência entre o contrato documentado e o comportamento real:

1. `GET/PATCH /clinics/me` estavam registrados depois de `/{clinic_id}` e podiam ser capturados pela rota dinâmica, retornando 422 antes da verificação correta de autoatendimento;
2. o frontend apresentava a matriz do `admin_master` como fixa, mas a API de role-permissions ainda aceitava alterações sem efeito prático, pois o administrador possui bypass autoritativo;
3. RF36 possuía função incompleta no backend, sem rota e sem consumo no frontend. O histórico de exame foi exposto com a mesma permissão `exams:read`, validação de escopo e resposta sem IP ou user-agent.

A matriz completa está em:

- `docs/matriz-rbac-rotas.md`;
- `docs/matriz-rbac-rotas.csv`.

## 2. Estado de RBAC-01 a RBAC-12

| ID | Situação | Evidência principal |
| --- | --- | --- |
| RBAC-01 | Concluído | Bootstrap não destrutivo em `role_permissions/seed.py`, migrations de dados e reconciliação somente por comando explícito. |
| RBAC-02 | Concluído | Catálogo frontend confrontado estaticamente; 27 constantes oficiais e nenhuma referência indefinida. |
| RBAC-03 | Concluído | Rotas, menu, grupos vazios, contadores e contexto de autenticação respondem às permissões reais. |
| RBAC-04 | Concluído | Módulos estruturais usam `require_admin`; pacientes/exames usam permissões granulares; perfil próprio usa permissões de autoatendimento. |
| RBAC-05 | Concluído | Ações de visualizar, criar, editar, status, upload, download, análise e revisão possuem booleanos independentes. |
| RBAC-06 | Concluído | Catálogo de permissões fechado; criação pela API/interface foi encerrada e novas permissões exigem código + migration/teste. |
| RBAC-07 | Concluído | Migration remove `ai_analysis:download` e vínculos antigos, com upgrade/downgrade testados. |
| RBAC-08 | Concluído | Payloads sensíveis usam `extra='forbid'`; campos desconhecidos/imutáveis retornam 422. |
| RBAC-09 | Concluído para o TCC | `/auth/me` é atualizado ao foco, retorno de visibilidade e a cada 60 s; menus, rotas e ações são recalculados. |
| RBAC-10 | Concluído | Revisão exige role `doctor` e `exams:review`; não há bypass para administrador. |
| RBAC-11 | Concluído | Catálogos estruturais não expõem POST de Role, Permission ou Status; OpenAPI reflete somente operações admitidas. |
| RBAC-12 | Concluído | Matriz de rotas, isolamento, persistência, rollback, sessão, schemas, revisão médica e contrato frontend/backend possuem regressão automatizada. |

## 3. Correções desta rodada

### 3.1 Precedência de `/clinics/me`

As rotas estáticas foram movidas antes de `/clinics/{clinic_id}`. Também receberam `response_model=ClinicResponse`. Isso garante que o usuário com `clinics:read_profile` ou `clinics:update_profile` alcance o endpoint correto e não receba 422 por tentativa de converter `me` em inteiro.

### 3.2 Matriz fixa do Administrador Master

O backend agora rejeita com HTTP 403 qualquer tentativa de criar, editar, apagar ou sincronizar vínculos de permissões da role `admin_master`. A decisão corresponde ao frontend, que já apresenta essa matriz em modo somente leitura.

A regra evita uma configuração enganosa: remover um vínculo do administrador no banco não reduziria seu acesso real, pois `require_admin` e o bypass de `require_permission` continuam autorizando o perfil.

### 3.3 Histórico protegido do exame — RF36

Foi criada a rota:

```text
GET /exams/{exam_id}/history
```

Contrato de segurança:

- exige `exams:read`;
- carrega o exame e valida o mesmo escopo usado nos detalhes;
- consulta apenas eventos vinculados ao exame solicitado;
- não expõe `ip_address` nem `user_agent` na resposta clínica;
- o frontend consome a rota no cartão “Histórico do Exame”;
- a conclusão da IA também gera evento vinculado ao exame, tornando a transição para `awaiting_review` visível no histórico.

A listagem global de auditoria continua exclusiva do Administrador Master.

## 4. Matriz e testes

A aplicação possui 65 operações HTTP catalogadas:

- 4 públicas;
- 61 protegidas;
- 183 combinações rota × role verificadas (61 × 3);
- 27 permissões no catálogo oficial;
- 18 permissões na matriz padrão do Médico;
- 8 permissões na matriz padrão do Funcionário da Clínica.

A matriz não substitui o escopo dos serviços. Uma role pode passar pela barreira da rota e ainda receber 403/404 quando tenta acessar clínica, paciente ou exame fora de seu vínculo.

## 5. Confronto com RF31, RF34 e RF36

### RF31 — Consultar exames

Implementado por listagem, busca/filtros e detalhes. A rota exige `exams:read`, e o serviço aplica escopo. Na matriz padrão, Administrador Master e Médico possuem acesso; Funcionário da Clínica não possui.

### RF34 — Baixar arquivo do exame

Implementado por `GET /exams/{exam_id}/download`, com `exams:download` e validação do escopo do exame. Na matriz padrão, Administrador Master e Médico possuem acesso; Funcionário da Clínica não possui.

### RF36 — Consultar histórico do exame

Passou de implementação incompleta para fluxo utilizável no backend e frontend. Usa `exams:read`, o mesmo escopo do exame e resposta sanitizada.

A monografia contém uma inconsistência: a Seção 4.3.3 afirma que o Funcionário da Clínica não acessa exames, mas a tabela de casos de uso ainda inclui FNC no UC08, associado a RF31, RF34 e RF36. O texto recomendado para correção está em `docs/ajustes-monografia-rf31-rf34-rf36.md`.

## 6. Limites conscientes do protótipo acadêmico

- A atualização de permissões em sessões ativas usa polling de 60 segundos, foco e visibilidade, sem WebSocket ou infraestrutura adicional.
- A matriz padrão é a referência dos três perfis, mas permissões granulares de Médico e Funcionário continuam configuráveis pelo administrador.
- O Administrador Master permanece fixo e a revisão médica permanece não delegável.
- Testes com PostgreSQL/Docker e duas sessões reais permanecem parte da homologação posterior; não são necessários para tornar esta rodada de código desproporcional ao escopo acadêmico.

## 7. Critério de conclusão

A CHK-05 é considerada concluída em código quando:

- toda rota não pública possui política explícita;
- a matriz automatizada aprova as três roles;
- módulos estruturais continuam exclusivos do administrador;
- frontend e backend usam a mesma permissão por rota/ação;
- a matriz do administrador é fixa nas duas camadas;
- revisão permanece exclusivamente médica;
- Funcionário não recebe acesso a exames na matriz padrão;
- RF36 funciona com escopo e resposta sanitizada;
- os testes e verificadores descritos no relatório passam.

## 8. Verificações executadas

```text
Backend: 76 passed, 47 warnings
Matriz protegida: 183 combinações rota × role
Frontend RBAC: 7 verificadores aprovados
Compilação Python: aprovada
Sintaxe dos arquivos JavaScript modificados: aprovada
```

Os 47 avisos são de depreciação em dependências (`python-jose` e adaptador SQLite dos testes) e não representam falha da regra de negócio.

O bundle completo do frontend não foi gerado neste ambiente porque o projeto recebido não contém `node_modules` e o executável local do Vite não está instalado (`vite: not found`). O comando a executar após instalar as dependências é:

```bash
cd frontend
npm run build
```
