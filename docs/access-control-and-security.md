# Controle de Acesso e Segurança

## Escopo

O ClinicAI é um protótipo acadêmico destinado à demonstração local. As proteções descritas
neste documento reduzem riscos técnicos no protótipo, mas não representam certificação,
auditoria profissional de segurança ou autorização para uso clínico real.

## Princípio de autoridade

O backend é a fonte autoritativa das regras de autenticação, autorização e escopo. Ocultar
menus, rotas ou botões no frontend melhora a interface, mas não substitui a validação da API.

Toda operação protegida deve ser recusada pelo backend quando o usuário não possuir papel,
permissão, vínculo institucional ou responsabilidade compatível.

## Autenticação e sessões

O backend utiliza tokens JWT de acesso e atualização associados ao `token_version` do usuário.

- login, atualização da sessão e rotas autenticadas verificam usuário e clínica ativos;
- *refresh tokens* são rotacionados;
- logout, troca ou redefinição de senha e inativação invalidam sessões anteriores;
- a troca da própria senha exige a senha atual, inclusive para o Administrador Master;
- respostas e logs não devem expor senhas, hashes, tokens ou segredos;
- credenciais acadêmicas não devem ser reutilizadas fora da demonstração local.

## Papéis e escopos

### Administrador Master

O Administrador Master gerencia componentes estruturais e operacionais da plataforma, como
clínicas, perfis, permissões, status, auditoria e usuários conforme as regras aplicáveis.

Na matriz padrão, o papel não recebe permissões clínicas de criação, leitura, atualização,
download, revisão ou análise de exames. O acesso administrativo não funciona como *bypass* para
resultados da IA ou revisões médicas.

O administrador pode visualizar listagens estritamente operacionais quando a permissão
correspondente estiver presente, mas não recebe o rótulo da IA nem acesso ao conteúdo clínico
detalhado.

### Gestor de clínica

O gestor permanece limitado à própria clínica. A matriz padrão permite operações
administrativas sobre usuários e pacientes e acesso à listagem operacional de exames.

O gestor não recebe `exams:read` nem `ai_analysis:read`. Assim, não acessa a tela clínica
detalhada, a imagem original, o Grad-CAM ou o resultado da IA nas listagens.

Existe uma autorização explícita e limitada para gerar o relatório PDF de exames concluídos ou
concluídos com divergência pertencentes à própria clínica. Essa exceção não amplia as demais
permissões clínicas.

### Médico

O médico permanece limitado à própria clínica e aos pacientes e exames sob sua
responsabilidade.

A revisão exige simultaneamente:

- papel `doctor`;
- permissão `exams:review`;
- vínculo do exame com o próprio médico;
- vínculo do exame com a própria clínica;
- estado compatível com revisão.

O rótulo da IA aparece nas listagens apenas para médicos autorizados, em exames nos estados
compatíveis com resultado disponível. A confirmação ou divergência da revisão permanece
auditável.

## Listagem, detalhe e relatório

As capacidades são deliberadamente separadas:

- `exams:list`: permite obter uma listagem operacional dentro do escopo;
- `exams:read`: permite acessar o detalhe clínico autorizado;
- `ai_analysis:read`: permite acessar o resultado e os recursos da análise;
- autorização de relatório: permite gerar o PDF somente ao médico responsável ou ao gestor da
  mesma clínica, em estados finais imprimíveis.

O fato de um papel poder listar exames não implica acesso ao detalhe, às imagens ou ao resultado
da IA.

## Catálogos fechados

Papéis, status e permissões possuem identificadores técnicos utilizados pelo código.

- identificadores oficiais não podem ser criados ou renomeados livremente pela API;
- mudanças estruturais devem ser implementadas por *migrations* Alembic;
- textos de exibição e descrições podem ser editados quando a API permitir;
- o catálogo de permissões está em
  `backend/app/modules/permissions/catalog.py`.

## Bootstrap e matriz RBAC

O primeiro `bootstrap` inicializa somente papéis ainda não configurados. O campo
`roles.permissions_initialized` permite preservar inclusive um papel deliberadamente deixado
sem permissões.

Reinicializações posteriores não reconciliam automaticamente a matriz. Mudanças oficiais para
bancos existentes devem ser implementadas por *migrations* de dados.

A restauração integral da matriz padrão é uma ação administrativa explícita:

```bash
docker compose exec backend python -m app.modules.role_permissions.reconcile \
  --confirm RECONCILE_RBAC
```

Esse comando pode remover customizações e não é executado pelo *entrypoint*.

## Validação das requisições

Schemas de entrada protegidos devem rejeitar campos desconhecidos ou imutáveis antes da regra
de negócio. O projeto utiliza modelos estritos com `extra="forbid"` nos contratos
correspondentes.

Arquivos de exame também passam por validações de:

- tamanho;
- extensão declarada;
- MIME e assinatura real;
- estrutura de JPEG ou PNG;
- dimensões e quantidade máxima de pixels;
- nome físico gerado pelo backend.

## Arquivos clínicos

Imagens originais e mapas Grad-CAM não são publicados como diretórios estáticos.

O acesso ocorre por rotas autenticadas que validam:

- papel e permissão;
- escopo da clínica;
- responsabilidade médica quando aplicável;
- vínculo do arquivo com o exame;
- caminho relativo canônico;
- ausência de travessia de diretórios;
- ausência de links simbólicos;
- existência do arquivo.

O serviço de IA devolve o mapa em Base64, acompanhado de tipo MIME e SHA-256. O backend valida
esses dados antes de persistir o arquivo na área operacional.

## Atualização de permissões no frontend

O frontend consulta `/auth/me` para renovar o estado do usuário:

- quando a janela recupera o foco;
- quando a aba volta a ficar visível;
- periodicamente durante a sessão.

Essa atualização recalcula menus, rotas e ações. Mesmo antes da atualização visual, uma
permissão revogada já deve ser recusada pelo backend.

## Auditoria

Operações relevantes registram informações de auditoria compatíveis com o protótipo. Os logs
não devem armazenar credenciais, tokens, hashes de senha ou segredos.

A existência de auditoria técnica não equivale a trilha certificada para sistemas clínicos de
produção.

## Regressão técnica

```bash
python3 scripts/check_dependency_locks.py
docker compose config --quiet

docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m pytest -q

docker compose run --rm --no-deps frontend npm run lint
docker compose run --rm --no-deps frontend npm run build

docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  ai -m unittest discover -s tests -p 'test_*.py' -v

python3 -m unittest tests.test_model_distribution
```

Os testes constituem regressão técnica do protótipo. Eles não substituem teste de intrusão,
auditoria profissional, avaliação de privacidade, validação clínica ou certificação
regulatória.
