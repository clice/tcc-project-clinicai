#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[CHK-09] Validando configuração do Docker Compose..."
docker compose config --quiet

echo "[CHK-09] Construindo backend e frontend..."
docker compose build backend frontend

echo "[CHK-09] Subindo PostgreSQL para validar a migration..."
docker compose up -d db

echo "[CHK-09] Aplicando migrations até o head..."
docker compose run --rm --no-deps \
  --entrypoint alembic \
  backend upgrade head

echo "[CHK-09] Conferindo revisão Alembic ativa..."
docker compose run --rm --no-deps \
  --entrypoint alembic \
  backend current

echo "[CHK-09] Executando testes específicos de estados e histórico..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m pytest -q \
  tests/test_exam_state_machine.py \
  tests/test_exam_history_rbac.py

echo "[CHK-09] Executando suíte completa do backend..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m pytest -q

echo "[CHK-09] Executando contratos do frontend contra o repositório completo..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:rbac

docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:clinics

docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:users

docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:patients

docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:exams

echo "[CHK-09] Gerando build de produção do frontend..."
docker compose run --rm --no-deps frontend npm run build

echo "[CHK-09] Compilando backend e testes..."
docker compose run --rm --no-deps \
  --entrypoint python \
  backend -m compileall -q app tests

echo "[CHK-09] Validação concluída com sucesso."
echo "[CHK-09] O container do banco permanece ativo; encerre-o com 'docker compose stop db' quando apropriado."
