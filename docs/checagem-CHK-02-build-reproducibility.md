# CHK-02 — Dependências e build reproduzível

## Objetivo

Garantir que frontend, backend e serviço de IA sejam construídos a partir de manifests portáveis, versões fixadas e imagens-base identificáveis. O aceite exige duas construções consecutivas sem cache com a mesma árvore instalada de dependências.

## Revisão após a primeira execução

A primeira versão do CHK-02 continha um defeito crítico: o `package-lock.json` havia sido gerado em um ambiente com registry interno e registrava 361 URLs desse registry. Como o npm preserva o campo `resolved`, o `npm ci` no computador da desenvolvedora tentava acessar um host privado e não portátil. O erro aparecia tardiamente como `Exit handler never called`.

A correção não é substituir `npm ci`. O lock precisa apontar para o registry público e o verificador deve rejeitar registries internos.

Também foram corrigidos estes pontos:

- imagens-base flutuantes;
- comparação do frontend que podia esconder falha de `npm ls` por causa de um pipeline sem `pipefail`;
- ausência de validação de `integrity` e dos hosts presentes no lock;
- evidência insuficiente sobre versões de Node, npm, Python e pip;
- documentação priorizando PowerShell, embora o ambiente oficial do projeto seja Ubuntu/Bash;
- incompatibilidade entre o `meta_classificador.joblib`, salvo com scikit-learn 1.6.1, e o runtime 1.6.0.

## Estado corrigido

### Frontend

- `package-lock.json` com `lockfileVersion: 3`;
- todos os artefatos resolvidos em `https://registry.npmjs.org/`;
- todos os pacotes com `integrity`;
- `.npmrc` fixa o registry público e configura tentativas de rede;
- Dockerfile usa `npm ci`;
- imagem-base fixada por versão e digest:
  - `node:22.23.1-bookworm-slim`;
  - digest multi-plataforma registrado no Dockerfile.

### Backend e IA

- dependências diretas com `==`;
- locks transitivos com hashes;
- instalação com `pip --require-hashes`;
- versão do pip fixada;
- imagem-base fixada por versão e digest:
  - `python:3.12.13-slim-bookworm`;
  - digest multi-plataforma registrado no Dockerfile.

### Compatibilidade do modelo

O serviço de IA usa `scikit-learn==1.6.1`, correspondente à versão que serializou o metaclassificador. Essa correspondência evita o `InconsistentVersionWarning` observado no teste de inferência.

## Validação estática

Na raiz do projeto:

```bash
python3 scripts/check_dependency_locks.py
```

O verificador rejeita:

- divergência entre manifest e lock;
- dependência Python sem versão exata;
- pacote Python sem hash;
- package-lock sem `integrity`;
- URLs internas, privadas ou diferentes do registry público do npm;
- Dockerfile sem `npm ci` ou `--require-hashes`;
- imagem-base sem tag exata e digest.

Resultado esperado:

```text
CHK-02: manifests, locks e Dockerfiles estão coerentes.
```

## Teste completo no Ubuntu

```bash
chmod +x scripts/verify_reproducible_builds.sh
./scripts/verify_reproducible_builds.sh
```

O script executa cada componente por completo antes de passar ao próximo:

1. build A sem cache;
2. captura e validação da árvore A;
3. build B sem cache;
4. captura e validação da árvore B;
5. comparação A × B.

Assim, uma falha do frontend interrompe o teste antes dos builds demorados do backend e da IA.

As evidências ficam em:

```text
reports/chk-02/
```

Principais arquivos:

- `result.txt`;
- `environment.txt`;
- `source-sha256.txt`;
- `build-<componente>-<rodada>.log`;
- `tree-<componente>-<rodada>.txt`;
- `versions-<componente>-<rodada>.txt`;
- `pip-check-<componente>-<rodada>.txt`;
- `diff-<componente>.txt`, somente em divergência.

Para manter as imagens temporárias:

```bash
CHK02_KEEP_IMAGES=1 ./scripts/verify_reproducible_builds.sh
```

## Recriação segura do package-lock

Só é necessário quando `package.json` mudar. No Ubuntu:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install \
  --package-lock-only \
  --ignore-scripts \
  --registry=https://registry.npmjs.org/
npm ci --registry=https://registry.npmjs.org/
npm run build
cd ..
python3 scripts/check_dependency_locks.py
```

Antes do commit, confirme que não existe registry privado:

```bash
grep -nE 'internal|artifactory|openai\.org|localhost|127\.0\.0\.1' \
  frontend/package-lock.json
```

O comando deve terminar sem saída.

## Regeneração dos locks Python

Quando um `requirements.txt` mudar, regenere o respectivo lock para Python 3.12/Linux x86-64 usando a ferramenta de lock adotada pelo projeto e o índice público do PyPI. Depois execute:

```bash
python3 scripts/check_dependency_locks.py
```

Não edite hashes manualmente como fluxo normal. Uma alteração pontual só é aceitável quando o arquivo oficial e o SHA-256 tiverem sido verificados e documentados.

## Critério de aceite

O CHK-02 só pode ser marcado como concluído quando:

- a validação estática passar;
- as seis construções terminarem sem erro;
- `npm ls` e `pip check` não apontarem inconsistências;
- os três pares de árvores forem idênticos;
- `reports/chk-02/result.txt` registrar `CHK-02 aprovado`.

## Limitação

A igualdade da árvore de dependências não significa que as imagens sejam byte a byte idênticas. Metadados de build e timestamps podem mudar. O critério deste item é a mesma base identificada e a mesma árvore instalada; a reprodutibilidade bit a bit exigiria uma política adicional de build hermético.
