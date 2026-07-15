"""Resolução segura dos mapas Grad-CAM produzidos pelo serviço de IA."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings


AI_STORAGE_DIR = Path(settings.ai_storage_dir)
GRADCAM_DIR = AI_STORAGE_DIR / "gradcam"
ALLOWED_GRADCAM_SUFFIXES = frozenset({".jpg", ".jpeg", ".png"})


def resolve_safe_gradcam_path(stored_path: str | None) -> Path:
    """Retorna um Grad-CAM existente, regular e contido no diretório autorizado."""

    if not stored_path:
        raise HTTPException(
            status_code=404,
            detail="Este exame não possui mapa Grad-CAM disponível.",
        )

    root = GRADCAM_DIR.resolve(strict=False)
    candidate = Path(stored_path)

    if candidate.is_symlink():
        raise HTTPException(
            status_code=403,
            detail="O caminho do Grad-CAM não é permitido.",
        )

    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(
            status_code=404,
            detail="O mapa Grad-CAM não foi encontrado no armazenamento da IA.",
        ) from exc

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail="O caminho do Grad-CAM está fora do armazenamento autorizado.",
        ) from exc

    if resolved.suffix.lower() not in ALLOWED_GRADCAM_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail="O arquivo Grad-CAM possui formato não permitido.",
        )

    if not resolved.is_file():
        raise HTTPException(
            status_code=404,
            detail="O mapa Grad-CAM não é um arquivo válido.",
        )

    return resolved
