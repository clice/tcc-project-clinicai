# CHK-08 — Pacientes

**Data da revisão:** 14 de julho de 2026
**Branch de referência:** `feature/fix`
**Commit-base:** `db19a3ce9aa8ba6224f7039c5cf2e109c1d999df`
**Perfil do sistema:** protótipo acadêmico e demonstrativo

## 1. Resultado executivo

A CHK-08 consolidou no backend a regra de escopo dos pacientes e eliminou
atalhos que permitiam alterar vínculos clínicos apenas porque o formulário
ocultava ou desabilitava determinados campos.

A política autoritativa adotada é:

| Perfil | Pacientes visíveis |
| --- | --- |
| Administrador Master | Todos os pacientes |
| Funcionário da Clínica | Todos os pacientes vinculados à própria clínica |
| Médico | Somente pacientes atribuídos ao próprio médico |

A permissão de rota continua necessária, mas não substitui o escopo aplicado
pelo serviço. Parâmetros de busca, clínica ou médico apenas reduzem o conjunto
permitido; nunca ampliam o acesso.

Também foi definida uma política conservadora para transferência, adequada ao
escopo acadêmico:

- médico não transfere nem reatribui pacientes;
- funcionário pode reatribuir o médico apenas dentro da própria clínica;
- administrador pode transferir entre clínicas;
- qualquer alteração de clínica ou médico é bloqueada quando o paciente já
  possui exames, preservando os vínculos históricos herdados pelos exames.

## 2. Confronto com requisitos e regras de negócio

### RF20 — Cadastrar paciente

O cadastro exige clínica e médico responsável. O backend verifica que a clínica
está ativa, que o usuário selecionado possui role `doctor`, está ativo e pertence
à mesma clínica.

Quando o ator é médico, o paciente obrigatoriamente é cadastrado sob a própria
responsabilidade. Enviar o identificador de outro médico retorna HTTP 403.

### RF21 — Consultar pacientes

A API passou a aceitar os filtros:

- `search`;
- `clinic_id`;
- `doctor_id`;
- `include_inactive`.

A consulta respeita o escopo antes de aplicar os filtros. A interface também
expõe pesquisa por nome, CPF, médico ou clínica sobre o conjunto já autorizado.

### RF22 — Atualizar paciente

Dados cadastrais continuam editáveis conforme `patients:update`. Alterações de
clínica ou médico responsável passam pela política de reatribuição do backend.

### RF23 — Ativar ou inativar paciente

O status muda somente pelas rotas dedicadas. As operações são idempotentes e a
reativação exige que clínica e médico permaneçam ativos e compatíveis.

### RF24 — Validar dados do paciente

CPF é validado e permanece único por clínica. Data de nascimento futura ou
incompatível com o limite de idade adotado pelo projeto é rejeitada. Telefone,
e-mail, CEP e UF continuam normalizados.

A data de nascimento permanece opcional porque a monografia não a descreve como
campo obrigatório. Quando informada, sua validade é verificada.

### RF26 e RF27 — Clínica e médico responsável

Os dois vínculos permanecem obrigatórios no banco e na criação. O backend impede
limpeza explícita dos identificadores pelo PATCH.

### RN03, RN04 e RN07

- RN03: todo paciente permanece vinculado a uma clínica;
- RN04: todo paciente permanece vinculado a um médico responsável;
- RN07: CPF é único dentro da mesma clínica e pode existir em clínicas distintas.

### RN05 e RN06

Como os exames herdam clínica e médico do paciente na criação, a CHK-08 bloqueia
mudanças desses vínculos quando existe qualquer exame associado. Isso evita que
o paciente seja movido enquanto seu histórico permanece ligado a outra clínica
ou outro médico.

## 3. Correções implementadas

### 3.1 Listagem e acesso cruzado

`list_patients` agora recebe filtros explícitos e sempre aplica
`filter_query_by_user_scope` antes deles. São rejeitados:

- funcionário filtrando outra clínica;
- médico filtrando pacientes de outro médico;
- consulta detalhada, edição ou status de paciente fora do escopo.

### 3.2 Cadastro por médico

O backend não substitui silenciosamente um `doctor_id` forjado. Se o médico
informar outro responsável, a requisição retorna HTTP 403.

### 3.3 Reatribuição e transferência

Foi criada `validate_patient_assignment_change`, que centraliza as regras:

- médico: nenhuma troca de clínica ou responsável;
- funcionário: apenas reatribuição dentro da própria clínica;
- administrador: transferência permitida quando não existe histórico;
- qualquer ator: mudança bloqueada com HTTP 409 se houver exame.

O log de atualização marca `assignment_changed=true` e registra os valores
antigos e novos.

### 3.4 Reativação segura

`activate_patient` agora revalida:

- clínica existente e ativa;
- médico existente;
- role médica;
- médico ativo;
- médico pertencente à clínica do paciente.

### 3.5 Status idempotente

Ativar paciente já ativo ou inativar paciente já inativo não cria log duplicado
nem produz transição adicional.

### 3.6 Proteção do médico responsável

O módulo de usuários agora impede alterar role, clínica ou status de um médico
que ainda possui pacientes ativos. O administrador deve primeiro reatribuir ou
inativar esses pacientes.

### 3.7 Interface

A interface:

- não envia `clinic_id` nem `doctor_id` em edição feita por médico;
- apresenta o status como campo somente leitura;
- mostra uma descrição clara do escopo de cada role;
- disponibiliza busca por paciente, CPF, médico ou clínica;
- mantém a API como fonte autoritativa da decisão.

## 4. Testes automatizados

O arquivo `backend/tests/test_patients_api.py` cobre:

1. escopo do administrador, funcionário e médico;
2. filtros que não ampliam acesso;
3. bloqueio de consulta cruzada;
4. CPF único por clínica e aceito entre clínicas diferentes;
5. data de nascimento inválida;
6. clínica e médico incompatíveis ou inativos;
7. cadastro médico somente sob responsabilidade própria;
8. reatribuição por funcionário dentro da clínica;
9. bloqueio de reatribuição por médico;
10. transferência administrativa sem histórico;
11. bloqueio de transferência ou reatribuição com exames;
12. status dedicado, idempotência e reativação segura;
13. impossibilidade de limpar campos obrigatórios;
14. proteção de médicos com pacientes ativos.

O verificador `frontend/scripts/check-patient-contract.mjs` confronta os
contratos essenciais do backend e frontend.

## 5. Execução obrigatória no Docker

Na raiz do projeto:

```bash
chmod +x scripts/verify_chk08_patients.sh
./scripts/verify_chk08_patients.sh
```

O script executa:

1. build das imagens de backend e frontend;
2. testes específicos da CHK-08;
3. suíte completa do backend;
4. contratos RBAC, clínicas, usuários e pacientes;
5. build do frontend;
6. compilação dos módulos Python.

Resultado final esperado:

```text
[CHK-08] Validação concluída com sucesso.
```

## 6. Critério de conclusão

A CHK-08 é considerada concluída quando:

- CPF e data de nascimento são validados;
- clínica e médico responsável são obrigatórios e compatíveis;
- status muda somente pelas rotas dedicadas;
- médico consulta apenas pacientes atribuídos a ele;
- funcionário consulta apenas pacientes da própria clínica;
- filtros não ampliam o escopo;
- acesso cruzado retorna 403;
- médico não transfere ou reatribui paciente;
- reativação revalida clínica e médico;
- transferência com histórico é bloqueada;
- testes e verificadores terminam sem falhas.

## 7. Limites conscientes

- Não foi criada uma operação complexa de transferência institucional com
  custódia de histórico. O protótipo bloqueia a transferência quando existem
  exames, solução proporcional ao TCC.
- Paginação server-side continua fora desta rodada.
- Não houve alteração estrutural no banco, portanto nenhuma migration nova foi
  necessária.
