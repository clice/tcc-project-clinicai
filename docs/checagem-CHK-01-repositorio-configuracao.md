# Relatório da CHK-01 — Repositório e Configuração

**Data:** 14/07/2026  
**Base:** `main` no commit `73498029c75158fbbcdfe7f1e57937e02d35f1b0`  
**Escopo:** estrutura, arquivos ignorados, ambientes, segredos, portas, volumes, nomes e
distribuição dos modelos.

## Resultado

**Estado: implementação concluída; validação Docker manual pendente.**

Esta checagem considera o ClinicAI um protótipo acadêmico para execução local. O critério de
aceite prioriza reprodução, integridade e funcionamento; endurecimento de servidor público é
registrado como evolução futura.

A revisão preservou o README atualizado, `docs/model-release-guide.md`, os scripts de
distribuição e a Release `models-v0.1.0`. As correções de configuração foram integradas sem
alterar o contrato da release.

## Correções

| Item | Correção aplicada |
|---|---|
| PostgreSQL | credencial local padronizada e configurada pelo `.env` da raiz |
| Rede local | portas do ambiente de desenvolvimento restritas a `127.0.0.1` |
| Inicialização | healthcheck do PostgreSQL e dependência do backend por saúde |
| Volumes | volume órfão e montagem duplicada dos modelos removidos |
| Containers | nomes fixos removidos para permitir isolamento do projeto |
| Ambientes | exemplos alinhados às variáveis consumidas pelo código e pela release |
| Repositório | `.gitattributes`, caches, coverage, Vite, Ruff e SQLite tratados |
| Docker | pesos recursivos, manifesto e artefatos temporários excluídos dos contextos |
| Alembic | credencial de demonstração removida do placeholder versionado |
| Modelos | atualização tornou-se transacional: falha preserva o conjunto anterior |

## Decisões

- `scripts/verify_model_manifest.py` não é necessário: o gerador, o `sha256sum` documentado, o
  downloader e os testes cobrem geração e validação.
- a senha PostgreSQL é diferente das senhas de usuários criados pelos seeds;
- credenciais conhecidas são aceitáveis para banco e usuários fictícios da demonstração local;
- a CHK-03 verificará idempotência e separação lógica dos dados de demonstração;
- `package-lock.json` e `npm ci` pertencem à CHK-02.

## Evidências automatizadas executadas

- 3 testes de distribuição aprovados, cobrindo instalação inicial, reaproveitamento dos
  artefatos válidos na segunda execução e preservação da versão anterior após adulteração;
- 61 testes do backend aprovados, com 17 avisos de depreciação de dependências;
- sete verificadores RBAC do frontend aprovados;
- build do frontend aprovado, mantendo o aviso conhecido do chunk principal acima de 500 kB;
- `docker-compose.yml` e `docker-compose.gpu.yml` com YAML válido;
- serviço `model-downloader`, healthcheck e volumes validados estaticamente;
- nenhuma chave privada, token OpenAI ou chave AWS encontrada.

## Evidência manual pendente

Como o ambiente de auditoria não possui Docker, execute no repositório real:

```bash
git status --short
docker compose config
docker compose --profile models run --rm model-downloader
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8001/health
```

Os usuários de demonstração e a recarga automática são escolhas compatíveis com o protótipo
local. Eles não caracterizam uma configuração para hospedagem pública ou uso clínico real.
