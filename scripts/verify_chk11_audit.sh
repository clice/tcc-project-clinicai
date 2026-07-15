#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TEST_DB_NAME="${CHK11_TEST_DB_NAME:-clinicai_chk11_test}"
TEST_DATABASE_URL="postgresql+psycopg://clinicai:clinicai123@db:5432/${TEST_DB_NAME}"

cleanup_chk11_test_database() {
  set +e

  echo "[CHK-11] Removendo banco PostgreSQL temporário..."
  docker compose exec -T db \
    psql -U clinicai -d postgres \
    -c "SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '${TEST_DB_NAME}'
          AND pid <> pg_backend_pid();" \
    >/dev/null 2>&1

  docker compose exec -T db \
    psql -U clinicai -d postgres \
    -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};" \
    >/dev/null 2>&1
}

trap cleanup_chk11_test_database EXIT

echo "[CHK-11] Validando configuração do Docker Compose..."
docker compose config --quiet

echo "[CHK-11] Construindo backend e frontend..."
docker compose build backend frontend

echo "[CHK-11] Executando testes específicos de auditoria e rollback..."
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m pytest -q \
  tests/test_audit_integrity.py \
  tests/test_exam_file_security.py \
  tests/test_exam_history_rbac.py

echo "[CHK-11] Subindo o PostgreSQL sem apagar volumes..."
docker compose up -d db

echo "[CHK-11] Recriando banco temporário para concorrência real..."
docker compose exec -T db \
  psql -U clinicai -d postgres \
  -v ON_ERROR_STOP=1 \
  -c "SELECT pg_terminate_backend(pid)
      FROM pg_stat_activity
      WHERE datname = '${TEST_DB_NAME}'
        AND pid <> pg_backend_pid();"

docker compose exec -T db \
  psql -U clinicai -d postgres \
  -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS ${TEST_DB_NAME};"

docker compose exec -T db \
  psql -U clinicai -d postgres \
  -v ON_ERROR_STOP=1 \
  -c "CREATE DATABASE ${TEST_DB_NAME};"

echo "[CHK-11] Aplicando migrations no banco temporário..."
docker compose run --rm --no-deps \
  -e DATABASE_URL="$TEST_DATABASE_URL" \
  --entrypoint alembic \
  -w /app \
  backend upgrade head

echo "[CHK-11] Revalidando claim e revisão concorrentes no PostgreSQL..."
docker compose run --rm --no-deps \
  -e DATABASE_URL="$TEST_DATABASE_URL" \
  -e TEST_DATABASE_URL="$TEST_DATABASE_URL" \
  --entrypoint python \
  -w /app \
  backend -m pytest -q \
  tests/test_exam_state_machine_postgres.py

echo "[CHK-11] Executando a suíte completa do backend..."
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m pytest -q

echo "[CHK-11] Revalidando o contrato RBAC do frontend..."
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:rbac

echo "[CHK-11] Gerando build de produção do frontend..."
docker compose run --rm --no-deps \
  -w /app \
  frontend npm run build

echo "[CHK-11] Compilando backend e testes..."
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m compileall -q app tests

echo "[CHK-11] Validação concluída com sucesso."
echo "[CHK-11] O container db permanece ativo; use 'docker compose stop db' quando apropriado."
