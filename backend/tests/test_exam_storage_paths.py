"""Resolução segura dos caminhos canônicos dos exames."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.modules.exams import file_storage


@pytest.fixture
def isolated_exam_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    data_root = tmp_path / "data"

    monkeypatch.setattr(
        file_storage,
        "DATA_DIR",
        data_root,
    )

    monkeypatch.setattr(
        file_storage,
        "UPLOAD_DIR",
        data_root / "exams",
    )

    return data_root


def test_resolves_canonical_relative_path(
    isolated_exam_storage: Path,
) -> None:
    image = (
        isolated_exam_storage
        / "exams"
        / "1"
        / "2"
        / "3"
        / "original"
        / "imagem.jpg"
    )

    image.parent.mkdir(
        parents=True
    )
    image.write_bytes(
        b"imagem"
    )

    resolved = (
        file_storage
        .resolve_safe_exam_file_path(
            (
                "exams/1/2/3/"
                "original/imagem.jpg"
            )
        )
    )

    assert resolved == image.resolve()


def test_serializes_canonical_path(
    isolated_exam_storage: Path,
) -> None:
    image = (
        isolated_exam_storage
        / "exams"
        / "4"
        / "5"
        / "6"
        / "original"
        / "imagem.png"
    )

    reference = (
        file_storage
        .serialize_exam_file_path(
            image
        )
    )

    assert reference == (
        "exams/4/5/6/original/"
        "imagem.png"
    )


@pytest.mark.parametrize(
    "invalid_path",
    (
        "../outside.jpg",
        "outside.jpg",
        "exams/1/2/3/imagem.jpg",
        (
            "exams/1/2/3/"
            "attribution/imagem.jpg"
        ),
        (
            "exams/0/2/3/"
            "original/imagem.jpg"
        ),
        (
            "exams/1/2/3/"
            "original/pasta/imagem.jpg"
        ),
    ),
)
def test_rejects_noncanonical_paths(
    isolated_exam_storage: Path,
    invalid_path: str,
) -> None:
    with pytest.raises(
        HTTPException
    ) as error:
        (
            file_storage
            .resolve_safe_exam_file_path(
                invalid_path
            )
        )

    assert error.value.status_code == 403


def test_rejects_absolute_path(
    isolated_exam_storage: Path,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(
        b"outside"
    )

    with pytest.raises(
        HTTPException
    ) as error:
        (
            file_storage
            .resolve_safe_exam_file_path(
                str(outside)
            )
        )

    assert error.value.status_code == 403


def test_resolves_missing_canonical_file_without_creating_it(
    isolated_exam_storage: Path,
) -> None:
    resolved = (
        file_storage
        .resolve_safe_exam_file_path(
            (
                "exams/1/2/3/"
                "original/ausente.jpg"
            )
        )
    )

    expected = (
        isolated_exam_storage
        / "exams"
        / "1"
        / "2"
        / "3"
        / "original"
        / "ausente.jpg"
    ).resolve(
        strict=False
    )

    assert resolved == expected
    assert not resolved.exists()


def test_safe_delete_removes_canonical_file(
    isolated_exam_storage: Path,
) -> None:
    image = (
        isolated_exam_storage
        / "exams"
        / "7"
        / "8"
        / "9"
        / "original"
        / "imagem.jpg"
    )

    image.parent.mkdir(
        parents=True
    )
    image.write_bytes(
        b"imagem"
    )

    deleted = (
        file_storage
        .delete_exam_file_safely(
            (
                "exams/7/8/9/"
                "original/imagem.jpg"
            )
        )
    )

    assert deleted is True
    assert not image.exists()
