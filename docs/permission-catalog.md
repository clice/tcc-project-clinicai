# Catálogo oficial de permissões do ClinicAI

O ClinicAI utiliza um catálogo fechado. Administradores podem distribuir as
permissões oficiais entre os perfis e editar somente seus textos de exibição,
mas não podem criar nomes técnicos pela interface ou pela API.

A fonte autoritativa é
`backend/app/modules/permissions/catalog.py`. O frontend replica os nomes que
consome em `frontend/src/utils/permissions.js` e a matriz de ações em
`frontend/src/utils/actionPermissions.mjs`.

## Permissões oficiais

| Módulo | Permissões |
| --- | --- |
| Usuários | `users:create`, `users:read`, `users:update`, `users:change_status`, `users:read_profile`, `users:update_profile` |
| Clínicas | `clinics:create`, `clinics:read`, `clinics:update`, `clinics:change_status`, `clinics:read_profile`, `clinics:update_profile` |
| Pacientes | `patients:create`, `patients:read`, `patients:update`, `patients:change_status` |
| Exames | `exams:create`, `exams:read`, `exams:update`, `exams:change_status`, `exams:review`, `exams:upload`, `exams:download` |
| Análise por IA | `ai_analysis:create`, `ai_analysis:read`, `ai_analysis:update` |
| Auditoria | `audit_logs:read` |

## Comportamento de inicialização

- Se a tabela `permissions` estiver vazia, o bootstrap cadastra o catálogo
  completo. Esse fluxo atende a primeira instalação do sistema.
- Se a tabela já possuir registros, o startup apenas valida a presença de
  todas as permissões oficiais.
- Se uma permissão oficial estiver ausente em banco existente, a aplicação
  interrompe a inicialização e exige uma migration. O seed não cria o registro
  silenciosamente.
- Registros antigos que não pertencem ao catálogo não são apagados pelo seed.
  A remoção deve ser feita por migration auditável, como previsto no RBAC-07.

## Procedimento para adicionar uma permissão

1. Adicionar a definição a `OFFICIAL_PERMISSION_DEFINITIONS`.
2. Aplicar `require_permission("modulo:acao")` à rota backend que utilizará a
   permissão e manter as regras de escopo no serviço.
3. Criar uma migration Alembic que insira a permissão e, quando necessário,
   seus vínculos padrão em `role_permissions`.
4. Implementar o `downgrade` removendo primeiro os vínculos e depois a
   permissão.
5. Adicionar a constante e a ação correspondente ao frontend, caso exista
   interface para a funcionalidade.
6. Adicionar testes da rota, da migration e da visibilidade da ação.
7. Executar os verificadores do catálogo, ações e navegação antes do deploy.

Esse fluxo garante que uma permissão só passe a existir após mudança
versionada no código e no banco de dados.
