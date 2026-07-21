"""Compatibilidade entre mapas novos, legados e demonstrativos."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.modules.ai_analyses import (
    file_storage,
)


@pytest.fixture
def isolated_attribution_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path]:
    data_root = (
        tmp_path
        / "data"
    )
    legacy_root = (
        tmp_path
        / "storage"
        / "gradcam"
    )
    demo_root = (
        tmp_path
        / "demo_assets"
        / "gradcam"
    )

    monkeypatch.setattr(
        file_storage,
        "DATA_DIR",
        data_root,
    )
    monkeypatch.setattr(
        file_storage,
        "NEW_ATTRIBUTION_DIR",
        data_root / "attribution",
    )
    monkeypatch.setattr(
        file_storage,
        "AI_STORAGE_DIR",
        legacy_root.parent,
    )
    monkeypatch.setattr(
        file_storage,
        "GRADCAM_DIR",
        legacy_root,
    )
    monkeypatch.setattr(
        file_storage,
        "DEMO_GRADCAM_DIR",
        demo_root,
    )

    return (
        data_root,
        legacy_root,
        demo_root,
    )


def test_resolves_relative_new_and_absolute_legacy_maps(
    isolated_attribution_roots: tuple[
        Path,
        Path,
        Path,
    ],
) -> None:
    (
        data_root,
        legacy_root,
        demo_root,
    ) = isolated_attribution_roots

    new_map = (
        data_root
        / "attribution"
        / "novo.jpg"
    )
    legacy_map = (
        legacy_root
        / "legado.png"
    )
    demo_map = (
        demo_root
        / "demonstrativo.jpeg"
    )

    for path, content in (
        (
            new_map,
            b"novo",
        ),
        (
            legacy_map,
            b"legado",
        ),
        (
            demo_map,
            b"demo",
        ),
    ):
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_bytes(
            content
        )

    assert (
        file_storage.resolve_safe_gradcam_path(
            "attribution/novo.jpg"
        )
        == new_map.resolve()
    )

    assert (
        file_storage.resolve_safe_gradcam_path(
            str(
                legacy_map
            )
        )
        == legacy_map.resolve()
    )

    assert (
        file_storage.resolve_safe_gradcam_path(
            str(
                demo_map
            )
        )
        == demo_map.resolve()
    )


def test_serializes_new_map_and_preserves_legacy_absolute_path(
    isolated_attribution_roots: tuple[
        Path,
        Path,
        Path,
    ],
) -> None:
    (
        data_root,
        legacy_root,
        _,
    ) = isolated_attribution_roots

    new_map = (
        data_root
        / "attribution"
        / "mapa.jpg"
    )
    legacy_map = (
        legacy_root
        / "mapa.jpg"
    )

    assert (
        file_storage.serialize_gradcam_path(
            new_map
        )
        == "attribution/mapa.jpg"
    )

    assert (
        file_storage.serialize_gradcam_path(
            legacy_map
        )
        == str(
            legacy_map.resolve(
                strict=False
            )
        )
    )


def test_rejects_external_traversal_and_invalid_extension(
    isolated_attribution_roots: tuple[
        Path,
        Path,
        Path,
    ],
    tmp_path: Path,
) -> None:
    data_root, _, _ = (
        isolated_attribution_roots
    )

    outside = (
        tmp_path
        / "outside.jpg"
    )
    outside.write_bytes(
        b"outside"
    )

    with pytest.raises(
        HTTPException
    ) as external_error:
        file_storage.resolve_safe_gradcam_path(
            str(
                outside
            )
        )

    assert (
        external_error.value.status_code
        == 403
    )

    with pytest.raises(
        HTTPException
    ) as traversal_error:
        file_storage.resolve_safe_gradcam_path(
            "../outside.jpg"
        )

    assert (
        traversal_error.value.status_code
        == 403
    )

    invalid = (
        data_root
        / "attribution"
        / "mapa.txt"
    )
    invalid.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    invalid.write_text(
        "não é imagem",
        encoding="utf-8",
    )

    with pytest.raises(
        HTTPException
    ) as extension_error:
        file_storage.resolve_safe_gradcam_path(
            "attribution/mapa.txt"
        )

    assert (
        extension_error.value.status_code
        == 415
    )


def test_missing_relative_map_returns_404(
    isolated_attribution_roots: tuple[
        Path,
        Path,
        Path,
    ],
) -> None:
    with pytest.raises(
        HTTPException
    ) as missing_error:
        file_storage.resolve_safe_gradcam_path(
            "attribution/ausente.jpg"
        )

    assert (
        missing_error.value.status_code
        == 404
    )
