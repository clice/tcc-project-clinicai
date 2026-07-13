#!/bin/sh
# =====================================================
# Entrypoint do backend ClinicAI.
#
# Executado toda vez que o container do backend sobe. Garante que:
#   1) o banco de dados esteja de fato aceitando conexões antes de seguir;
#   2) as migrations (Alembic) estejam aplicadas;
#   3) os dados iniciais (seeds/bootstrap) existam.
#
# Tudo aqui é idempotente. Migrations aplicam evoluções oficiais de dados;
# seeds fazem somente bootstrap de registros ausentes. Em particular, a
# matriz RBAC editável não é reconciliada na inicialização.
# =====================================================

set -e

echo "[entrypoint] Aguardando o banco de dados ficar disponível..."

python <<'PYCODE'
import sys
import time

import psycopg

from app.core.config import settings

# psycopg.connect() não entende o sufixo de dialect/driver do SQLAlchemy
# (ex: "postgresql+psycopg://"). Normalizamos para o formato que o
# psycopg puro aceita antes de testar a conexão.
db_url = settings.database_url
if "+" in db_url.split("://", 1)[0]:
    scheme, rest = db_url.split("://", 1)
    base_scheme = scheme.split("+", 1)[0]
    db_url = f"{base_scheme}://{rest}"

max_attempts = 30

for attempt in range(1, max_attempts + 1):
    try:
        conn = psycopg.connect(db_url, connect_timeout=3)
        conn.close()
        break
    except Exception as exc:
        print(f"[entrypoint] Tentativa {attempt}/{max_attempts} falhou: {exc}")
        if attempt == max_attempts:
            print("[entrypoint] Banco de dados não respondeu a tempo. Abortando.")
            sys.exit(1)
        time.sleep(2)
PYCODE

echo "[entrypoint] Banco de dados disponível."

echo "[entrypoint] Aplicando migrations (alembic upgrade head)..."
alembic upgrade head

echo "[entrypoint] Executando seeds..."
python -m app.modules.seeds

echo "[entrypoint] Setup concluído. Iniciando aplicação..."
exec "$@"
