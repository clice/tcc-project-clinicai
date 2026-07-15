#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODEL_DIR="ai/models/exported/gastrointestinal"
REQUIRED_MODEL_FILES=(
  "resnet50.pt"
  "efficientnet_b4.pt"
  "pvt_v2_b2.pt"
  "meta_classificador.joblib"
  "manifesto_modelos.json"
)

printf '[CHK-12] Conferindo os artefatos locais...\n'
missing=0
for filename in "${REQUIRED_MODEL_FILES[@]}"; do
  if [[ ! -f "$MODEL_DIR/$filename" ]]; then
    printf '  AUSENTE: %s\n' "$MODEL_DIR/$filename" >&2
    missing=1
  fi
done
if [[ "$missing" -ne 0 ]]; then
  cat >&2 <<'EOF'
[CHK-12] Instale os modelos antes de continuar:
  docker compose --profile models run --rm model-downloader
EOF
  exit 1
fi

printf '[CHK-12] Validando o Docker Compose...\n'
docker compose config --quiet

printf '[CHK-12] Construindo backend e serviço de IA...\n'
docker compose build backend ai

printf '[CHK-12] Executando testes unitários do serviço de IA...\n'
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  ai -m unittest discover -s tests -p 'test_*.py' -v

printf '[CHK-12] Executando testes do cliente e persistência no backend...\n'
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m pytest -q \
  tests/test_ai_service_contract.py \
  tests/test_audit_integrity.py

printf '[CHK-12] Subindo o serviço de IA para os testes HTTP reais...\n'
docker compose up -d ai

printf '[CHK-12] Aguardando /health confirmar quatro artefatos carregados...\n'
ready=0
for _attempt in $(seq 1 120); do
  if docker compose exec -T ai python - <<'PY' >/dev/null 2>&1
import json
from urllib.request import urlopen

with urlopen("http://127.0.0.1:8001/health", timeout=5) as response:
    payload = json.load(response)
assert response.status == 200
assert payload["ready"] is True
assert payload["artifact_summary"] == {"expected": 4, "loaded": 4}
PY
  then
    ready=1
    break
  fi
  sleep 2
done
if [[ "$ready" -ne 1 ]]; then
  printf '[CHK-12] O serviço não ficou pronto. Logs do container:\n' >&2
  docker compose logs --tail=200 ai >&2
  exit 1
fi

printf '[CHK-12] Validando /health e /models...\n'
docker compose exec -T ai python - <<'PY'
import json
from urllib.request import urlopen

with urlopen("http://127.0.0.1:8001/health", timeout=10) as response:
    health = json.load(response)
assert health["status"] == "ok"
assert health["ready"] is True
assert health["device"]["type"] in {"cpu", "cuda"}
assert health["artifact_summary"] == {"expected": 4, "loaded": 4}
assert health["domains"]["gastrointestinal"]["loaded"] is True

with urlopen("http://127.0.0.1:8001/models", timeout=10) as response:
    models = json.load(response)
gastro = models["domains"]["gastrointestinal"]
assert gastro["active_model"] == "ensemble_stacking"
assert gastro["exam_types"] == ["colonoscopy", "endoscopy"]
assert gastro["classes"] == {"0": "normal", "1": "abnormal"}
assert gastro["loaded"] is True
assert len(gastro["artifacts"]) == 4
assert all(item["exists"] and item["loaded"] for item in gastro["artifacts"])
assert gastro["model_version"]
print(json.dumps({"health": health, "gastrointestinal": gastro}, indent=2, ensure_ascii=False))
PY

printf '[CHK-12] Validando imagem inválida, domínio desconhecido e inferência gastrointestinal...\n'
docker compose exec -T ai python - <<'PY'
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from PIL import Image


def multipart(image_bytes: bytes, *, exam_type: str) -> tuple[bytes, str]:
    boundary = f"----clinicai-{uuid4().hex}"
    chunks = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="exam_type"\r\n\r\n',
        exam_type.encode(),
        b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="file"; filename="exam.png"\r\n',
        b"Content-Type: image/png\r\n\r\n",
        image_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    return b"".join(chunks), boundary


def post(image_bytes: bytes, exam_type: str, timeout: int = 30):
    body, boundary = multipart(image_bytes, exam_type=exam_type)
    request = Request(
        "http://127.0.0.1:8001/predict",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    return urlopen(request, timeout=timeout)

try:
    post(b"not-an-image", "endoscopy")
    raise AssertionError("imagem inválida deveria retornar 422")
except HTTPError as exc:
    assert exc.code == 422, exc.read().decode()

image_buffer = BytesIO()
Image.new("RGB", (320, 240), (80, 120, 160)).save(image_buffer, format="PNG")
image_bytes = image_buffer.getvalue()

try:
    post(image_bytes, "mammography")
    raise AssertionError("domínio desconhecido deveria retornar 422")
except HTTPError as exc:
    assert exc.code == 422, exc.read().decode()

with post(image_bytes, "colonoscopy", timeout=300) as response:
    prediction = json.load(response)
assert prediction["exam_type"] == "colonoscopy"
assert prediction["exam_domain"] == "gastrointestinal"
assert prediction["prediction_class"] in {0, 1}
assert prediction["label"] in {"normal", "abnormal"}
assert 0 <= prediction["confidence"] <= 1
assert prediction["model_name"] == "ensemble_stacking"
assert prediction["model_version"]
assert prediction["device"] in {"cpu", "cuda", "cuda:0"}
assert prediction["gradcam_available"] is True
assert prediction["gradcam_path"]
assert Path(prediction["gradcam_path"]).is_file()
print(json.dumps(prediction, indent=2, ensure_ascii=False))
PY

printf '[CHK-12] Executando a suíte completa do backend...\n'
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m pytest -q

printf '[CHK-12] Validando contrato de exames e build do frontend...\n'
docker compose run --rm --no-deps \
  -v "$ROOT_DIR:/workspace" \
  -w /workspace/frontend \
  frontend npm run check:exams

docker compose run --rm --no-deps frontend npm run build

printf '[CHK-12] Compilando módulos Python...\n'
docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  backend -m compileall -q app tests

docker compose run --rm --no-deps \
  --entrypoint python \
  -w /app \
  ai -m compileall -q app tests

printf '[CHK-12] Validação concluída com sucesso.\n'
printf '[CHK-12] O container ai permanece ativo; use docker compose stop ai quando apropriado.\n'
