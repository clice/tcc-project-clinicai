# CHK-07 — Usuários

**Data da revisão:** 14 de julho de 2026
**Branch-base:** `feature/fix`
**Commit-base consultado no GitHub:** `c0d73489b95a4143af0f8f36611e2b1ca4b1e1b4`
**Escopo:** CPF/e-mail únicos, vínculo role × clínica, troca de role e clínica, autoedição, senha, status, último administrador e exposição de dados.

## 1. Resultado executivo

As invariantes do módulo de usuários passaram a ser validadas explicitamente no backend, sem depender das regras do formulário React. A API agora diferencia o payload administrativo do payload de autoedição, reserva alterações de status para endpoints dedicados e encerra sessões quando role ou clínica mudam.

A CHK também reduziu a exposição da rota auxiliar de médicos. `GET /users/doctors` devolve apenas `id` e `name`, suficientes para os seletores de pacientes, sem CPF, e-mail, telefone, status interno ou datas de acesso.

## 2. Regras consolidadas

### 2.1 CPF e e-mail

- CPF é normalizado para 11 dígitos e validado pelo dígito verificador.
- CPF permanece obrigatório e único na criação e na atualização.
- E-mail é normalizado para minúsculas.
- A busca de duplicidade usa comparação sem diferença entre maiúsculas e minúsculas, inclusive contra registros legados.
- As constraints únicas do banco continuam como segunda barreira para os valores normalizados.

### 2.2 Role e clínica

A função `validate_user_role_clinic_rules` é a fonte de verdade no backend:

- `admin_master`: `clinic_id` deve ser `null`;
- `doctor`: clínica ativa obrigatória;
- `clinic_staff`: clínica ativa obrigatória;
- clínica inexistente ou inativa é recusada;
- a mesma validação é aplicada na criação, troca de role, troca de clínica e reativação.

Ao mudar role ou clínica, `token_version` é incrementado. Dessa forma, access e refresh tokens anteriores deixam de ser válidos e o usuário precisa autenticar novamente com o novo contexto de segurança.

### 2.3 Autoedição

Foram separados dois schemas:

- `UserAdminUpdate`: dados cadastrais, `role_id` e `clinic_id`;
- `UserSelfUpdate`: somente nome, e-mail, CPF e telefone.

A rota `/users/me` usa `UserSelfUpdate`. Enviar `role_id`, `clinic_id` ou `status_id` retorna HTTP 422 com `extra_forbidden`, mesmo que o frontend seja contornado.

O administrador também não pode alterar a própria role ou clínica pela rota dinâmica. A própria senha deve ser trocada em `/users/me/password`.

### 2.4 Senha

- troca da própria senha exige a senha atual;
- a nova senha deve ser diferente;
- o bcrypt continua limitado a 72 bytes;
- a troca incrementa `token_version` e devolve um novo par de tokens somente à sessão que comprovou a senha atual;
- reset administrativo é permitido apenas para outro usuário;
- respostas e logs não incluem senha, hash ou tokens.

### 2.5 Status e último administrador

`status_id` foi removido do payload de atualização administrativa. O status muda somente por:

```text
PATCH /users/{user_id}/activate
PATCH /users/{user_id}/inactivate
```

Esses fluxos são idempotentes. Repetir uma operação já aplicada não cria outro log nem incrementa novamente a versão da sessão.

Antes de inativar um administrador ativo, o backend conta os administradores master ativos. A operação é recusada quando removeria o último. A mesma proteção é usada na troca de role para impedir o rebaixamento do último administrador ativo.

### 2.6 Exposição de dados

- rotas administrativas continuam retornando os dados necessários à gestão, inclusive CPF e e-mail;
- `/users/me` retorna somente os dados do próprio usuário;
- `/users/doctors` retorna apenas `id` e `name`;
- `password_hash` e `token_version` não fazem parte dos schemas públicos;
- o seletor de médicos continua limitado à clínica do usuário autenticado.

## 3. Ajustes no frontend

- status é selecionável na criação e somente leitura na edição;
- ativação e inativação continuam nos botões próprios da listagem;
- o payload de edição não envia `status_id`;
- role e clínica da própria conta ficam desabilitadas;
- redefinição administrativa da própria senha não é oferecida nessa tela;
- o botão de inativar não é exibido para o usuário autenticado;
- a tela avisa que mudar role ou clínica encerra as sessões do usuário.

Essas regras melhoram a experiência, mas não substituem as validações do backend.

## 4. Testes adicionados

`backend/tests/test_users_api.py` cobre:

1. criação, listagem, consulta, normalização e respostas seguras;
2. e-mail único sem diferença de caixa;
3. CPF único;
4. admin sem clínica e usuários clínicos com clínica ativa obrigatória;
5. promoção e rebaixamento entre roles;
6. troca de clínica e revogação de tokens antigos;
7. autoedição permitida e campos sensíveis rejeitados;
8. status apenas por rotas dedicadas e idempotência;
9. bloqueio de ativação em clínica inativa;
10. proteção do último administrador ativo;
11. seletor mínimo e isolado de médicos;
12. troca/reset de senha sem exposição de credenciais.

A suíte de schemas estritos passou a cobrir separadamente `UserAdminUpdate` e `UserSelfUpdate`.

## 5. Verificadores do frontend

Foi acrescentado:

```bash
npm run check:users
```

O verificador confronta schemas, rotas, service e interface para garantir:

- payloads administrativo e próprio separados;
- ausência de `status_id` no PATCH comum;
- opção de médico reduzida;
- unicidade case-insensitive do e-mail;
- validação de role/clínica;
- proteção do último administrador;
- revogação em troca de contexto;
- frontend sem envio de status na edição.

## 6. Execução obrigatória no Docker

Na raiz do projeto:

```bash
chmod +x scripts/verify_chk07_users.sh
./scripts/verify_chk07_users.sh
```

O script executa:

1. build das imagens de backend e frontend;
2. testes específicos da CHK-07;
3. suíte completa do backend;
4. contrato RBAC;
5. contrato de clínicas;
6. contrato de usuários;
7. build do frontend;
8. compilação Python.

O resultado final esperado é:

```text
[CHK-07] Validação concluída com sucesso.
```

## 7. Evidência desta revisão

No ambiente de análise:

```text
Testes específicos de usuários: 10 passed
Contrato RBAC: aprovado
Contrato de clínicas: aprovado
Contrato de usuários: aprovado
Compilação Python: aprovada
```

A suíte reconstruída contém 97 casos, todos aprovados em execuções segmentadas:

```text
10 testes específicos de usuários
25 testes de schemas estritos
10 testes de autenticação e sessão
12 testes de rotas, isolamento e sessão
40 testes restantes do backend
Total: 97 aprovados
```

A execução única ultrapassou o limite de tempo deste ambiente, mas todos os arquivos foram executados e aprovados nos grupos acima. A branch real possuía 95 casos antes desta rodada; com os 10 novos testes e um caso adicional de schema estrito, a execução Docker completa deve coletar 106 casos.

## 8. Critério de conclusão

A CHK-07 é considerada concluída quando:

- CPF e e-mail duplicados são rejeitados;
- a invariável role/clínica é aplicada em todos os fluxos;
- role/clínica alteradas revogam tokens anteriores;
- autoedição não aceita role, clínica ou status;
- status usa apenas endpoints dedicados;
- o último administrador ativo não pode ser removido;
- senhas e campos internos não aparecem em respostas ou logs;
- o seletor de médicos não expõe dados cadastrais desnecessários;
- `scripts/verify_chk07_users.sh` termina com sucesso.
