"""Compatibilidade entre a raiz data e os volumes legados."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.modules.exams import file_storage


@pytest.fixture
def isolated_storage_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    data_root = tmp_path / "data"
    legacy_root = (
        tmp_path
        / "uploads"
        / "exams"
    )

    monkeypatch.setattr(
        file_storage,
        "DATA_DIR",
        data_root,
    )
    monkeypatch.setattr(
        file_storage,
        "NEW_UPLOAD_DIR",
        data_root / "exams",
    )
    monkeypatch.setattr(
        file_storage,
        "LEGACY_UPLOAD_DIR",
        legacy_root,
    )
    monkeypatch.setattr(
        file_storage,
        "UPLOAD_DIR",
        legacy_root,
    )

    return data_root, legacy_root


def test_resolves_relative_new_and_absolute_legacy_paths(
    isolated_storage_roots: tuple[Path, Path],
) -> None:
    data_root, legacy_root = isolated_storage_roots

    new_file = (
        data_root
        / "exams"
        / "1"
        / "2"
        / "3"
        / "original"
        / "novo.jpg"
    )
    new_file.parent.mkdir(
        parents=True
    )
    new_file.write_bytes(
        b"novo"
    )

    legacy_file = (
        legacy_root
        / "1"
        / "2"
        / "3"
        / "legado.jpg"
    )
    legacy_file.parent.mkdir(
        parents=True
    )
    legacy_file.write_bytes(
        b"legado"
    )

    assert (
        file_storage
        .resolve_safe_exam_file_path(
            "exams/1/2/3/original/novo.jpg"
        )
        == new_file.resolve()
    )

    assert (
        file_storage
        .resolve_safe_exam_file_path(
            str(legacy_file)
        )
        == legacy_file.resolve()
    )


def test_serializes_new_path_and_preserves_legacy_absolute_path(
    isolated_storage_roots: tuple[Path, Path],
) -> None:
    data_root, legacy_root = isolated_storage_roots

    new_file = (
        data_root
        / "exams"
        / "4"
        / "5"
        / "6"
        / "original"
        / "imagem.png"
    )

    legacy_file = (
        legacy_root
        / "4"
        / "5"
        / "6"
        / "imagem.png"
    )

    assert (
        file_storage
        .serialize_exam_file_path(
            new_file
        )
        == (
            "exams/4/5/6/original/"
            "imagem.png"
        )
    )

    assert (
        file_storage
        .serialize_exam_file_path(
            legacy_file
        )
        == str(
            legacy_file.resolve(
                strict=False
            )
        )
    )


def test_rejects_external_and_traversal_paths(
    isolated_storage_roots: tuple[Path, Path],
    tmp_path: Path,
) -> None:
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
        file_storage.resolve_safe_exam_file_path(
            str(outside)
        )

    assert (
        external_error.value.status_code
        == 403
    )

    with pytest.raises(
        HTTPException
    ) as traversal_error:
        file_storage.resolve_safe_exam_file_path(
            "../outside.jpg"
        )

    assert (
        traversal_error.value.status_code
        == 403
    )


def test_safe_delete_supports_relative_new_path(
    isolated_storage_roots: tuple[Path, Path],
) -> None:
    data_root, _ = isolated_storage_roots

    new_file = (
        data_root
        / "exams"
        / "7"
        / "8"
        / "9"
        / "original"
        / "imagem.jpg"
    )
    new_file.parent.mkdir(
        parents=True
    )
    new_file.write_bytes(
        b"imagem"
    )

    assert (
        file_storage.delete_exam_file_safely(
            "exams/7/8/9/original/imagem.jpg"
        )
        is True
    )

    assert not new_file.exists()
    assert not (
        data_root
        / "exams"
        / "7"
    ).exists()
