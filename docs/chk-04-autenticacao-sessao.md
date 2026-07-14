# CHK-04 — Autenticação e sessão

**Escopo:** versão acadêmica e demonstrativa do ClinicAI  
**Objetivo:** validar login, expiração, refresh token, logout, `token_version`, alteração de senha, bloqueio por usuário/clínica inativos e logs de tentativa.

## Decisões proporcionais ao projeto acadêmico

- Foi mantido JWT com `token_version`, sem lista distribuída de revogação.
- O refresh token passou a ser rotacionado: cada renovação incrementa `token_version` e invalida o par anterior.
- Logout, troca/reset de senha e inativação de usuário encerram tokens já emitidos.
- A inativação de uma clínica incrementa a versão de sessão dos usuários vinculados, impedindo que tokens antigos voltem a funcionar após a reativação.
- Rate limiting não foi implementado nesta etapa. Para o perfil exclusivamente local e acadêmico, ele permanece uma proteção complementar e não bloqueia a versão candidata. Antes de exposição pública, pode ser aplicado no proxy ou backend.

## Correções realizadas

1. A política de sessão agora valida, de forma única, o status do usuário e da clínica no login, refresh e rotas autenticadas.
2. Tokens com `sub` malformado retornam `401`, sem gerar erro interno.
3. Login com e-mail inexistente e senha incorreta devolve a mesma resposta pública e executa bcrypt no caminho de conta inexistente.
4. Refresh token é de uso único dentro da versão de sessão atual.
5. A rota `/users/me/password` passou a ser alcançável antes da rota dinâmica `/{user_id}`.
6. `/users/me` recebeu schema explícito de resposta e não retorna `password_hash`, `token_version` ou tokens.
7. A troca da própria senha exige a senha atual, inclusive para `admin_master`, e devolve um novo par de tokens apenas para a sessão que comprovou a senha.
8. O reset administrativo de senha continua permitido para outro usuário e encerra as sessões do alvo.
9. Dados de auditoria são sanitizados para remover campos conhecidos de senha, token, autorização e chave secreta.
10. O frontend salva o novo par de tokens devolvido após a troca da própria senha.

## Casos automatizados

A suíte `backend/tests/test_authentication_session_api.py` cobre:

- login válido;
- login inválido com e-mail existente e inexistente;
- respostas equivalentes contra enumeração direta de contas;
- access token ausente, expirado, de tipo incorreto e com `sub` inválido;
- refresh token expirado ou de tipo incorreto;
- rotação de refresh token;
- logout e invalidação de access/refresh;
- usuário inativo;
- clínica inativa;
- inativação e reativação de usuário sem ressurreição do token antigo;
- inativação e reativação de clínica sem ressurreição do token antigo;
- troca da própria senha com senha atual obrigatória;
- reset administrativo de senha;
- ausência de senha, hash e tokens em respostas públicas e logs.

## Evidência executada

```bash
cd backend
python -m pytest -q
```

Resultado obtido nesta revisão:

```text
71 passed, 47 warnings in 28.63s
```

Os avisos observados são de depreciação interna do `python-jose` e do adaptador SQLite usado nos testes; não representam falha dos casos de autenticação.

Validação sintática do serviço frontend alterado:

```bash
node --check frontend/src/services/userService.js
```

Resultado: aprovado.

## Critério do CHK-04

- `401` para token ausente, inválido, expirado, reutilizado ou com `token_version` antigo;
- `403` para credenciais corretas associadas a usuário ou clínica inativos;
- logout e alterações críticas encerram as sessões esperadas;
- senhas, hashes, access tokens e refresh tokens não são persistidos nos logs;
- respostas públicas de perfil/usuário não expõem campos internos de credencial;
- rate limiting permanece complementar para o ambiente local acadêmico.

**Situação:** concluído para o escopo acadêmico local.
