#!/usr/bin/env bash

set -Eeuo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPOSITORY_ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERRO: Docker não foi encontrado. Instale ou abra o Docker Desktop e tente novamente."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERRO: o comando 'docker compose' não está disponível."
  exit 1
fi

if [[ ! -f backend/.env || ! -f frontend/.env ]]; then
  echo "ERRO: faltam backend/.env ou frontend/.env."
  echo "Crie-os a partir dos respectivos arquivos .env.example antes de testar."
  exit 1
fi

run_step() {
  local description="$1"
  shift
  echo
  echo "==> $description"
  "$@"
}

run_step "Iniciando o banco de dados" docker compose up -d db

echo
echo "==> Aguardando o PostgreSQL ficar disponível"
for attempt in {1..30}; do
  if docker compose exec -T db pg_isready -U clinicai -d clinicai >/dev/null 2>&1; then
    break
  fi

  if [[ "$attempt" -eq 30 ]]; then
    echo "ERRO: o PostgreSQL não ficou disponível dentro do tempo esperado."
    exit 1
  fi

  sleep 2
done

run_step "Construindo as imagens de teste" docker compose build backend frontend
run_step "Aplicando as migrations" \
  docker compose run --rm --no-deps --entrypoint alembic backend upgrade head
run_step "Executando os testes do backend" \
  docker compose run --rm --no-deps --entrypoint python backend -m pytest -q
run_step "Validando os contratos do fluxo de exames" \
  docker compose run --rm --no-deps \
    -v "$REPOSITORY_ROOT:/workspace:ro" \
    frontend \
    npm --prefix /workspace/frontend run check:exams
run_step "Validando a navegação e as permissões" \
  docker compose run --rm --no-deps frontend npm run check:navigation
run_step "Gerando o build de produção do frontend" \
  docker compose run --rm --no-deps frontend npm run build

echo
echo "SUCESSO: todos os testes do Bloco 1 foram aprovados."
