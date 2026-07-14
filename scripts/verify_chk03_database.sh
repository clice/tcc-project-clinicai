#!/usr/bin/env sh
# Verifica CHK-03 em PostgreSQL descartável, sem tocar no banco de desenvolvimento.

set -eu

PROJECT_NAME="clinicai-chk03"
COMPOSE_FILE="docker-compose.chk03.yml"
REPORT_DIR="reports/chk-03"
KEEP_ENVIRONMENT="${CHK03_KEEP_ENVIRONMENT:-0}"

compose() {
  docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "$@"
}

runner() {
  entrypoint="$1"
  shift
  compose run --rm --no-deps --entrypoint "$entrypoint" chk03-runner "$@"
}

startup() {
  seed_mode="$1"
  compose run --rm --no-deps -e "SEED_MODE=$seed_mode" chk03-runner true
}

cleanup() {
  if [ "$KEEP_ENVIRONMENT" = "1" ]; then
    echo "[CHK-03] Ambiente mantido por CHK03_KEEP_ENVIRONMENT=1."
  else
    compose down -v --remove-orphans >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

rm -rf "$REPORT_DIR"
mkdir -p "$REPORT_DIR"
compose down -v --remove-orphans >/dev/null 2>&1 || true

printf '%s\n' "[CHK-03] Construindo o runner do backend..."
compose build chk03-runner

printf '%s\n' "[CHK-03] Iniciando PostgreSQL descartável..."
compose up -d chk03-db

attempt=1
while ! compose exec -T chk03-db pg_isready -U clinicai_chk03 -d clinicai_chk03 >/dev/null 2>&1; do
  if [ "$attempt" -ge 30 ]; then
    echo "[CHK-03] PostgreSQL não ficou pronto a tempo." >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 2
done

printf '%s\n' "[CHK-03] 1/8 - Banco vazio antes das migrations."
runner python -m app.maintenance.database_contract assert-empty

printf '%s\n' "[CHK-03] 2/8 - Upgrade até o head e contrato do schema."
runner alembic upgrade head
runner alembic check
runner python -m app.maintenance.database_contract verify-schema \
  --output /reports/schema-inventory.json

printf '%s\n' "[CHK-03] 3/8 - Downgrade/upgrade da migration de índice do CHK-03."
runner alembic downgrade c8d2e4f6a701
runner python -m app.maintenance.database_contract assert-index \
  --table clinics --columns status_id --present false
runner alembic upgrade head
runner python -m app.maintenance.database_contract assert-index \
  --table clinics --columns status_id --present true

printf '%s\n' "[CHK-03] 4/8 - Round-trip das migrations recentes de RBAC até o head."
runner alembic downgrade a1b2c3d4e5f6
runner alembic upgrade head
runner alembic check
runner python -m app.maintenance.database_contract verify-schema \
  --output /reports/schema-after-roundtrip.json

printf '%s\n' "[CHK-03] 5/8 - Bootstrap estrutural, sem dados demo."
startup bootstrap
runner python -m app.maintenance.database_contract assert-no-demo

printf '%s\n' "[CHK-03] 6/8 - Preservação de configuração em três startups."
runner python -m app.maintenance.database_contract customize
runner python -m app.maintenance.database_contract snapshot \
  --output /reports/bootstrap-customized-reference.json

for iteration in 1 2 3; do
  startup bootstrap
  runner python -m app.maintenance.database_contract snapshot \
    --output "/reports/bootstrap-restart-${iteration}.json"
  runner python -m app.maintenance.database_contract compare \
    --expected /reports/bootstrap-customized-reference.json \
    --actual "/reports/bootstrap-restart-${iteration}.json"
done

printf '%s\n' "[CHK-03] 7/8 - Massa acadêmica opcional e vínculos fictícios."
startup academic_demo
runner python -m app.maintenance.database_contract assert-demo
runner python -m app.maintenance.database_contract snapshot \
  --output /reports/academic-demo-reference.json

printf '%s\n' "[CHK-03] 8/8 - Idempotência demo em três startups."
for iteration in 1 2 3; do
  startup academic_demo
  runner python -m app.maintenance.database_contract assert-demo
  runner python -m app.maintenance.database_contract snapshot \
    --output "/reports/academic-demo-restart-${iteration}.json"
  runner python -m app.maintenance.database_contract compare \
    --expected /reports/academic-demo-reference.json \
    --actual "/reports/academic-demo-restart-${iteration}.json"
done

cat > "$REPORT_DIR/result.txt" <<'EOF'
CHK-03 aprovado.

Validado em PostgreSQL 16:
- banco vazio antes de alembic upgrade head;
- head Alembic único e alembic check sem diferenças;
- downgrade/upgrade das migrations recentes;
- uniques, FKs, política de cascata e índices;
- bootstrap sem massa de demonstração;
- preservação de configuração administrativa em três startups;
- criação previsível da massa acadêmica fictícia;
- idempotência da massa acadêmica em três startups.
EOF

printf '\n%s\n' "CHK-03 aprovado. Evidências: $REPORT_DIR/"
