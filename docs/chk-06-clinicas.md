# CHK-06 — Clínicas

**Data da revisão:** 14 de julho de 2026  
**Branch-base:** `feature/fix`  
**Commit-base consultado no GitHub:** `00e16cb58851a6670b7b58e693d2c1ee349b8622`  
**Perfil do sistema:** protótipo acadêmico e demonstrativo

## 1. Escopo verificado

A checagem cobriu:

- cadastro, consulta, atualização e exclusão lógica de clínicas;
- status ativo/inativo;
- CNPJ, e-mail, telefones e endereço;
- associação de usuários;
- bloqueio de clínica inativa;
- leitura e edição da própria clínica;
- isolamento entre clínicas;
- auditoria de criação, edição e mudança de status;
- efeitos da inativação sobre usuários, pacientes e exames.

O sistema não expõe exclusão física de clínica. O `DELETE` permanece indisponível e a remoção operacional ocorre por inativação, preservando os vínculos e o histórico acadêmico.

## 2. Achados e correções

### 2.1 Status podia ser alterado pelo PATCH genérico

`ClinicUpdate` aceitava `status_id`. Isso permitia mudar o status por `PATCH /clinics/{id}` ou `PATCH /clinics/me`, contornando as rotas dedicadas de ativação e inativação.

Além de permitir que um usuário com `clinics:update_profile` alterasse o status da própria clínica, a reativação pelo PATCH genérico poderia fazer tokens antigos voltarem a funcionar, pois a invalidação de `token_version` existia apenas em `/inactivate`.

Correção:

- `status_id` foi removido de `ClinicUpdate`;
- mudança de status ocorre somente por `/activate` e `/inactivate`;
- o formulário administrativo deixa o status editável apenas na criação;
- o status do perfil próprio é somente leitura.

### 2.2 E-mail não era normalizado de modo uniforme

O frontend enviava e-mail em minúsculas, mas chamadas diretas à API poderiam persistir variações de caixa. A busca de duplicidade também era sensível a caixa em algumas bases.

Correção:

- criação e atualização normalizam o e-mail para minúsculas;
- a verificação de duplicidade usa comparação case-insensitive;
- registros antigos com letras maiúsculas também são confrontados.

### 2.3 Resposta de `/clinics/me` não achatava o status

A rota devolvia o objeto ORM diretamente. Como `ClinicResponse` espera `status_name` e `status_display_name` no nível principal, esses campos poderiam aparecer como `null`, embora o relacionamento estivesse carregado.

Correção:

- `/clinics/me` usa `build_clinic_response`;
- usuário sem vínculo recebe a barreira explícita de clínica obrigatória.

### 2.4 Efeitos da inativação não estavam completamente registrados

A inativação já encerrava as sessões dos usuários vinculados, mas o log não deixava explícito quantos usuários, pacientes e exames estavam associados.

Correção:

- o evento de auditoria registra as quantidades associadas;
- registra que pacientes e exames foram preservados;
- inativação e ativação repetidas são idempotentes, evitando logs e incrementos de sessão duplicados.

### 2.5 Perfil da clínica não era consumido pelo frontend

As permissões `clinics:read_profile` e `clinics:update_profile` e as rotas `/clinics/me` existiam, mas não havia tela que as utilizasse.

Correção:

- foi criado o cartão “Minha clínica” no perfil do usuário;
- leitura e edição obedecem às permissões retornadas pelo backend;
- status é exibido como somente leitura;
- CNPJ, contatos e endereço usam as mesmas normalizações do cadastro administrativo.

## 3. Regras consolidadas

- Administrador Master cria, lista, consulta, atualiza, ativa e inativa clínicas.
- Médico e Funcionário da Clínica consultam e atualizam somente a clínica vinculada, quando possuírem as permissões de perfil.
- Usuário comum não acessa `GET/PATCH /clinics/{id}` nem operações administrativas.
- `clinic_id` enviado para recursos relacionados continua validado no backend.
- Usuário não administrador deve estar associado a uma clínica ativa.
- Clínica inativa bloqueia login e sessão dos usuários vinculados.
- Nova associação de usuário a clínica inativa é recusada.
- Criação ou transferência de paciente/exame para clínica inativa é recusada.
- Pacientes e exames existentes não são apagados nem têm o próprio status alterado pela inativação da clínica.
- O Administrador Master continua capaz de consultar os registros preservados para fins administrativos e de auditoria.

## 4. Cobertura automatizada adicionada

`backend/tests/test_clinics_api.py` cobre:

1. CRUD administrativo com normalização de CNPJ, e-mail, telefones, CEP e UF;
2. listagem e consulta por ID;
3. duplicidade de CNPJ;
4. duplicidade de e-mail sem diferença entre maiúsculas e minúsculas;
5. validações inválidas de documento, contato e endereço;
6. rejeição de status pertencente a outro escopo;
7. ausência de `DELETE` físico;
8. rejeição de `status_id` no PATCH genérico;
9. ativação e inativação pelas rotas dedicadas;
10. invalidação de sessões;
11. bloqueio de login de usuário da clínica inativa;
12. recusa de associação de usuário, paciente e exame à clínica inativa;
13. preservação dos pacientes e exames existentes;
14. quantidades registradas na auditoria;
15. idempotência da inativação;
16. leitura e edição da própria clínica;
17. resposta com status achatado;
18. bloqueio de consulta e alteração de outra clínica;
19. bloqueio das operações administrativas para usuário comum.

O verificador `frontend/scripts/check-clinic-contract.mjs` confronta o contrato de status, serviços, perfil próprio e efeitos auditáveis entre frontend e backend.

## 5. Evidência executada neste ambiente

Testes específicos:

```text
10 passed, 26 warnings
```

Suíte disponível no pacote local usado para preparar a alteração:

```text
86 passed, 73 warnings
```

O pacote local não continha nove testes de CHK-01 a CHK-03 que já estão na branch atual do GitHub. Como a branch `feature/fix` possuía 85 testes aprovados antes desta alteração, o resultado esperado após aplicar a CHK-06 é **95 testes aprovados**, desde que não existam mudanças concorrentes. Esse número deve ser confirmado no Docker da máquina de desenvolvimento.

Também foram aprovados:

```text
node frontend/scripts/check-clinic-contract.mjs
node --check frontend/src/services/clinicService.js
node --check frontend/scripts/check-clinic-contract.mjs
```

## 6. Comandos obrigatórios no Ubuntu com Docker

Na raiz do projeto:

```bash
chmod +x scripts/verify_chk06_clinics.sh
./scripts/verify_chk06_clinics.sh
```

O script executa:

- build das imagens de backend e frontend;
- testes específicos da CHK-06;
- suíte completa do backend;
- verificadores de RBAC;
- verificador do contrato de clínicas;
- build do frontend;
- compilação dos módulos Python.

## 7. Resultado esperado

```text
Testes específicos: 10 passed
Suíte completa na branch atual: aproximadamente 95 passed
RBAC: sete verificadores aprovados
Contrato de clínicas: aprovado
Build do frontend: concluído
Compileall: concluído sem erro
```

Avisos de depreciação do `python-jose`, `passlib` ou adaptador SQLite não bloqueiam esta checagem. Erros, testes `failed` ou falha de build bloqueiam o encerramento.

## 8. Situação

**CHK-06 concluída em código para o escopo acadêmico**, pendente apenas da execução do script Docker na cópia local atualizada da branch `feature/fix`.
