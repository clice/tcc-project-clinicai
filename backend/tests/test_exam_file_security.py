"""CHK-10 — upload, armazenamento seguro, retenção e download por escopo."""

from __future__ import annotations
from datetime import date

import base64
import os
import stat
import struct
import zlib
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.modules.audit_logs.model import AuditLog
from app.modules.clinics.model import Clinic
from app.modules.exams import file_storage
from app.modules.exams.file_storage import (
    delete_exam_file_safely,
    resolve_safe_exam_file_path,
    store_validated_exam_file,
    validate_exam_file,
)
from app.modules.exams.model import Exam
from app.modules.exams.service import (
    cancel_exam,
    download_exam_file,
    preview_exam_file,
    replace_exam_file,
)
from app.modules.patients.model import Patient
from app.modules.roles.model import Role
from app.modules.statuses.model import Status
from app.modules.users.model import User


VALID_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8L"
    "CwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUF"
    "BQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4e"
    "Hh4eHh4eHh4eHh4eHh4eHh7/wAARCAADAAIDASIAAhEBAxEB/8QAHwAAAQUBAQE"
    "BAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQ"
    "RBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY"
    "3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJW"
    "Wl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5u"
    "fo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8"
    "QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSM"
    "zUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGV"
    "mZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm"
    "6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxE"
    "APwD5fooorrOU/9k="
)


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def make_png(width: int = 2, height: int = 2) -> bytes:
    """Gera PNG RGB não entrelaçado, suficiente para validação estrutural."""

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    rows = b"".join(b"\x00" + (b"\x14\x1e\x28" * width) for _ in range(height))
    return (
        file_storage.PNG_SIGNATURE
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(rows))
        + _png_chunk(b"IEND", b"")
    )


def make_dimension_only_png(width: int, height: int) -> bytes:
    """O limite é rejeitado no IHDR, antes de descompactar os pixels."""

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        file_storage.PNG_SIGNATURE
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(b"\x00"))
        + _png_chunk(b"IEND", b"")
    )


def upload(data: bytes, *, filename: str, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def assert_http_error(expected_status: int, call) -> HTTPException:
    with pytest.raises(HTTPException) as error:
        call()
    assert error.value.status_code == expected_status
    return error.value


@pytest.fixture
def isolated_upload_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_root = tmp_path / "uploads"
    upload_root = data_root / "exams"
    monkeypatch.setattr(file_storage, "DATA_DIR", data_root)
    monkeypatch.setattr(file_storage, "UPLOAD_DIR", upload_root)
    return upload_root


def test_valid_png_and_jpeg_are_identified_from_real_bytes() -> None:
    png = validate_exam_file(upload(make_png(3, 4), filename="imagem.png", content_type="image/png"))
    jpeg = validate_exam_file(upload(VALID_JPEG, filename="imagem.jpeg", content_type="image/jpeg"))

    assert (png.mime_type, png.extension, png.width, png.height) == ("image/png", ".png", 3, 4)
    assert (jpeg.mime_type, jpeg.extension, jpeg.width, jpeg.height) == ("image/jpeg", ".jpg", 2, 3)
    assert len(png.sha256) == len(jpeg.sha256) == 64


@pytest.mark.parametrize(
    ("file_data", "filename", "declared_mime", "status_code"),
    (
        (make_png(), "imagem.png", "image/jpeg", 415),
        (make_png(), "imagem.jpg", "image/png", 415),
        (b"conteudo executavel", "ataque.png", "image/png", 415),
        (make_png()[:-8], "truncada.png", "image/png", 400),
        (VALID_JPEG[:-2], "truncada.jpg", "image/jpeg", 400),
    ),
)
def test_spoofed_or_corrupted_inputs_return_4xx(
    file_data: bytes,
    filename: str,
    declared_mime: str,
    status_code: int,
) -> None:
    assert_http_error(
        status_code,
        lambda: validate_exam_file(
            upload(file_data, filename=filename, content_type=declared_mime)
        ),
    )


def test_png_with_invalid_crc_returns_400() -> None:
    corrupted = bytearray(make_png())
    corrupted[29] ^= 0xFF
    assert_http_error(
        400,
        lambda: validate_exam_file(
            upload(bytes(corrupted), filename="corrompida.png", content_type="image/png")
        ),
    )


def test_size_and_dimension_limits_return_413(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_storage, "MAX_FILE_SIZE", 32)
    assert_http_error(
        413,
        lambda: validate_exam_file(
            upload(make_png(), filename="grande.png", content_type="image/png")
        ),
    )

    monkeypatch.setattr(file_storage, "MAX_FILE_SIZE", 10_000_000)
    assert_http_error(
        413,
        lambda: validate_exam_file(
            upload(
                make_dimension_only_png(file_storage.MAX_IMAGE_WIDTH + 1, 1),
                filename="larga.png",
                content_type="image/png",
            )
        ),
    )
    assert_http_error(
        413,
        lambda: validate_exam_file(
            upload(
                make_dimension_only_png(8_000, 6_000),
                filename="pixel-bomb.png",
                content_type="image/png",
            )
        ),
    )


def test_original_name_never_controls_physical_path_and_modes_are_restricted(
    isolated_upload_root: Path,
) -> None:
    original_name = "../../etc/passwd.png"
    image = validate_exam_file(
        upload(make_png(), filename=original_name, content_type="image/png")
    )
    stored = store_validated_exam_file(image, clinic_id=7, patient_id=11, exam_id=13)

    assert stored.read_bytes() == image.data
    assert stored.name != Path(original_name).name
    assert stored.name.endswith(".png")
    assert len(stored.stem) == 32
    assert stored.parent == isolated_upload_root / "7" / "11" / "13" / "original"
    assert stat.S_IMODE(stored.stat().st_mode) == file_storage.FILE_MODE
    for directory in (isolated_upload_root, *stored.parents[:4]):
        assert stat.S_IMODE(directory.stat().st_mode) == file_storage.DIRECTORY_MODE


def test_exclusive_creation_prevents_overwrite(
    isolated_upload_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = validate_exam_file(upload(make_png(), filename="imagem.png", content_type="image/png"))
    values = iter(["a" * 32, "a" * 32, "b" * 32])
    monkeypatch.setattr(file_storage, "uuid4", lambda: SimpleNamespace(hex=next(values)))

    first = store_validated_exam_file(image, clinic_id=1, patient_id=2, exam_id=3)
    first_before = first.read_bytes()
    second = store_validated_exam_file(image, clinic_id=1, patient_id=2, exam_id=3)

    assert first.name == f"{'a' * 32}.png"
    assert second.name == f"{'b' * 32}.png"
    assert first != second
    assert first.read_bytes() == first_before


def test_path_traversal_and_symlink_are_rejected(
    isolated_upload_root: Path,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "segredo.png"
    outside.write_bytes(make_png())
    assert_http_error(403, lambda: resolve_safe_exam_file_path(str(outside)))

    isolated_upload_root.mkdir(parents=True, exist_ok=True)
    link = isolated_upload_root / "link.png"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Ambiente sem suporte a symlink: {exc}")
    assert_http_error(403, lambda: resolve_safe_exam_file_path(str(link)))


def test_safe_deletion_never_removes_external_file_and_cleans_empty_folders(
    isolated_upload_root: Path,
    tmp_path: Path,
) -> None:
    image = validate_exam_file(upload(make_png(), filename="imagem.png", content_type="image/png"))
    stored = store_validated_exam_file(image, clinic_id=1, patient_id=2, exam_id=3)
    exam_dir = stored.parent

    external = tmp_path / "externo.png"
    external.write_bytes(make_png())

    assert delete_exam_file_safely(str(external)) is False
    assert external.exists()
    assert (
        delete_exam_file_safely(
            file_storage.serialize_exam_file_path(stored)
        )
        is True
    )
    assert not stored.exists()
    assert not exam_dir.exists()


def _seed_download_context(db_session, physical_file: Path):
    active_user = Status(name="active", display_name="Ativo", applies_to="user")
    active_clinic = Status(name="active", display_name="Ativa", applies_to="clinic")
    active_patient = Status(name="active", display_name="Ativo", applies_to="patient")
    pending = Status(name="pending", display_name="Pendente", applies_to="exam")
    canceled = Status(name="canceled", display_name="Cancelado", applies_to="exam")
    manager_role = Role(name="clinic_manager", display_name="Gestor", permissions_initialized=True)
    doctor_role = Role(name="doctor", display_name="Médico", permissions_initialized=True)
    clinic_a = Clinic(name="Clínica A", cnpj="11222333000181", status=active_clinic)
    clinic_b = Clinic(name="Clínica B", cnpj="11444777000161", status=active_clinic)
    doctor_a = User(
        name="Médico A",
        email="medico.upload.a@example.com",
        cpf="52998224725",
        password_hash="hash",
        role=doctor_role,
        status=active_user,
        clinic=clinic_a,
    )
    patient = Patient(
        name="Paciente A",
        cpf="16899535009",
        clinic=clinic_a,
        doctor=doctor_a,
        status=active_patient,
        birth_date=date(1978, 3, 12),
        sex="male",
        phone="88999991003",
    )
    manager_a = User(
        name="Gestor A",
        email="manager.upload.a@example.com",
        cpf="12345678909",
        password_hash="hash",
        role=manager_role,
        status=active_user,
        clinic=clinic_a,
    )
    manager_b = User(
        name="Gestor B",
        email="manager.upload.b@example.com",
        cpf="39053344705",
        password_hash="hash",
        role=manager_role,
        status=active_user,
        clinic=clinic_b,
    )
    exam = Exam(
        clinic=clinic_a,
        patient=patient,
        doctor=doctor_a,
        status=pending,
        exam_type="colonoscopy",
        description="Exame protegido",
        file_path=file_storage.serialize_exam_file_path(physical_file),
        file_name=physical_file.name,
        file_mime_type="image/png",
    )
    db_session.add_all(
        [
            active_user,
            active_clinic,
            active_patient,
            pending,
            canceled,
            manager_role,
            doctor_role,
            clinic_a,
            clinic_b,
            doctor_a,
            patient,
            manager_a,
            manager_b,
            exam,
        ]
    )
    db_session.commit()
    return exam, doctor_a, manager_a, manager_b


def test_download_is_scoped_to_clinic_and_audited(
    db_session,
    isolated_upload_root: Path,
) -> None:
    physical_file = (
        isolated_upload_root
        / "1"
        / "1"
        / "1"
        / "original"
        / "arquivo.png"
    )
    physical_file.parent.mkdir(parents=True)
    physical_file.write_bytes(make_png())
    exam, doctor, manager_a, manager_b = _seed_download_context(
        db_session,
        physical_file,
    )

    assert_http_error(
        403,
        lambda: download_exam_file(db_session, exam.id, manager_b),
    )
    assert_http_error(
        403,
        lambda: download_exam_file(db_session, exam.id, manager_a),
    )
    assert db_session.query(AuditLog).filter(AuditLog.action == "download").count() == 0

    preview_response = preview_exam_file(
        db_session,
        exam.id,
        doctor,
    )

    assert Path(preview_response.path) == physical_file
    assert preview_response.media_type == "image/png"
    assert preview_response.headers[
        "content-disposition"
    ].startswith("inline;")
    assert (
        preview_response.headers["cache-control"]
        == "private, no-store"
    )

    assert (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "download")
        .count()
        == 0
    )

    response = download_exam_file(
        db_session,
        exam.id,
        doctor,
    )

    assert Path(response.path) == physical_file
    assert response.media_type == "image/png"

    disposition = response.headers[
        "content-disposition"
    ]

    assert disposition.startswith("attachment;")
    assert response.headers["cache-control"] == "no-store"
    assert (
        f'exame-{exam.id}-paciente-a-sem-data.png'
        in disposition
    )

    logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "download")
        .all()
    )

    assert len(logs) == 1
    assert (
        logs[0].new_data["download_name"]
        == f"exame-{exam.id}-paciente-a-sem-data.png"
    )
    assert logs[0].new_data["delivery_mode"] == "attachment"


def test_cancel_retains_file_and_replace_deletes_only_old_file(
    db_session,
    isolated_upload_root: Path,
) -> None:
    old_file = (
        isolated_upload_root
        / "1"
        / "1"
        / "1"
        / "original"
        / "antigo.png"
    )
    old_file.parent.mkdir(parents=True)
    old_file.write_bytes(make_png())
    exam, doctor, manager, _ = _seed_download_context(
        db_session,
        old_file,
    )

    cancel_exam(db_session, exam.id, doctor)
    assert old_file.exists(), "Cancelamento é lógico e deve reter o arquivo."

    # Retoma diretamente para pending para isolar a política física de troca.
    db_session.refresh(exam)
    pending = db_session.query(Status).filter_by(name="pending", applies_to="exam").one()
    exam.status_id = pending.id
    db_session.commit()

    assert_http_error(
        403,
        lambda: replace_exam_file(
            db_session,
            exam.id,
            upload(
                make_png(4, 3),
                filename="negado.png",
                content_type="image/png",
            ),
            manager,
        ),
    )
    assert old_file.exists()

    doctor = exam.doctor
    assert doctor is not None

    result = replace_exam_file(
        db_session,
        exam.id,
        upload(
            make_png(4, 3),
            filename="novo.png",
            content_type="image/png",
        ),
        doctor,
    )

    # O caminho físico permanece apenas no modelo interno e não deve fazer
    # parte da resposta pública devolvida pelo service.
    assert "file_path" not in result
    assert result["file_name"]

    db_session.refresh(exam)
    assert exam.file_path
    new_file = resolve_safe_exam_file_path(exam.file_path)
    assert new_file.exists()
    assert new_file != old_file
    assert not old_file.exists(), "Substituição confirmada deve remover a versão anterior."
