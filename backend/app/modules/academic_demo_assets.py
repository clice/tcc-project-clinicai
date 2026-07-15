"""Instalação e validação dos ativos versionados da massa acadêmica."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.modules.exams.file_storage import build_exam_storage_dir

if TYPE_CHECKING:
    from app.modules.exams.model import Exam


BUNDLED_DEMO_ASSETS_DIR = Path(__file__).resolve().parents[2] / "demo_assets"
DEMO_ASSET_MANIFEST = BUNDLED_DEMO_ASSETS_DIR / "manifest.json"
DEMO_FILE_MODE = 0o600


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_demo_manifest() -> dict[str, Any]:
    """Carrega o manifesto versionado dos ativos acadêmicos."""

    try:
        payload = json.loads(DEMO_ASSET_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "O manifesto dos ativos acadêmicos não pôde ser carregado."
        ) from exc

    if payload.get("schema_version") != 1:
        raise RuntimeError("Versão inesperada do manifesto dos ativos acadêmicos.")

    return payload


def get_demo_asset_entry(asset_key: str) -> dict[str, Any]:
    """Retorna uma entrada do manifesto."""

    assets = get_demo_manifest().get("assets", {})
    entry = assets.get(asset_key)
    if not isinstance(entry, dict):
        raise RuntimeError(f"Ativo acadêmico desconhecido: {asset_key}.")
    return entry


def _bundled_asset_path(asset_key: str) -> tuple[Path, dict[str, Any]]:
    entry = get_demo_asset_entry(asset_key)
    relative_path = Path(str(entry["path"]))

    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise RuntimeError(f"Caminho inválido no manifesto: {relative_path}.")

    root = BUNDLED_DEMO_ASSETS_DIR.resolve(strict=True)
    source = (root / relative_path).resolve(strict=True)

    try:
        source.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("Ativo acadêmico fora do diretório versionado.") from exc

    if source.is_symlink() or not source.is_file():
        raise RuntimeError(f"Ativo acadêmico inválido: {source}.")

    if _sha256(source) != str(entry["sha256"]):
        raise RuntimeError(f"Hash divergente no ativo acadêmico: {source.name}.")

    if source.stat().st_size != int(entry["size_bytes"]):
        raise RuntimeError(f"Tamanho divergente no ativo acadêmico: {source.name}.")

    return source, entry


def verify_bundled_demo_assets() -> dict[str, str]:
    """Valida os quatro ativos versionados."""

    hashes: dict[str, str] = {}
    for key in (
        "normal_image",
        "abnormal_image",
        "normal_gradcam",
        "abnormal_gradcam",
    ):
        _, entry = _bundled_asset_path(key)
        hashes[key] = str(entry["sha256"])
    return hashes


def _copy_if_missing(source: Path, target: Path) -> Path:
    """Copia o ativo sem sobrescrever um arquivo persistido."""

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        if target.is_symlink() or not target.is_file():
            raise RuntimeError(f"Destino acadêmico inválido: {target}.")
        return target.resolve(strict=True)

    try:
        with source.open("rb") as input_file, target.open("xb") as output_file:
            for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
                output_file.write(chunk)
            output_file.flush()
            os.fsync(output_file.fileno())
        os.chmod(target, DEMO_FILE_MODE)
    except Exception:
        target.unlink(missing_ok=True)
        raise

    return target.resolve(strict=True)


def exam_asset_target(exam: "Exam", asset_key: str) -> Path:
    """Calcula o caminho determinístico do ativo de um exame demo."""

    _, entry = _bundled_asset_path(asset_key)
    storage_dir = build_exam_storage_dir(
        clinic_id=exam.clinic_id,
        patient_id=exam.patient_id,
        exam_id=exam.id,
    )
    return storage_dir / str(entry["filename"])


def install_exam_asset(
    exam: "Exam",
    asset_key: str,
    *,
    assign_fields: bool,
) -> Path:
    """Instala o JPEG acadêmico no volume de uploads."""

    source, entry = _bundled_asset_path(asset_key)
    target = _copy_if_missing(source, exam_asset_target(exam, asset_key))

    if assign_fields:
        exam.file_path = str(target)
        exam.file_name = str(entry["filename"])
        exam.file_mime_type = str(entry["mime_type"])

    return target


def bundled_gradcam_path(asset_key: str) -> Path:
    """Retorna um Grad-CAM versionado após validar hash e localização."""

    source, entry = _bundled_asset_path(asset_key)
    if entry.get("kind") != "gradcam":
        raise RuntimeError(f"O ativo {asset_key} não é um Grad-CAM.")
    return source
