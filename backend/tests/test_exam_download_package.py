"""Testes dos nomes públicos e do ZIP de imagens do exame."""

from datetime import date
from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

from app.modules.exams.service import (
    build_exam_download_filename,
    build_exam_images_package_bytes,
    build_exam_images_package_filename,
    build_gradcam_download_filename,
)


def build_exam():
    return SimpleNamespace(
        id=42,
        patient=SimpleNamespace(name="José da Silva"),
        exam_date=date(2026, 7, 18),
        file_mime_type="image/jpeg",
    )


def test_public_names_follow_the_closed_pattern(tmp_path) -> None:
    exam = build_exam()
    original_path = tmp_path / "stored-original.jpg"
    gradcam_path = tmp_path / "stored-gradcam.png"

    assert build_exam_download_filename(
        exam,
        original_path,
    ) == "exame-42-jose-da-silva-2026-07-18.jpg"

    assert build_gradcam_download_filename(
        exam,
        gradcam_path,
    ) == (
        "mapa-grad-cam-exame-42-jose-da-silva-"
        "2026-07-18.png"
    )

    assert build_exam_images_package_filename(exam) == (
        "imagens-exame-42-jose-da-silva-2026-07-18.zip"
    )


def test_zip_contains_only_the_two_public_names(tmp_path) -> None:
    original_path = tmp_path / "private-original.jpg"
    gradcam_path = tmp_path / "private-gradcam.png"
    original_path.write_bytes(b"original")
    gradcam_path.write_bytes(b"gradcam")

    package = build_exam_images_package_bytes(
        original_path=original_path,
        original_name="exame-42-paciente-2026-07-18.jpg",
        gradcam_path=gradcam_path,
        gradcam_name=(
            "mapa-grad-cam-exame-42-paciente-2026-07-18.png"
        ),
    )

    with ZipFile(BytesIO(package)) as archive:
        assert archive.namelist() == [
            "exame-42-paciente-2026-07-18.jpg",
            "mapa-grad-cam-exame-42-paciente-2026-07-18.png",
        ]
        assert archive.read(archive.namelist()[0]) == b"original"
        assert archive.read(archive.namelist()[1]) == b"gradcam"
