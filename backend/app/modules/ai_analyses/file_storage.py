"""Resolução segura dos mapas de atribuição produzidos ou versionados."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings
from app.modules.academic_demo_assets import (
    BUNDLED_DEMO_ASSETS_DIR,
)


DATA_DIR = Path(
    settings.clinicai_data_dir
)
NEW_ATTRIBUTION_DIR = (
    DATA_DIR
    / "attribution"
)

# Caminhos legados preservados durante a migração.
AI_STORAGE_DIR = Path(
    settings.ai_storage_dir
)
GRADCAM_DIR = (
    AI_STORAGE_DIR
    / "gradcam"
)

DEMO_GRADCAM_DIR = (
    BUNDLED_DEMO_ASSETS_DIR
    / "gradcam"
)

ALLOWED_GRADCAM_SUFFIXES = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
    }
)


def _allowed_attribution_roots() -> tuple[Path, ...]:
    roots = (
        NEW_ATTRIBUTION_DIR,
        GRADCAM_DIR,
        DEMO_GRADCAM_DIR,
    )

    unique_roots: list[Path] = []

    for root in roots:
        resolved_root = root.resolve(
            strict=False
        )

        if resolved_root not in unique_roots:
            unique_roots.append(
                resolved_root
            )

    return tuple(
        unique_roots
    )


def serialize_gradcam_path(
    file_path: Path,
) -> str:
    """Serializa mapas novos relativamente à raiz data."""

    resolved_path = file_path.resolve(
        strict=False
    )
    data_root = DATA_DIR.resolve(
        strict=False
    )

    try:
        relative_path = (
            resolved_path.relative_to(
                data_root
            )
        )
    except ValueError:
        # Caminhos legados e ativos versionados permanecem absolutos.
        return str(
            resolved_path
        )

    return relative_path.as_posix()


def _resolve_candidate(
    stored_path: str,
) -> Path:
    raw_path = Path(
        stored_path
    )

    if raw_path.is_absolute():
        return raw_path

    if ".." in raw_path.parts:
        raise HTTPException(
            status_code=403,
            detail=(
                "O caminho do mapa de "
                "atribuição não é permitido."
            ),
        )

    return (
        DATA_DIR
        / raw_path
    )


def _is_inside_allowed_root(
    resolved: Path,
) -> bool:
    for root in _allowed_attribution_roots():
        try:
            resolved.relative_to(
                root
            )
            return True
        except ValueError:
            continue

    return False


def resolve_safe_gradcam_path(
    stored_path: str | None,
) -> Path:
    """Resolve mapa relativo novo ou caminho absoluto legado autorizado."""

    if not stored_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "Este exame não possui mapa "
                "de atribuição disponível."
            ),
        )

    candidate = _resolve_candidate(
        stored_path
    )

    if candidate.is_symlink():
        raise HTTPException(
            status_code=403,
            detail=(
                "O caminho do mapa de "
                "atribuição não é permitido."
            ),
        )

    try:
        resolved = candidate.resolve(
            strict=True
        )
    except (
        FileNotFoundError,
        OSError,
    ) as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "O mapa de atribuição não foi "
                "encontrado no armazenamento autorizado."
            ),
        ) from exc

    if not _is_inside_allowed_root(
        resolved
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "O caminho do mapa de atribuição "
                "está fora do armazenamento autorizado."
            ),
        )

    if (
        resolved.suffix.lower()
        not in ALLOWED_GRADCAM_SUFFIXES
    ):
        raise HTTPException(
            status_code=415,
            detail=(
                "O mapa de atribuição possui "
                "formato não permitido."
            ),
        )

    if not resolved.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "O mapa de atribuição não é "
                "um arquivo válido."
            ),
        )

    return resolved
