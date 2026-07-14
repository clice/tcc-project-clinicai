# Guia de Publicação e Atualização dos Modelos

Este documento descreve como preparar, publicar, validar e atualizar os artefatos de
Inteligência Artificial distribuídos pelo GitHub Releases do ClinicAI.

Quem deseja apenas instalar e executar o sistema deve seguir a seção **Como Executar o Projeto**
do [`README.md`](../README.md) principal.

## 1. Como a distribuição funciona

Os pesos treinados não ficam no histórico do Git. Eles são publicados como anexos de uma
GitHub Release e baixados pelo serviço `model-downloader` definido em `docker-compose.yml`.

A configuração padrão fica no `.env` da raiz:

```dotenv
MODEL_RELEASE_REPOSITORY=clice/tcc-project-clinicai
MODEL_RELEASE_TAG=models-v0.1.0
MODEL_RELEASE_MANIFEST=manifesto_modelos.json
```

O arquivo `manifesto_modelos.json` registra a versão, o tamanho e o SHA-256 de cada artefato.
Durante o download, `scripts/download_models.py` valida esses dados antes de instalar os
arquivos em `ai/models/exported/gastrointestinal/`. O conjunto é preparado em um diretório
temporário e só substitui a instalação atual depois que todos os artefatos passam pela
verificação; se um download falhar, a versão anterior permanece intacta.

## 2. Release atual

- Tag: `models-v0.1.0`;
- Título: `Modelos ClinicAI v0.1.0`;
- Página: <https://github.com/clice/tcc-project-clinicai/releases/tag/models-v0.1.0>;
- Domínio: `gastrointestinal`;
- Versão do manifesto: `0.1.0`.

Uma Release publicada deve conter exatamente:

```text
resnet50.pt
efficientnet_b4.pt
pvt_v2_b2.pt
meta_classificador.joblib
manifesto_modelos.json
```

Os arquivos automáticos `Source code (zip)` e `Source code (tar.gz)` não substituem esses
anexos e não contêm os modelos ignorados pelo Git.

## 3. Quando criar uma nova Release

Não altere os anexos de uma versão já publicada. Crie uma nova Release quando houver mudança
em qualquer um destes elementos:

- pesos de um dos modelos base;
- meta-classificador;
- arquiteturas dos modelos;
- classes ou ordem das classes;
- pré-processamento exigido pelos pesos;
- ordem das meta-features do ensemble;
- formato do manifesto ou contrato de carregamento.

Alterações apenas no frontend, backend, README ou RBAC não exigem uma nova Release de modelos,
desde que o contrato de inferência permaneça compatível.

### Sugestão de versionamento

| Tipo de alteração | Exemplo de versão |
|---|---|
| Correção dos artefatos, mantendo o mesmo contrato | `models-v0.1.1` |
| Nova versão compatível dos modelos ou do ensemble | `models-v0.2.0` |
| Mudança incompatível de classes, entrada ou contrato | `models-v1.0.0` |

## 4. Preparar uma nova versão

### 4.1 Atualizar e conferir a branch principal

Trabalhe primeiro em uma branch própria, revise as mudanças e faça o merge na `main`. Depois:

```bash
git switch main
git pull --ff-only origin main
git status
```

O diretório de trabalho deve estar limpo antes de criar a tag da Release.

### 4.2 Posicionar os artefatos

Coloque os quatro arquivos em:

```text
ai/models/exported/gastrointestinal/
```

Use exatamente estes nomes:

```text
resnet50.pt
efficientnet_b4.pt
pvt_v2_b2.pt
meta_classificador.joblib
```

A ordem das meta-features do meta-classificador deve continuar igual à definida em
`ai/app/inference/domains/gastrointestinal.py`: ResNet-50, EfficientNet-B4 e PVTv2-B2.

### 4.3 Testar a inferência local

Antes de publicar, suba o serviço de IA e execute uma predição pelo Swagger:

```bash
docker compose up --build -d ai
docker compose logs --tail=100 ai
```

Abra <http://localhost:8001/docs>, envie uma imagem para `POST /predict` e use:

```text
exam_type: endoscopy
```

Somente prossiga se a resposta for HTTP `200` e contiver a predição completa.

### 4.4 Executar os testes do distribuidor

Na raiz do projeto:

```bash
python3 -m unittest tests.test_model_distribution
```

Os testes confirmam o download, a validação dos hashes, a rejeição de artefatos adulterados e a
preservação integral da versão anterior quando a atualização falha.

## 5. Gerar o manifesto

Escolha uma tag que ainda não exista. Exemplo para a versão `0.1.1`:

```bash
python3 scripts/generate_model_manifest.py \
  --release-tag models-v0.1.1 \
  --model-version 0.1.1
```

O arquivo será criado em:

```text
ai/models/exported/gastrointestinal/manifesto_modelos.json
```

Confira o conteúdo e os hashes locais:

```bash
cat ai/models/exported/gastrointestinal/manifesto_modelos.json

sha256sum \
  ai/models/exported/gastrointestinal/resnet50.pt \
  ai/models/exported/gastrointestinal/efficientnet_b4.pt \
  ai/models/exported/gastrointestinal/pvt_v2_b2.pt \
  ai/models/exported/gastrointestinal/meta_classificador.joblib
```

Os hashes e tamanhos devem coincidir com os valores do manifesto.

## 6. Planejar a atualização da versão padrão

Não altere `.env.example` para uma tag que ainda não foi publicada e validada. Durante o teste
da nova Release, configure a tag somente no `.env` local:

```dotenv
MODEL_RELEASE_TAG=models-v0.1.1
```

Depois que o teste em clone limpo da seção 8 passar, altere `MODEL_RELEASE_TAG` em `.env.example`
e atualize os exemplos de versão na documentação. Revise essas mudanças em uma branch e faça o
merge na `main`.

Não versione o `.env` local e nunca grave tokens de acesso no repositório, no Compose ou na
documentação.

## 7. Criar a Release no GitHub

1. Abra <https://github.com/clice/tcc-project-clinicai/releases>.
2. Selecione **Draft a new release**.
3. Informe a nova tag, por exemplo `models-v0.1.1`.
4. Selecione `main` como target.
5. Use o título `Modelos ClinicAI v0.1.1`.
6. Marque **Set as a pre-release** enquanto o sistema estiver em desenvolvimento.
7. Descreva as mudanças dos modelos e eventuais requisitos de compatibilidade.
8. Anexe os quatro artefatos e `manifesto_modelos.json`.
9. Aguarde o término de todos os uploads.
10. Salve como rascunho e confira nomes e tamanhos.
11. Publique somente depois da conferência final.

Checklist antes de publicar:

- [ ] a tag do formulário é igual a `release_tag` no manifesto;
- [ ] a versão descrita é igual a `model_version` no manifesto;
- [ ] o target é a `main` atualizada;
- [ ] os cinco anexos estão presentes e possuem tamanho maior que zero;
- [ ] a inferência local retornou HTTP `200`;
- [ ] os testes de distribuição passaram;
- [ ] nenhum arquivo contém credenciais ou dados clínicos.

## 8. Validar a Release publicada

Faça o teste em um clone novo, sem aproveitar os modelos locais:

```bash
cd ..
git clone https://github.com/clice/tcc-project-clinicai.git clinicai-release-test
cd clinicai-release-test
cp .env.example .env
docker compose --profile models run --rm model-downloader
```

A saída deve informar que cada arquivo foi baixado e verificado. Execute novamente:

```bash
docker compose --profile models run --rm model-downloader
```

Na segunda execução, o distribuidor deve informar que cada arquivo já existe e possui o
SHA-256 esperado.

Para validar o fluxo completo, configure os demais ambientes e suba o sistema:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build -d
docker compose ps
```

Confira os logs e repita a predição pelo Swagger:

```bash
docker compose logs --tail=100 ai
docker compose logs --tail=100 backend
```

## 9. Se uma Release apresentar erro

- Não substitua silenciosamente os anexos da versão publicada.
- Confirme que o downloader manteve a versão local anterior intacta.
- Preserve a Release anterior para reprodutibilidade.
- Corrija e teste os artefatos localmente.
- Gere outro manifesto com uma nova versão.
- Publique uma nova tag, normalmente incrementando a versão de correção.
- Atualize `MODEL_RELEASE_TAG` somente depois de confirmar a nova versão.

Se o problema for percebido ainda no rascunho, corrija os anexos antes da publicação.

## 10. Repositórios privados

O distribuidor atual usa URLs públicas do GitHub Releases. Se o repositório se tornar privado,
será necessário implementar autenticação específica. Tokens não devem ser colocados no
`docker-compose.yml`, em arquivos `.env.example`, no README ou no histórico do Git.
