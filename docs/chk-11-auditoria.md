# CHK-11 — Auditoria e rastreabilidade

**Data da revisão:** 14 de julho de 2026
**Branch de referência:** `feature/fix`
**HEAD analisado:** `a6a0e2a907e7db06394b3e473ab8a08a1ca96bd4`
**Perfil do sistema:** protótipo acadêmico e demonstrativo

## 1. Resultado executivo

A base de auditoria do ClinicAI já estava bem distribuída pelos serviços de autenticação, usuários, clínicas, pacientes, exames, IA e RBAC. O padrão predominante é correto: `create_audit_log()` não realiza commit por padrão, de modo que a alteração de domínio e o respectivo log participam da mesma transação.

A revisão encontrou cinco lacunas que impediam considerar a matriz ação × log completa:

1. o upload inicial do exame aparecia apenas dentro do evento de criação, sem ação `upload` própria;
2. o claim que inicia a inferência alterava `analysis_in_progress`, realizava commit e não gerava log;
3. a sanitização removia somente um conjunto curto de chaves exatas e não tratava descrições, `raw_response`, caminhos internos ou imagens em Base64;
4. o evento de revisão registrava a transição de status, mas não os valores antigos e novos de `findings`, `conclusion` e `reviewed_at`;
5. o evento de download persistia o caminho físico interno do arquivo.

A correção proposta fecha essas lacunas sem migration, sem nova dependência e sem alteração de frontend.

## 2. Confirmação da CHK-10

A branch `feature/fix` está três commits à frente do commit-base da CHK-09 (`5394a4885d3bdacf94552a784fbf5e16bfd59658`) e contém os oito arquivos previstos para a CHK-10. O HEAD atual é `a6a0e2a907e7db06394b3e473ab8a08a1ca96bd4`, com a documentação e o script de verificação da etapa.

Não havia execução de GitHub Actions associada ao HEAD. Portanto, esta confirmação comprova a presença das alterações na branch, mas não substitui o resultado do script Docker executado no ambiente local.

## 3. Política de auditoria adotada

### 3.1 Regra transacional

- Alterações de banco e logs usam a mesma `Session` e o mesmo commit.
- Um erro ao construir ou persistir o log impede o commit da ação.
- Operações que possuem rollback explícito, como sincronização de RBAC e claim de IA, restauram integralmente o estado anterior.
- Falha de login é uma exceção consciente: não existe alteração de domínio a desfazer, então o próprio evento é persistido para preservar a tentativa inválida.
- A chamada HTTP ao serviço de IA não pode permanecer dentro de uma transação longa. O fluxo é dividido em eventos auditáveis: início/claim, sucesso ou falha.

### 3.2 Semântica do download

O evento `download` significa **acesso autorizado e resposta de arquivo preparada**. O servidor não consegue garantir atomicamente que o cliente recebeu todos os bytes depois que a resposta começou a ser transmitida. A redação do log evita afirmar uma transferência completa que o backend não consegue comprovar.

### 3.3 Dados permitidos e proibidos

Podem ser registrados:

- identificadores de usuário, clínica e entidade;
- ação, data e descrição operacional;
- campos antigos e novos necessários à rastreabilidade;
- status, versão do modelo, classe, confiança, dimensões, tamanho e SHA-256;
- nome físico aleatório do arquivo, quando necessário para correlação.

Não podem ser registrados:

- senha, hash, senha atual ou nova senha;
- access token, refresh token, ID token, bearer token, cookie ou segredo;
- conteúdo binário, Base64, data URI ou imagem original/Grad-CAM;
- `raw_response` integral do serviço de IA;
- caminhos físicos internos de arquivos ou Grad-CAM.

## 4. Matriz ação × log

| Área | Ação de domínio | Ação de auditoria | Entidade | Dados antigos/novos | Atomicidade | Estado após CHK-11 |
|---|---|---|---|---|---|---|
| Autenticação | Login válido | `login_success` | `auth` | e-mail e horário de acesso | mesmo commit de `last_access_at` | Coberto |
| Autenticação | Credencial inválida | `login_failed` | `auth` | e-mail normalizado, sem senha | log independente; não há mutação de domínio | Coberto |
| Autenticação | Conta/clínica inativa | `login_failed` | `auth` | motivo operacional, sem credencial | log independente | Coberto |
| Sessão | Renovar tokens | `refresh_token` | `auth` | nova `token_version`, sem token | mesmo commit | Coberto |
| Sessão | Logout | `logout` | `auth` | nova `token_version`, sem token | mesmo commit | Coberto |
| Usuários | Criar | `create` | `user` | `new_data` cadastral, sem senha/hash | mesmo commit | Coberto |
| Usuários | Editar perfil/admin | `update` | `user` | `old_data` e `new_data` | mesmo commit | Coberto |
| Usuários | Trocar/resetar senha | `update_password` | `user` | marcador e `token_version` | mesmo commit | Coberto |
| Usuários | Ativar/inativar | `change_status_*` | `user` | status anterior/novo | mesmo commit | Coberto |
| Clínicas | Criar/editar | `create` / `update` | `clinic` | dados anteriores/novos | mesmo commit | Coberto |
| Clínicas | Ativar/inativar | `change_status_*` | `clinic` | status e sessões invalidadas | mesmo commit | Coberto |
| Pacientes | Criar/editar | `create` / `update` | `patient` | dados anteriores/novos | mesmo commit | Coberto |
| Pacientes | Ativar/inativar | `change_status_*` | `patient` | status anterior/novo | mesmo commit | Coberto |
| Exames | Criar registro | `create` | `exam` | vínculos, metadados e status inicial | mesmo commit da criação | Coberto |
| Arquivos | Upload inicial | `upload` | `exam` | MIME real, tamanho, dimensões, hash e nome aleatório | mesmo commit da criação | Corrigido |
| Exames | Editar metadados | `update` | `exam` | metadados anteriores/novos | mesmo commit | Coberto |
| Exames | Cancelar/restaurar | `cancel_exam` / `restore_exam` | `exam` | status anterior/novo e ação de transição | mesmo commit | Coberto |
| Arquivos | Substituir imagem | `upload` | `exam` | metadados antigos/novos, sem bytes/caminho | commit antes de remover versão antiga | Coberto |
| Arquivos | Download autorizado | `download` | `exam` | nome aleatório e MIME, sem caminho físico | log confirma autorização/preparo | Corrigido |
| IA | Adquirir claim/iniciar | `run_ai_analysis` | `exam` | fase `started`, horário e marcador | mesmo commit do claim | Corrigido |
| IA | Concluir análise | `run_ai_analysis` | `ai_analysis` e `exam` | resultado seguro e transição para revisão | mesmo commit da análise e status | Coberto |
| IA | Falhar | `ai_analysis_failed` | `exam` | status anterior/novo; erro sanitizado | mesmo commit da falha | Corrigido |
| IA | Editar análise | `update` | `ai_analysis` | valores anteriores/novos; presença de artefatos, sem conteúdo | mesmo commit | Corrigido |
| Revisão | Confirmar/divergir | `review_exam` | `exam` | status, achados, conclusão, médico e horário | mesmo commit da revisão | Corrigido |
| RBAC | Editar role | `update` | `role` | dados anteriores/novos | mesmo commit | Coberto |
| RBAC | Editar permissão | `update` | `permission` | dados anteriores/novos | mesmo commit | Coberto |
| RBAC | Criar/editar/remover vínculo | `create` / `update` / `delete` | `role_permission` | role e permissão anteriores/novas | mesmo commit | Coberto |
| RBAC | Sincronizar matriz | `update` | `role_permission` | conjunto antigo/novo de IDs | transação única com rollback explícito | Coberto |
| Configuração | Editar catálogo de status | `update` | `status` | dados anteriores/novos | mesmo commit | Coberto |

## 5. Alterações técnicas

### 5.1 Sanitização central

`sanitize_audit_data()` passa a:

- percorrer dicionários, listas e tuplas recursivamente;
- identificar chaves de credenciais, tokens, segredos, conteúdo binário, Base64, respostas brutas e caminhos internos;
- preservar `token_version`, que é metadado de revogação e não uma credencial;
- redigir bearer tokens, atribuições textuais de senha/segredo, data URIs e sequências longas compatíveis com Base64;
- sanitizar também `description` e `user_agent` antes da persistência.

### 5.2 Upload inicial

A criação passa a produzir dois eventos na mesma transação:

1. `create/exam`, para o registro e os vínculos;
2. `upload/exam`, para o arquivo validado.

Nenhum evento recebe bytes, nome original ou caminho físico.

### 5.3 Claim da IA

O claim atômico continua usando atualização condicional, mas o commit somente ocorre depois de criar o evento `run_ai_analysis` com `phase=started`. Se a criação do log falhar, o rollback remove o marcador de execução e evita exame preso sem histórico.

### 5.4 Resultado e falha da IA

- O log de sucesso registra apenas metadados do modelo e `gradcam_available`.
- Atualizações registram `gradcam_updated`, `gradcam_available`, `raw_response_updated` e `raw_response_available`, nunca o conteúdo ou caminho.
- Mensagens de falha passam pela redação textual central antes de serem armazenadas.

### 5.5 Revisão médica

O evento de revisão inclui:

- status anterior e novo;
- `findings` e `conclusion` anteriores e novos;
- `reviewed_by_id` anterior e novo;
- `reviewed_at` anterior e novo;
- presença ou ausência de divergência.

Os testes devem utilizar somente dados sintéticos ou anonimizados.

## 6. Testes automatizados

O arquivo `backend/tests/test_audit_integrity.py` verifica:

1. remoção recursiva de senhas, tokens, segredos, imagens, Base64, respostas brutas e caminhos;
2. login bem-sucedido e falho sem vazamento de credenciais;
3. eventos distintos de criação e upload;
4. download sem caminho físico no log;
5. rollback conjunto do claim e de seu log;
6. logs de sucesso, falha e edição da IA sem conteúdo bruto/Grad-CAM;
7. revisão médica com valores antigos e novos;
8. edição de paciente sem commit parcial quando o log falha;
9. sincronização de RBAC com rollback integral quando a auditoria falha.

A suíte PostgreSQL de concorrência permanece necessária para confirmar uma única aquisição do claim e uma única revisão/log em sessões reais independentes.

## 7. Execução no Docker

Na raiz do repositório:

```bash
chmod +x scripts/verify_chk11_audit.sh
./scripts/verify_chk11_audit.sh
```

O script:

- valida o Compose;
- constrói backend e frontend;
- executa os testes específicos da CHK-11 e os testes acumulados de arquivo/histórico;
- cria um banco PostgreSQL temporário sem apagar o volume principal;
- reexecuta os testes concorrentes da CHK-09;
- executa toda a suíte backend;
- revalida o contrato RBAC, o build do frontend e `compileall`.

## 8. Critério de conclusão

A CHK-11 é considerada concluída quando:

- a matriz ação × log não contém lacunas críticas;
- cada mutação persistente relevante possui evento correspondente;
- claim, resultado, falha e revisão da IA são rastreáveis;
- criação e upload são eventos distintos;
- mudanças de domínio não são confirmadas sem o respectivo log;
- testes de rollback demonstram ausência de estado parcial;
- `old_data` e `new_data` representam a alteração realizada;
- senha, token, segredo, Base64, imagem, `raw_response` e caminho físico não aparecem nos logs;
- o script Docker termina com `[CHK-11] Validação concluída com sucesso.`

## 9. Inventário da entrega

### Arquivos modificados

- `backend/app/modules/audit_logs/service.py`
- `backend/app/modules/ai_analysis/service.py`
- `backend/app/modules/exams/service.py`

### Arquivos novos

- `backend/tests/test_audit_integrity.py`
- `docs/chk-11-auditoria.md`
- `scripts/verify_chk11_audit.sh`

### Arquivos apagados

- nenhum.

### Migration

- nenhuma.

### Dependências

- nenhuma.

### Frontend

- nenhuma alteração.

## 10. Limitações conscientes

- A auditoria do protótipo permanece no mesmo banco relacional da aplicação; armazenamento imutável/WORM, assinatura criptográfica e envio a SIEM ficam fora do escopo acadêmico atual.
- A camada de auditoria não deve ser usada como cópia integral de imagens, respostas da IA ou prontuário.
- O evento de download comprova autorização e preparação da resposta, não recepção integral no cliente.
- IP e User-Agent auxiliam a rastreabilidade, mas não constituem prova inequívoca de identidade.
