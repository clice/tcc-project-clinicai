#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[CHK-10] Validando configuração do Docker Compose..."
docker compose config --quiet

echo "[CHK-10] Construindo backend e frontend..."
docker compose build backend frontend

echo "[CHK-10] Executando testes específicos de upload, armazenamento e download..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m pytest -q \
  tests/test_exam_file_security.py \
  tests/test_tenant_isolation.py

echo "[CHK-10] Executando suíte completa do backend..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m pytest -q

echo "[CHK-10] Executando contratos acumulados do frontend..."
for contract in rbac clinics users patients exams; do
  docker compose run --rm --no-deps \
    -v "$ROOT_DIR:/workspace" \
    -w /workspace/frontend \
    frontend npm run "check:${contract}"
done

echo "[CHK-10] Gerando build de produção do frontend..."
docker compose run --rm --no-deps frontend npm run build

echo "[CHK-10] Compilando backend e testes..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m compileall -q app tests

echo "[CHK-10] Validação concluída com sucesso."
