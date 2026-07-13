# Matriz de controle de acesso do ClinicAI

Este documento registra a decisão arquitetural da RBAC-04. A interface não é
considerada uma barreira de segurança: toda restrição exibida no frontend é
repetida no backend, que permanece como fonte autoritativa da autorização.

## Política adotada

- Módulos estruturais são exclusivos do perfil `admin_master`.
- Pacientes e exames usam permissões granulares e o escopo clínico aplicado
  pelos serviços do backend.
- Dashboard e perfil próprio são acessíveis a usuários autenticados; as APIs
  de perfil exigem permissões específicas de autoatendimento.
- Uma permissão administrativa eventualmente vinculada a outra role não abre
  Clínicas, Usuários administrativos ou Logs de Auditoria.

## Matriz única de rotas

| Área e rotas frontend | Requisito no frontend | Endpoints backend relacionados | Dependência backend |
| --- | --- | --- | --- |
| `/dashboard` | Usuário autenticado | APIs consumidas pelos cartões | Permissão de cada recurso e escopo do usuário |
| `/profile` | Usuário autenticado | `GET/PATCH /users/me`, `PATCH /users/me/password`, `GET/PATCH /clinics/me` | `users:read_profile`, `users:update_profile`, `clinics:read_profile` ou `clinics:update_profile` |
| `/clinics`, `/clinics/create`, `/clinics/:id`, `/clinics/:id/edit` | Role `admin_master` | CRUD, ativação e inativação em `/clinics` | `require_admin` |
| `/users`, `/users/create`, `/users/:id`, `/users/:id/edit` | Role `admin_master` | CRUD, senha, ativação e inativação em `/users` | `require_admin` |
| `/audit-logs` | Role `admin_master` | `GET /audit-logs/` | `require_admin` |
| `/patients` e `/patients/:id` | `patients:read` | `GET /patients/` e `GET /patients/{id}` | `require_permission("patients:read")` + escopo |
| `/patients/create` | `patients:create` | `POST /patients/` | `require_permission("patients:create")` + escopo |
| `/patients/:id/edit` | `patients:update` | `PATCH /patients/{id}` | `require_permission("patients:update")` + escopo |
| Ações de status de pacientes | Ação interna por permissão | `PATCH /patients/{id}/activate` e `/inactivate` | `require_permission("patients:change_status")` + escopo |
| `/exams` e `/exams/:id` | `exams:read` | `GET /exams/`, `/exams/{id}` e `/exams/form-options` | `require_permission("exams:read")` + escopo |
| `/exams/create` | `exams:create` | `POST /exams/` | `require_permission("exams:create")` + escopo |
| `/exams/:id/edit` | `exams:update` | `PATCH /exams/{id}` | `require_permission("exams:update")` + escopo |
| Ações de exame | Permissão correspondente à ação | Cancelar/restaurar, analisar, revisar, baixar e substituir arquivo | `exams:change_status`, `ai_analysis:create`, `exams:review`, `exams:download` ou `exams:upload` + escopo |
| `/roles`, `/permissions` e `/statuses` | Role `admin_master` | APIs de configuração correspondentes | `require_admin` |

## Verificação de regressão

O teste `backend/tests/test_rbac_route_matrix.py` inspeciona as dependências
registradas nas rotas FastAPI. Ele falha se um endpoint estrutural deixar de
usar `require_admin` ou se uma rota de perfil próprio for acidentalmente
convertida em exclusiva do administrador.

## Matriz de ações da interface

As páginas de listagem não usam mais um booleano agregado de gerenciamento.
Cada botão consulta a permissão correspondente, e as regras de estado do
registro são aplicadas como uma condição adicional.

| Recurso | Ação da interface | Permissão exigida | Condição adicional |
| --- | --- | --- | --- |
| Pacientes | Visualizar | `patients:read` | Registro no escopo do usuário |
| Pacientes | Cadastrar | `patients:create` | — |
| Pacientes | Editar | `patients:update` | Registro no escopo do usuário |
| Pacientes | Ativar ou inativar | `patients:change_status` | Estado atual do paciente |
| Clínicas | Visualizar | `clinics:read` | Entrada do módulo restrita a `admin_master` |
| Clínicas | Cadastrar | `clinics:create` | Entrada do módulo restrita a `admin_master` |
| Clínicas | Editar | `clinics:update` | Entrada do módulo restrita a `admin_master` |
| Clínicas | Ativar ou inativar | `clinics:change_status` | Role administrativa e estado atual |
| Usuários | Visualizar | `users:read` | Entrada do módulo restrita a `admin_master` |
| Usuários | Cadastrar | `users:create` | Entrada do módulo restrita a `admin_master` |
| Usuários | Editar | `users:update` | Entrada do módulo restrita a `admin_master` |
| Usuários | Ativar ou inativar | `users:change_status` | Role administrativa e estado atual |
| Exames | Visualizar | `exams:read` | Exame no escopo do usuário |
| Exames | Cadastrar | `exams:create` | — |
| Exames | Editar | `exams:update` | Status `processing` ou `pending` |
| Exames | Cancelar ou retomar | `exams:change_status` | Status compatível com a transição |
| Exames | Baixar arquivo | `exams:download` | Arquivo existente |
| Exames | Substituir arquivo | `exams:upload` | Ação preparada na matriz para a interface correspondente |
| Exames | Revisar | `exams:review` | Role `doctor` e status `awaiting_review` |
| Exames | Solicitar análise | `ai_analysis:create` | Exame e status compatíveis |

O teste `frontend/scripts/check-action-permissions.mjs` simula uma role com
uma única permissão por vez. Ele confirma que nenhuma concessão libera outra
ação e também verifica se os componentes de lista e os botões adicionais estão
ligados aos booleanos específicos.

O catálogo técnico e o procedimento obrigatório para incluir novas permissões
estão documentados em `docs/permission-catalog.md`.
