# CHK-09 — Exames e máquina de estados

**Data:** 14 de julho de 2026
**Branch de referência:** `feature/fix`
**Commit-base:** `f5c151c1de762ee7e4f3435027077e6a0d238688`

## 1. Objetivo

Formalizar no backend o ciclo de vida dos exames, impedir transições não previstas, tratar repetição e concorrência e manter uma única revisão médica. A autorização e a máquina de estados permanecem autoritativas no backend; o frontend somente reflete as ações permitidas.

## 2. Estados oficiais

A máquina contém exatamente os sete estados de exame:

- `pending`;
- `processing`;
- `awaiting_review`;
- `completed`;
- `completed_with_divergence`;
- `failed`;
- `canceled`.

O cadastro normal continua iniciando em `processing`, conforme RN08. `pending` permanece no catálogo para registros legados e para a transição explícita de início de processamento, além de poder ser cancelado conforme RN12.

## 3. Tabela autoritativa de transições

A tabela executável está em `backend/app/modules/exams/state_machine.py` e é verificada de forma parametrizada por `backend/tests/test_exam_state_machine.py`.

| Estado atual | Ação | Próximo estado |
|---|---|---|
| inexistente | `create` | `processing` |
| `pending` | `start_processing` | `processing` |
| `pending` | `cancel` | `canceled` |
| `processing` | `cancel` | `canceled` |
| `processing` | `analysis_succeeded` | `awaiting_review` |
| `processing` | `analysis_failed` | `failed` |
| `processing` | `replace_file` | `processing` |
| `failed` | `restore` | `processing` |
| `failed` | `replace_file` | `processing` |
| `canceled` | `restore` | `processing` |
| `awaiting_review` | `review_confirm` | `completed` |
| `awaiting_review` | `review_divergence` | `completed_with_divergence` |

Toda combinação ausente retorna `409 Conflict`. Os estados `completed` e `completed_with_divergence` são terminais.

## 4. Repetição e idempotência

- repetir `cancel` quando o exame já está `canceled` devolve o estado atual e não cria outro log;
- repetir `restore` quando o exame já chegou a `processing` devolve o estado atual e não cria outro log;
- repetir `analyze` depois de uma análise concluída devolve a análise já persistida;
- repetir `analyze` enquanto a inferência está em andamento retorna `409` e não chama o serviço de IA novamente;
- repetir a revisão médica retorna `409`, preservando uma única conclusão clínica.

## 5. Concorrência

A migration `e4f6a8b0c213` adiciona aos exames:

- `analysis_in_progress`;
- `analysis_started_at`.

O disparo da IA usa atualização condicional atômica para adquirir o claim. Cancelamento, restauração, persistência do resultado e revisão usam bloqueio de linha no PostgreSQL. Com isso:

- duas requisições de análise não executam duas inferências;
- duas revisões não geram duas conclusões;
- cancelamento concorrente com retorno da IA não permite que o resultado tardio sobrescreva `canceled`;
- a unicidade de `ai_analysis.exam_id` permanece como última barreira no banco.

## 6. Cancelamento, falha e restauração

- somente `pending` e `processing` podem ser cancelados;
- somente `canceled` e `failed` podem ser restaurados;
- restauração sempre retorna a `processing`;
- a restauração exige que o arquivo físico ainda exista;
- exame com análise concluída não pode retornar ao processamento;
- substituição de imagem é permitida somente em `processing` ou `failed` e é bloqueada durante inferência.

## 7. Revisão médica única

A revisão exige simultaneamente:

- role `doctor`;
- permissão `exams:review`;
- acesso ao exame pelo escopo do médico responsável;
- estado `awaiting_review`;
- análise de IA vinculada.

Concordância leva a `completed`; divergência leva a `completed_with_divergence`. Ambos são estados finais.

## 8. Histórico de status e auditoria

RN24 é atendida pelo histórico autorizado de auditoria do próprio exame, em vez de uma tabela adicional. Toda transição grava de forma padronizada:

- estado e ID anteriores;
- estado e ID novos;
- `transition_action`;
- usuário ou ação do sistema;
- data/hora do evento.

Repetições idempotentes não geram eventos duplicados.

## 9. Rastreabilidade RN07–RN25

| RN | Evidência principal |
|---|---|
| RN07 | teste de CPF único por clínica da CHK-08 |
| RN08 | `create -> processing` na tabela automatizada |
| RN09 | `analysis_succeeded -> awaiting_review` |
| RN10 | rota e service de revisão exclusivos de médico |
| RN11 | estados finais sem transições de saída |
| RN12 | cancelamento e restauração testados |
| RN13 | `failed -> processing` por restauração |
| RN14 | toda transição não declarada retorna `409` |
| RN15 | revisão confirma ou registra divergência |
| RN16 | FK e unicidade de `AIAnalysis.exam_id` |
| RN17 | `model_name` e `model_version` obrigatórios |
| RN18 | confiança persistida |
| RN19 | caminho Grad-CAM persistido quando fornecido |
| RN20 | timestamp de criação da análise |
| RN21 | transições críticas auditadas na mesma transação |
| RN22 | suíte de autenticação/usuários inativos |
| RN23 | matriz automatizada de RBAC |
| RN24 | histórico de status por auditoria do exame |
| RN25 | cancelamento lógico, sem exclusão física |

O teste CHK-09 também exige que a matriz de rastreabilidade contenha todas as regras de RN07 a RN25 sem lacunas.

## 10. Frontend

- foi adicionado `npm run check:exams`;
- o botão de análise aparece somente em `processing`, com permissão adequada e sem claim ativo;
- durante a análise, a interface bloqueia repetição visual;
- cancelar aparece apenas para `pending`/`processing`;
- restaurar aparece para `canceled`/`failed`;
- revisão continua restrita a `awaiting_review`;
- logs de depuração do `ExamForm` foram removidos.

## 11. Validações realizadas na preparação

Executadas com sucesso neste ambiente:

```text
python -m pytest -q tests/test_exam_state_machine.py
10 passed

python -m compileall -q app tests/test_exam_state_machine.py
aprovado

node frontend/scripts/check-exam-state-contract.mjs
Contrato de exames coerente: 7 estados, transições, repetição e concorrência validados.

git diff --check
aprovado
```

A suíte completa, o build do Vite e a migration PostgreSQL devem ser validados no Docker da máquina do projeto pelo script entregue.

## 12. Limitação conhecida

O claim impede concorrência imediata, mas esta checagem não introduz um reconciliador periódico para processos interrompidos que deixem `analysis_in_progress=true`. Recuperação por SLA e worker de reconciliação permanecem como melhoria de confiabilidade posterior; uma falha tratada normalmente libera o claim e move o exame para `failed`.
