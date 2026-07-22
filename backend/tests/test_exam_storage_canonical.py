"""Persistência das imagens na hierarquia canônica."""

from pathlib import Path

import pytest

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


def test_writes_under_exam_original_directory(
    isolated_exam_storage: Path,
) -> None:
    stored = (
        file_storage
        .store_validated_exam_file(
            build_image(),
            clinic_id=1,
            patient_id=2,
            exam_id=3,
        )
    )

    expected_directory = (
        isolated_exam_storage
        / "exams"
        / "1"
        / "2"
        / "3"
        / "original"
    )

    assert stored.parent == (
        expected_directory
    )

    assert stored.is_file()

    assert stored.read_bytes() == (
        b"clinicai-storage-test"
    )

    assert stored.suffix == ".jpg"


def test_serializes_and_resolves_stored_file(
    isolated_exam_storage: Path,
) -> None:
    stored = (
        file_storage
        .store_validated_exam_file(
            build_image(),
            clinic_id=4,
            patient_id=5,
            exam_id=6,
        )
    )

    reference = (
        file_storage
        .serialize_exam_file_path(
            stored
        )
    )

    assert reference == (
        "exams/4/5/6/original/"
        f"{stored.name}"
    )

    resolved = (
        file_storage
        .resolve_safe_exam_file_path(
            reference
        )
    )

    assert resolved == stored.resolve()


def test_successive_writes_use_distinct_file_names(
    isolated_exam_storage: Path,
) -> None:
    first = (
        file_storage
        .store_validated_exam_file(
            build_image(),
            clinic_id=7,
            patient_id=8,
            exam_id=9,
        )
    )

    second = (
        file_storage
        .store_validated_exam_file(
            build_image(),
            clinic_id=7,
            patient_id=8,
            exam_id=9,
        )
    )

    assert first != second
    assert first.name != second.name

    assert first.is_file()
    assert second.is_file()

    assert first.parent == second.parent

    assert first.parent == (
        isolated_exam_storage
        / "exams"
        / "7"
        / "8"
        / "9"
        / "original"
    )
