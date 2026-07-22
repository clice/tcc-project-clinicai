# Controle de acesso e segurança do ClinicAI

## Escopo

O ClinicAI é um protótipo acadêmico destinado à demonstração local. As
proteções descritas neste documento reduzem riscos no protótipo, mas não
representam validação ou certificação para uso clínico real.

## Autenticação e sessões

O backend utiliza tokens JWT de acesso e atualização associados ao
`token_version` do usuário.

- login, refresh e rotas autenticadas validam usuário e clínica ativos;
- refresh tokens são rotacionados;
- logout, troca ou reset de senha e inativação invalidam sessões anteriores;
- respostas e logs não devem expor senhas, hashes, tokens ou segredos;
- a troca da própria senha exige a senha atual, inclusive para o administrador.

## Autorização

O backend é a fonte autoritativa. Ocultar menus e botões no frontend não
substitui a autorização da API.

- `admin_master`: gerencia módulos estruturais;
- `clinic_manager`: permanece limitado à própria clínica;
- `doctor`: permanece limitado aos pacientes e exames sob sua responsabilidade;
- filtros recebidos pela API nunca ampliam o escopo institucional;
- a revisão médica exige simultaneamente a role `doctor` e a permissão
  `exams:review`;
- o administrador não possui bypass para registrar uma revisão médica.

## Catálogos fechados

Roles, status e permissões possuem identificadores técnicos utilizados pelo
código e pelas regras de negócio.

- identificadores técnicos não podem ser criados ou renomeados pela API pública;
- alterações estruturais devem ser realizadas por migrations Alembic;
- textos de exibição e descrições podem ser editados quando a API permitir;
- a fonte do catálogo de permissões é
  `backend/app/modules/permissions/catalog.py`.

## Validação das requisições

Schemas utilizados como corpo de requisição devem herdar de
`StrictRequestModel`, configurado com `extra="forbid"`.

Campos desconhecidos ou imutáveis devem produzir HTTP 422 antes da execução da
regra de negócio.

## Sessões ativas e alterações RBAC

O frontend atualiza `/auth/me`:

- quando a janela recupera o foco;
- quando a aba volta a ficar visível;
- periodicamente enquanto a sessão está ativa.

Essa atualização recalcula menus, rotas e ações. Mesmo antes da atualização
visual, uma permissão revogada já deve ser recusada pelo backend.

## Arquivos clínicos

Imagens originais e mapas Grad-CAM não devem ser expostos como diretórios
públicos.

O acesso deve ocorrer por rotas autenticadas que validem:

- permissão correspondente;
- escopo da clínica e do médico;
- vínculo do arquivo com o exame;
- caminho interno seguro;
- existência e integridade básica do arquivo.

## Regressão

As verificações permanentes estão nos testes e scripts do próprio projeto:

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

python3 tests/test_model_distribution.py
```

Os testes automatizados constituem a regressão técnica permanente do projeto.
A verificação manual breve do fluxo acadêmico de exames, da jornada do médico e
do isolamento entre clínicas será registrada durante o fechamento técnico do
protótipo. Essas verificações não equivalem a auditoria profissional de segurança,
validação clínica ou certificação para uso real.
