#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[CHK-07] Construindo imagens de backend e frontend..."
docker compose build backend frontend

echo "[CHK-07] Executando testes específicos de usuários..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m pytest -q tests/test_users_api.py

echo "[CHK-07] Executando a suíte completa do backend..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m pytest -q

echo "[CHK-07] Verificando o contrato RBAC..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:rbac

echo "[CHK-07] Verificando o contrato de clínicas..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:clinics

echo "[CHK-07] Verificando o contrato de usuários..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:users

echo "[CHK-07] Gerando o build do frontend..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run build

echo "[CHK-07] Compilando os módulos Python..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m compileall -q app tests

echo "[CHK-07] Validação concluída com sucesso."
