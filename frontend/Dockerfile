FROM node:22-alpine

WORKDIR /app

COPY package*.json ./

# Achado FE-06 de revisão: não existe package-lock.json no projeto, então
# "npm install" resolve versões dentro dos intervalos do package.json a
# cada build — pode instalar uma versão diferente da que o autor usou.
# Correção (não aplicada automaticamente aqui, requer rodar localmente
# com acesso à internet):
#   1. Rode `npm install` localmente (fora do Docker) para gerar
#      package-lock.json.
#   2. Commit o arquivo gerado.
#   3. Troque a linha abaixo para `RUN npm ci` (mais rápido e determinístico
#      que "npm install", mas EXIGE que package-lock.json exista — não
#      troque antes do passo 1/2, ou o build vai falhar).
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start", "--", "--host", "0.0.0.0"]