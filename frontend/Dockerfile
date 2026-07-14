# Imagem e digest fixos: Node 22.23.1 sobre Debian Bookworm slim.
FROM node:22.23.1-bookworm-slim@sha256:53ada149d435c38b14476cb57e4a7da73c15595aba79bd6971b547ceb6d018bf

WORKDIR /app

COPY package.json package-lock.json .npmrc ./

# npm ci usa exclusivamente a árvore registrada no package-lock.json.
# A versão do Node/npm vem da imagem-base fixada acima.
RUN node --version \
    && npm --version \
    && npm ci --no-audit --no-fund

COPY . .

EXPOSE 3000

CMD ["npm", "start", "--", "--host", "0.0.0.0"]
