# Guia de Publicação e Atualização dos Modelos

Este documento descreve como preparar, publicar, validar e atualizar os artefatos de
Inteligência Artificial distribuídos pelo GitHub Releases do ClinicAI.

Para apenas instalar e executar o sistema, consulte o
[`README.md`](../README.md) principal.

## 1. Como a distribuição funciona

Os pesos treinados não ficam no histórico do Git. Eles são publicados como anexos de uma
GitHub Release e baixados pelo serviço auxiliar `model-downloader` definido em
`docker-compose.yml`.

A configuração padrão fica no `.env` da raiz:

```dotenv
MODEL_RELEASE_REPOSITORY=clice/tcc-project-clinicai
MODEL_RELEASE_TAG=models-v0.1.2
MODEL_RELEASE_MANIFEST=manifesto_modelos.json
```

O arquivo `manifesto_modelos.json` registra:

- versão do esquema;
- tag da release;
- versão do modelo;
- domínio;
- nome, tamanho e SHA-256 de cada artefato.

Durante o download, `scripts/download_models.py` valida o manifesto e os anexos antes de
instalá-los em:

```text
ai/models/exported/gastrointestinal/
```

A atualização é preparada em uma área temporária. A instalação existente somente é
substituída depois que todo o conjunto é aprovado. Em caso de falha, a versão anterior
permanece intacta.

## 2. Release operacional atual

- tag: `models-v0.1.2`;
- título: `Modelos ClinicAI v0.1.2`;
- domínio: `gastrointestinal`;
- versão do modelo: `0.1.2`;
- protocolo: `viana_codigo_kfold3_roi_sh_da`;
- fold operacional: `1`;
- critério de seleção: melhor desempenho entre os três folds em acurácia e F1-*Score*.

A release deve conter exatamente:

```text
resnet50.pt
efficientnet_b4.pt
pvt_v2_b2.pt
meta_classificador.joblib
manifesto_modelos.json
```

Os arquivos automáticos `Source code (zip)` e `Source code (tar.gz)` não substituem esses
anexos.

As releases `models-v0.1.0` e `models-v0.1.1` permanecem preservadas como versões históricas.
Não altere silenciosamente os anexos de uma versão publicada.

## 3. Quando criar uma nova release

Crie uma nova versão quando houver mudança em qualquer item que afete a inferência:

- pesos de um modelo base;
- meta-classificador;
- arquitetura;
- classes ou ordem das classes;
- pré-processamento;
- ordem das *meta-features*;
- formato do manifesto;
- contrato de carregamento;
- método de atribuição que exija artefatos diferentes.

Mudanças apenas no frontend, backend, README ou RBAC não exigem nova release quando o contrato
dos modelos permanece inalterado.

### Sugestão de versionamento

| Alteração | Exemplo |
|---|---|
| Correção compatível dos artefatos | `models-v0.1.3` |
| Nova versão compatível do modelo | `models-v0.2.0` |
| Mudança incompatível de entrada ou classes | `models-v1.0.0` |

## 4. Preparar uma nova versão

### 4.1 Trabalhar em branch própria

Revise e integre primeiro as mudanças de código e documentação. Antes da publicação:

```bash
git switch main
git pull --ff-only origin main
git status --short --branch
```

O diretório de trabalho deve estar limpo.

### 4.2 Posicionar os artefatos

Coloque os quatro arquivos em:

```text
ai/models/exported/gastrointestinal/
```

Use exatamente:

```text
resnet50.pt
efficientnet_b4.pt
pvt_v2_b2.pt
meta_classificador.joblib
```

A ordem das *meta-features* deve permanecer:

1. ResNet-50;
2. EfficientNet-B4;
3. PVTv2-B2.

### 4.3 Testar a inferência local

```bash
docker compose up --build -d ai
docker compose logs --tail=100 ai
```

Abra `http://localhost:8001/docs` e execute `POST /predict` com uma imagem compatível e:

```text
exam_type: endoscopy
```

Prossiga somente quando a resposta retornar HTTP 200, classe, confiança, versão e contrato de
atribuição compatíveis.

### 4.4 Executar os testes

```bash
python3 -m unittest tests.test_model_distribution

docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  ai -m unittest discover -s tests -p 'test_*.py' -v
```

## 5. Gerar o manifesto

Escolha uma tag ainda inexistente. Exemplo para uma atualização futura `0.1.3`:

```bash
python3 scripts/generate_model_manifest.py \
  --release-tag models-v0.1.3 \
  --model-version 0.1.3
```

O arquivo será gerado em:

```text
ai/models/exported/gastrointestinal/manifesto_modelos.json
```

Confira:

```bash
cat ai/models/exported/gastrointestinal/manifesto_modelos.json

sha256sum \
  ai/models/exported/gastrointestinal/resnet50.pt \
  ai/models/exported/gastrointestinal/efficientnet_b4.pt \
  ai/models/exported/gastrointestinal/pvt_v2_b2.pt \
  ai/models/exported/gastrointestinal/meta_classificador.joblib
```

Os tamanhos e hashes devem coincidir.

## 6. Testar a nova tag localmente

Não altere `.env.example` antes de publicar e validar a nova release. Durante a preparação, use
somente o `.env` local:

```dotenv
MODEL_RELEASE_TAG=models-v0.1.3
```

Não versione o `.env` nem armazene tokens no repositório.

## 7. Criar a release

1. Abra a seção **Releases** do repositório.
2. Selecione **Draft a new release**.
3. Informe a nova tag.
4. Use a `main` atualizada como alvo.
5. Informe o título correspondente.
6. Marque como *pre-release* somente durante a validação, quando necessário.
7. Descreva os modelos, o protocolo, o fold e mudanças de compatibilidade.
8. Anexe os quatro artefatos e o manifesto.
9. Confira nomes e tamanhos.
10. Publique somente após a revisão final.

Checklist:

- [ ] a tag é igual a `release_tag`;
- [ ] a versão é igual a `model_version`;
- [ ] o domínio é `gastrointestinal`;
- [ ] os cinco anexos estão presentes;
- [ ] os hashes coincidem;
- [ ] a inferência local foi aprovada;
- [ ] os testes foram aprovados;
- [ ] nenhum arquivo contém credenciais ou dados clínicos.

## 8. Validar em clone limpo

```bash
cd ..
git clone https://github.com/clice/tcc-project-clinicai.git clinicai-release-test
cd clinicai-release-test

cp .env.example .env
docker compose --profile models run --rm model-downloader
```

Execute novamente:

```bash
docker compose --profile models run --rm model-downloader
```

Na segunda execução, os arquivos válidos devem ser preservados.

Para testar o fluxo completo:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker compose up --build -d
docker compose ps
docker compose logs --tail=100 ai
docker compose logs --tail=100 backend
```

Repita a predição pelo Swagger e verifique o fluxo no ClinicAI.

## 9. Tornar a nova versão padrão

Somente depois da validação em clone limpo:

1. atualize `MODEL_RELEASE_TAG` em `.env.example`;
2. confira o *fallback* em `docker-compose.yml`;
3. atualize `README.md`, `ai/README.md`, `backend/demo_assets/README.md` e este guia;
4. execute os testes;
5. integre a alteração por branch e revisão.

Não sobrescreva releases anteriores.

## 10. Tratamento de falhas

Quando uma versão apresentar problema:

- preserve a release anterior;
- confirme que o downloader manteve a instalação local válida;
- corrija e teste os artefatos;
- gere outro manifesto;
- publique uma nova tag;
- atualize a versão padrão apenas após validação.

## 11. Repositórios privados

O distribuidor atual utiliza anexos públicos. Um repositório privado exigiria autenticação
específica.

Tokens não devem ser inseridos no `docker-compose.yml`, em `.env.example`, nos READMEs ou no
histórico do Git.
