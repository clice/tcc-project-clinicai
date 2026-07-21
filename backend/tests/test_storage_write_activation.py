"""Ativação controlada da nova raiz de escrita do backend."""

from pathlib import Path

import pytest

from app.modules.exams import (
    file_storage,
)


def build_image() -> (
    file_storage.ValidatedExamImage
):
    return file_storage.ValidatedExamImage(
        data=b"clinicai-storage-test",
        mime_type="image/jpeg",
        extension=".jpg",
        width=1,
        height=1,
        sha256="0" * 64,
    )


def configure_roots(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    use_new_root: bool,
) -> tuple[Path, Path]:
    data_root = (
        tmp_path
        / "data"
    )
    new_root = (
        data_root
        / "exams"
    )
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
        new_root,
    )
    monkeypatch.setattr(
        file_storage,
        "LEGACY_UPLOAD_DIR",
        legacy_root,
    )
    monkeypatch.setattr(
        file_storage,
        "UPLOAD_DIR",
        (
            new_root
            if use_new_root
            else legacy_root
        ),
    )

    return (
        new_root,
        legacy_root,
    )


def test_new_root_writes_under_original_and_serializes_relative(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    new_root, _ = configure_roots(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        use_new_root=True,
    )

    stored = (
        file_storage
        .store_validated_exam_file(
            build_image(),
            clinic_id=1,
            patient_id=2,
            exam_id=3,
        )
    )

    assert stored.parent == (
        new_root
        / "1"
        / "2"
        / "3"
        / "original"
    )
    assert stored.read_bytes() == (
        b"clinicai-storage-test"
    )

    reference = (
        file_storage
        .serialize_exam_file_path(
            stored
        )
    )

    assert reference == (
        "exams/1/2/3/original/"
        f"{stored.name}"
    )
    assert (
        file_storage
        .resolve_safe_exam_file_path(
            reference
        )
        == stored.resolve()
    )


def test_legacy_root_keeps_previous_layout_and_absolute_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, legacy_root = configure_roots(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        use_new_root=False,
    )

    stored = (
        file_storage
        .store_validated_exam_file(
            build_image(),
            clinic_id=4,
            patient_id=5,
            exam_id=6,
        )
    )

    assert stored.parent == (
        legacy_root
        / "4"
        / "5"
        / "6"
    )
    assert (
        "original"
        not in stored.parent.parts
    )
    assert (
        file_storage
        .serialize_exam_file_path(
            stored
        )
        == str(
            stored.resolve()
        )
    )
