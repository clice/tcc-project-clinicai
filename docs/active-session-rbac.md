# Propagação de alterações RBAC para sessões ativas

## Objetivo

O backend do ClinicAI consulta a matriz atual do banco antes de autorizar cada
requisição. Portanto, uma permissão revogada deixa de funcionar imediatamente
na API. Entretanto, menus e botões do frontend são calculados a partir dos
dados retornados por `/auth/me` e poderiam permanecer visíveis durante uma
sessão antiga.

## Estratégia adotada

Enquanto houver uma sessão autenticada, o frontend atualiza `/auth/me`:

- quando a janela recupera o foco;
- quando a aba volta ao estado visível;
- a cada 60 segundos enquanto a aba está ativa.

As chamadas são serializadas para impedir atualizações concorrentes. Falhas de
rede transitórias preservam a sessão atual; respostas 401 continuam sendo
tratadas pelo interceptor global, que encerra uma sessão inválida.

Após cada atualização, o sistema compara `role_id`, `role_name` e o conjunto
ordenado de permissões. Quando encontra diferença, atualiza o contexto de
autenticação e o armazenamento local, recalcula menus, rotas e ações e exibe um
aviso global ao usuário.

O administrador também recebe, após salvar uma role, a informação de que
usuários conectados serão sincronizados ao retornar à aba ou em até 60
segundos.

## Teste manual com duas sessões

1. Entrar como administrador na sessão A.
2. Entrar como médico ou funcionário na sessão B, usando outro navegador ou
   perfil isolado.
3. Na sessão B, abrir uma tela que dependa de uma permissão da role.
4. Na sessão A, remover essa permissão e salvar.
5. Voltar à sessão B ou aguardar no máximo 60 segundos.
6. Confirmar o aviso de acessos atualizados.
7. Confirmar que menu, botão e rota protegida foram recalculados.
8. Tentar chamar a operação revogada e confirmar HTTP 403 no backend.

## Limitação e evolução futura

O intervalo de 60 segundos é adequado ao escopo do TCC e evita infraestrutura
adicional. Uma evolução possível é versionar a matriz RBAC e distribuir a nova
versão por WebSocket ou Server-Sent Events, eliminando o polling periódico.
