"""Persistência e resolução canônica dos mapas de atribuição."""

import base64
import hashlib
import struct
import zlib
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.modules.ai_analyses import file_storage


def build_png_chunk(
    chunk_type: bytes,
    payload: bytes,
) -> bytes:
    checksum = zlib.crc32(
        chunk_type
    )

    checksum = zlib.crc32(
        payload,
        checksum,
    ) & 0xFFFFFFFF

    return (
        struct.pack(
            ">I",
            len(payload),
        )
        + chunk_type
        + payload
        + struct.pack(
            ">I",
            checksum,
        )
    )


def build_valid_png() -> bytes:
    signature = bytes.fromhex(
        "89504e470d0a1a0a"
    )

    ihdr = struct.pack(
        ">IIBBBBB",
        1,
        1,
        8,
        2,
        0,
        0,
        0,
    )

    scanline = bytes.fromhex(
        "00000000"
    )

    return (
        signature
        + build_png_chunk(
            b"IHDR",
            ihdr,
        )
        + build_png_chunk(
            b"IDAT",
            zlib.compress(
                scanline
            ),
        )
        + build_png_chunk(
            b"IEND",
            b"",
        )
    )


VALID_PNG = build_valid_png()


@pytest.fixture
def isolated_attribution_storage(
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
        "EXAMS_DIR",
        data_root / "exams",
    )

    return data_root


def test_stores_map_in_exam_attribution_directory(
    isolated_attribution_storage: Path,
) -> None:
    stored = (
        file_storage
        .store_attribution_from_base64(
            encoded_data=(
                base64.b64encode(
                    VALID_PNG
                ).decode("ascii")
            ),
            mime_type="image/png",
            expected_sha256=(
                hashlib.sha256(
                    VALID_PNG
                ).hexdigest()
            ),
            clinic_id=1,
            patient_id=2,
            exam_id=3,
        )
    )

    assert stored.parent == (
        isolated_attribution_storage
        / "exams"
        / "1"
        / "2"
        / "3"
        / "attribution"
    )

    assert stored.is_file()
    assert stored.suffix == ".png"
    assert stored.read_bytes() == VALID_PNG


def test_serializes_and_resolves_stored_map(
    isolated_attribution_storage: Path,
) -> None:
    stored = (
        file_storage
        .store_attribution_from_base64(
            encoded_data=(
                base64.b64encode(
                    VALID_PNG
                ).decode("ascii")
            ),
            mime_type="image/png",
            expected_sha256=(
                hashlib.sha256(
                    VALID_PNG
                ).hexdigest()
            ),
            clinic_id=4,
            patient_id=5,
            exam_id=6,
        )
    )

    reference = (
        file_storage
        .serialize_gradcam_path(
            stored
        )
    )

    assert reference == (
        "exams/4/5/6/attribution/"
        f"{stored.name}"
    )

    resolved = (
        file_storage
        .resolve_safe_gradcam_path(
            reference
        )
    )

    assert resolved == stored.resolve()


@pytest.mark.parametrize(
    "invalid_path",
    (
        "../mapa.jpg",
        "/tmp/mapa.jpg",
        "attribution/mapa.jpg",
        (
            "exams/1/2/3/"
            "original/mapa.jpg"
        ),
        (
            "exams/0/2/3/"
            "attribution/mapa.jpg"
        ),
        (
            "exams/1/2/3/"
            "attribution/mapa.txt"
        ),
    ),
)
def test_rejects_noncanonical_map_paths(
    isolated_attribution_storage: Path,
    invalid_path: str,
) -> None:
    with pytest.raises(
        HTTPException
    ) as error:
        (
            file_storage
            .resolve_safe_gradcam_path(
                invalid_path
            )
        )

    assert error.value.status_code == 403


def test_missing_canonical_map_returns_404(
    isolated_attribution_storage: Path,
) -> None:
    with pytest.raises(
        HTTPException
    ) as error:
        (
            file_storage
            .resolve_safe_gradcam_path(
                (
                    "exams/1/2/3/"
                    "attribution/ausente.jpg"
                )
            )
        )

    assert error.value.status_code == 404


def test_rejects_incorrect_map_hash(
    isolated_attribution_storage: Path,
) -> None:
    with pytest.raises(
        file_storage.AttributionStorageError,
        match="hash",
    ):
        (
            file_storage
            .store_attribution_from_base64(
                encoded_data=(
                    base64.b64encode(
                        VALID_PNG
                    ).decode("ascii")
                ),
                mime_type="image/png",
                expected_sha256="0" * 64,
                clinic_id=1,
                patient_id=2,
                exam_id=3,
            )
        )


def test_rejects_declared_mime_different_from_content(
    isolated_attribution_storage: Path,
) -> None:
    with pytest.raises(
        file_storage.AttributionStorageError,
        match="tipo",
    ):
        (
            file_storage
            .store_attribution_from_base64(
                encoded_data=(
                    base64.b64encode(
                        VALID_PNG
                    ).decode("ascii")
                ),
                mime_type="image/jpeg",
                expected_sha256=(
                    hashlib.sha256(
                        VALID_PNG
                    ).hexdigest()
                ),
                clinic_id=1,
                patient_id=2,
                exam_id=3,
            )
        )


def test_delete_removes_only_canonical_map(
    isolated_attribution_storage: Path,
) -> None:
    stored = (
        file_storage
        .store_attribution_from_base64(
            encoded_data=(
                base64.b64encode(
                    VALID_PNG
                ).decode("ascii")
            ),
            mime_type="image/png",
            expected_sha256=(
                hashlib.sha256(
                    VALID_PNG
                ).hexdigest()
            ),
            clinic_id=7,
            patient_id=8,
            exam_id=9,
        )
    )

    file_storage.delete_attribution_file_safely(
        stored
    )

    assert not stored.exists()
