"""Resolução segura dos mapas Grad-CAM produzidos ou versionados."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings
from app.modules.academic_demo_assets import BUNDLED_DEMO_ASSETS_DIR


AI_STORAGE_DIR = Path(settings.ai_storage_dir)
GRADCAM_DIR = AI_STORAGE_DIR / "gradcam"
DEMO_GRADCAM_DIR = BUNDLED_DEMO_ASSETS_DIR / "gradcam"
ALLOWED_GRADCAM_SUFFIXES = frozenset({".jpg", ".jpeg", ".png"})


def _is_inside_allowed_root(resolved: Path) -> bool:
    roots = (
        GRADCAM_DIR.resolve(strict=False),
        DEMO_GRADCAM_DIR.resolve(strict=False),
    )
    for root in roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def resolve_safe_gradcam_path(stored_path: str | None) -> Path:
    """Resolve Grad-CAM regular dentro dos diretórios autorizados."""

    if not stored_path:
        raise HTTPException(
            status_code=404,
            detail="Este exame não possui mapa Grad-CAM disponível.",
        )

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
            detail="O mapa Grad-CAM não foi encontrado no armazenamento autorizado.",
        ) from exc

    if not _is_inside_allowed_root(resolved):
        raise HTTPException(
            status_code=403,
            detail="O caminho do Grad-CAM está fora do armazenamento autorizado.",
        )

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
