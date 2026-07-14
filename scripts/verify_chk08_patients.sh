#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[CHK-08] Construindo imagens de backend e frontend..."
docker compose build backend frontend

echo "[CHK-08] Executando testes específicos de pacientes e isolamento..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m pytest -q \
  tests/test_patients_api.py \
  tests/test_tenant_isolation.py \
  tests/test_strict_request_schemas.py

echo "[CHK-08] Executando a suíte completa do backend..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m pytest -q

echo "[CHK-08] Verificando o contrato RBAC..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:rbac

echo "[CHK-08] Verificando o contrato de clínicas..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:clinics

echo "[CHK-08] Verificando o contrato de usuários..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:users

echo "[CHK-08] Verificando o contrato de pacientes..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:patients

echo "[CHK-08] Gerando o build do frontend..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run build

echo "[CHK-08] Compilando os módulos Python..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m compileall -q app tests

echo "[CHK-08] Validação concluída com sucesso."
