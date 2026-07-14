#!/usr/bin/env bash
set -Eeuo pipefail

# CHK-02: constrói frontend, backend e IA duas vezes sem cache e compara a
# árvore efetivamente instalada. Script principal para Ubuntu/Linux.

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${CHK02_EVIDENCE_DIR:-$ROOT_DIR/reports/chk-02}"
KEEP_IMAGES="${CHK02_KEEP_IMAGES:-0}"
CURRENT_COMPONENT="preflight"
CURRENT_ROUND="-"

mkdir -p "$EVIDENCE_DIR"
rm -f "$EVIDENCE_DIR"/{result.txt,failure.txt,diff-*.txt,tree-*.txt,tree-*.json,versions-*.txt,image-*.json,build-*.log,pip-check-*.txt,static-check.log,environment.txt,source-sha256.txt} 2>/dev/null || true

cleanup() {
  if [[ "$KEEP_IMAGES" != "1" ]]; then
    docker image rm \
      clinicai-frontend:chk02-a clinicai-frontend:chk02-b \
      clinicai-backend:chk02-a clinicai-backend:chk02-b \
      clinicai-ai:chk02-a clinicai-ai:chk02-b \
      >/dev/null 2>&1 || true
  fi
}

on_error() {
  local exit_code=$?
  local line_no=${1:-unknown}
  {
    echo "CHK-02 reprovado."
    echo "Data UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    echo "Componente: $CURRENT_COMPONENT"
    echo "Rodada: $CURRENT_ROUND"
    echo "Linha do script: $line_no"
    echo "Comando: ${BASH_COMMAND:-unknown}"
    echo "Consulte as evidências em: $EVIDENCE_DIR"
  } | tee "$EVIDENCE_DIR/result.txt" "$EVIDENCE_DIR/failure.txt" >&2
  exit "$exit_code"
}

trap 'on_error $LINENO' ERR
trap cleanup EXIT INT TERM

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Erro: comando obrigatório ausente: $1" >&2
    return 1
  fi
}

require_command docker
require_command python3
require_command sha256sum
require_command sort
require_command cmp

docker info >/dev/null

{
  echo "Data UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "Sistema: $(uname -a)"
  echo "Docker: $(docker --version)"
  echo "Docker Compose: $(docker compose version 2>/dev/null || echo 'não utilizado neste teste')"
} | tee "$EVIDENCE_DIR/environment.txt"

python3 "$ROOT_DIR/scripts/check_dependency_locks.py" | tee "$EVIDENCE_DIR/static-check.log"

sha256sum \
  "$ROOT_DIR/frontend/package.json" \
  "$ROOT_DIR/frontend/package-lock.json" \
  "$ROOT_DIR/frontend/.npmrc" \
  "$ROOT_DIR/frontend/Dockerfile" \
  "$ROOT_DIR/backend/requirements.txt" \
  "$ROOT_DIR/backend/requirements.lock.txt" \
  "$ROOT_DIR/backend/Dockerfile" \
  "$ROOT_DIR/ai/requirements.txt" \
  "$ROOT_DIR/ai/requirements.lock.txt" \
  "$ROOT_DIR/ai/Dockerfile" \
  >"$EVIDENCE_DIR/source-sha256.txt"

canonicalize_npm_tree() {
  local input_json=$1
  local output_txt=$2

  python3 - "$input_json" "$output_txt" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
data = json.loads(source.read_text(encoding="utf-8"))

problems = data.get("problems") or []
if problems:
    raise SystemExit("npm ls encontrou problemas:\n- " + "\n- ".join(problems))

lines: list[str] = []


def walk(dependencies: dict, prefix: str = "") -> None:
    for name in sorted(dependencies):
        node = dependencies[name] or {}
        version = node.get("version", "<sem-versao>")
        logical_path = f"{prefix}>{name}@{version}" if prefix else f"{name}@{version}"
        lines.append(logical_path)
        walk(node.get("dependencies") or {}, logical_path)


walk(data.get("dependencies") or {})
destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

build_image() {
  local component=$1
  local round=$2
  local tag="clinicai-${component}:chk02-${round}"
  local log="$EVIDENCE_DIR/build-${component}-${round}.log"

  CURRENT_COMPONENT=$component
  CURRENT_ROUND=$round
  echo
  echo "==> Construindo $tag sem cache"
  DOCKER_BUILDKIT=1 docker build \
    --no-cache \
    --progress=plain \
    --tag "$tag" \
    "$ROOT_DIR/$component" \
    2>&1 | tee "$log"

  docker image inspect "$tag" >"$EVIDENCE_DIR/image-${component}-${round}.json"
}

capture_frontend_tree() {
  local round=$1
  local tag="clinicai-frontend:chk02-${round}"
  local raw="$EVIDENCE_DIR/tree-frontend-${round}.json"
  local output="$EVIDENCE_DIR/tree-frontend-${round}.txt"

  docker run --rm --entrypoint sh "$tag" -lc \
    'node --version; npm --version; npm config get registry' \
    >"$EVIDENCE_DIR/versions-frontend-${round}.txt"

  # Sem pipe: se npm ls detectar dependência inválida, o teste falha de fato.
  docker run --rm --entrypoint npm "$tag" ls --all --json >"$raw"
  canonicalize_npm_tree "$raw" "$output"
}

capture_python_tree() {
  local component=$1
  local round=$2
  local tag="clinicai-${component}:chk02-${round}"
  local unsorted="$EVIDENCE_DIR/tree-${component}-${round}.unsorted.txt"
  local output="$EVIDENCE_DIR/tree-${component}-${round}.txt"

  docker run --rm --entrypoint sh "$tag" -lc \
    'python --version; python -m pip --version' \
    >"$EVIDENCE_DIR/versions-${component}-${round}.txt"

  docker run --rm --entrypoint python "$tag" -m pip check \
    >"$EVIDENCE_DIR/pip-check-${component}-${round}.txt"
  docker run --rm --entrypoint python "$tag" -m pip freeze --all >"$unsorted"
  LC_ALL=C sort "$unsorted" >"$output"
  rm -f "$unsorted"
}

compare_component() {
  local component=$1
  local first="$EVIDENCE_DIR/tree-${component}-a.txt"
  local second="$EVIDENCE_DIR/tree-${component}-b.txt"

  if ! cmp -s "$first" "$second"; then
    diff -u "$first" "$second" >"$EVIDENCE_DIR/diff-${component}.txt" || true
    echo "Falha: a árvore de dependências de $component mudou entre os builds." >&2
    return 1
  fi

  sha256sum "$first" >"$EVIDENCE_DIR/sha256-${component}.txt"
  echo "OK: $component produziu a mesma árvore nas duas construções."
}

for component in frontend backend ai; do
  for round in a b; do
    build_image "$component" "$round"
    if [[ "$component" == "frontend" ]]; then
      capture_frontend_tree "$round"
    else
      capture_python_tree "$component" "$round"
    fi
  done
  compare_component "$component"
done

CURRENT_COMPONENT="finalização"
CURRENT_ROUND="-"
cat >"$EVIDENCE_DIR/result.txt" <<EOF
CHK-02 aprovado.
Data UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')
Critério: duas construções consecutivas sem cache produziram a mesma árvore de dependências para frontend, backend e IA.
Registry npm: https://registry.npmjs.org/
EOF

echo
echo "CHK-02 aprovado. Evidências gravadas em: $EVIDENCE_DIR"
