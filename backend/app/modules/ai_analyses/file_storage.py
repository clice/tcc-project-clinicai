"""Armazenamento canônico dos mapas de atribuição."""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from app.core.config import settings
from app.modules.exams.file_storage import (
    detect_and_parse_image,
)


DATA_DIR = Path(
    settings.clinicai_data_dir
)
EXAMS_DIR = DATA_DIR / "exams"

DIRECTORY_MODE = 0o750
FILE_MODE = 0o640
MAX_NAME_ATTEMPTS = 10

MAX_ATTRIBUTION_SIZE = (
    settings.max_upload_size_mb
    * 1024
    * 1024
)

ALLOWED_ATTRIBUTION_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


class AttributionStorageError(RuntimeError):
    """Falha na validação ou persistência do mapa."""


def _validate_identifiers(
    *,
    clinic_id: int,
    patient_id: int,
    exam_id: int,
) -> None:
    values = (
        clinic_id,
        patient_id,
        exam_id,
    )

    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
        for value in values
    ):
        raise AttributionStorageError(
            "Identificadores inválidos para "
            "armazenar o mapa de atribuição."
        )


def _ensure_directory(
    path: Path,
) -> Path:
    root = EXAMS_DIR.resolve(
        strict=False
    )

    root.mkdir(
        parents=True,
        exist_ok=True,
        mode=DIRECTORY_MODE,
    )
    os.chmod(
        root,
        DIRECTORY_MODE,
    )

    candidate = path.resolve(
        strict=False
    )

    try:
        relative_parts = (
            candidate.relative_to(
                root
            ).parts
        )
    except ValueError as exc:
        raise AttributionStorageError(
            "Diretório de atribuição "
            "fora da raiz de exames."
        ) from exc

    current = root

    for part in relative_parts:
        current = current / part

        if (
            current.exists()
            and current.is_symlink()
        ):
            raise AttributionStorageError(
                "A hierarquia de atribuição "
                "contém link simbólico."
            )

        current.mkdir(
            exist_ok=True,
            mode=DIRECTORY_MODE,
        )
        os.chmod(
            current,
            DIRECTORY_MODE,
        )

    return candidate


def build_attribution_storage_dir(
    *,
    clinic_id: int,
    patient_id: int,
    exam_id: int,
) -> Path:
    """Retorna a pasta attribution do exame."""

    _validate_identifiers(
        clinic_id=clinic_id,
        patient_id=patient_id,
        exam_id=exam_id,
    )

    return _ensure_directory(
        EXAMS_DIR
        / str(clinic_id)
        / str(patient_id)
        / str(exam_id)
        / "attribution"
    )


def _validate_relative_attribution_path(
    relative_path: Path,
) -> None:
    parts = relative_path.parts

    if (
        len(parts) != 6
        or parts[0] != "exams"
        or parts[4] != "attribution"
        or not all(
            part.isdigit()
            and int(part) > 0
            for part in parts[1:4]
        )
        or not parts[5]
        or Path(parts[5]).suffix.lower()
        not in {".jpg", ".jpeg", ".png"}
    ):
        raise AttributionStorageError(
            "Caminho do mapa de atribuição inválido."
        )


def serialize_gradcam_path(
    file_path: Path,
) -> str:
    """Serializa o mapa relativamente à raiz de dados."""

    resolved_path = file_path.resolve(
        strict=False
    )

    try:
        relative_path = (
            resolved_path.relative_to(
                DATA_DIR.resolve(
                    strict=False
                )
            )
        )
    except ValueError as exc:
        raise AttributionStorageError(
            "O mapa está fora da raiz de dados."
        ) from exc

    _validate_relative_attribution_path(
        relative_path
    )

    return relative_path.as_posix()


def store_attribution_from_base64(
    *,
    encoded_data: str,
    mime_type: str,
    expected_sha256: str,
    clinic_id: int,
    patient_id: int,
    exam_id: int,
) -> Path:
    """Valida e grava o mapa retornado pela IA."""

    if mime_type not in (
        ALLOWED_ATTRIBUTION_MIME_TYPES
    ):
        raise AttributionStorageError(
            "Tipo de mapa de atribuição não permitido."
        )

    if re.fullmatch(
        r"[0-9a-f]{64}",
        expected_sha256,
    ) is None:
        raise AttributionStorageError(
            "Hash inválido para o mapa de atribuição."
        )

    try:
        data = base64.b64decode(
            encoded_data,
            validate=True,
        )
    except (
        binascii.Error,
        ValueError,
    ) as exc:
        raise AttributionStorageError(
            "Conteúdo Base64 inválido para o mapa."
        ) from exc

    if not data:
        raise AttributionStorageError(
            "O mapa de atribuição está vazio."
        )

    if len(data) > MAX_ATTRIBUTION_SIZE:
        raise AttributionStorageError(
            "O mapa de atribuição excede "
            "o limite permitido."
        )

    actual_sha256 = hashlib.sha256(
        data
    ).hexdigest()

    if actual_sha256 != expected_sha256:
        raise AttributionStorageError(
            "O hash do mapa não corresponde "
            "ao conteúdo recebido."
        )

    (
        real_mime,
        canonical_extension,
        _width,
        _height,
    ) = detect_and_parse_image(
        data
    )

    if real_mime != mime_type:
        raise AttributionStorageError(
            "O tipo declarado do mapa não "
            "corresponde ao conteúdo."
        )

    expected_extension = (
        ALLOWED_ATTRIBUTION_MIME_TYPES[
            mime_type
        ]
    )

    if (
        canonical_extension
        != expected_extension
    ):
        raise AttributionStorageError(
            "A extensão canônica do mapa "
            "não corresponde ao tipo declarado."
        )

    storage_dir = (
        build_attribution_storage_dir(
            clinic_id=clinic_id,
            patient_id=patient_id,
            exam_id=exam_id,
        )
    )

    last_error: OSError | None = None

    for _ in range(
        MAX_NAME_ATTEMPTS
    ):
        file_path = (
            storage_dir
            / (
                f"{uuid4().hex}"
                f"{canonical_extension}"
            )
        )

        try:
            with file_path.open(
                "xb"
            ) as output:
                output.write(
                    data
                )
                output.flush()
                os.fsync(
                    output.fileno()
                )

            os.chmod(
                file_path,
                FILE_MODE,
            )

            return file_path

        except FileExistsError as exc:
            last_error = exc
            continue

        except OSError:
            file_path.unlink(
                missing_ok=True
            )
            raise

    raise AttributionStorageError(
        "Não foi possível gerar um nome "
        "físico exclusivo para o mapa."
    ) from last_error


def resolve_safe_gradcam_path(
    stored_path: str | None,
) -> Path:
    """Resolve exclusivamente um mapa da pasta do exame."""

    if not stored_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "Este exame não possui mapa "
                "de atribuição disponível."
            ),
        )

    raw_path = Path(
        stored_path
    )

    if (
        raw_path.is_absolute()
        or ".." in raw_path.parts
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "O caminho do mapa de "
                "atribuição não é permitido."
            ),
        )

    try:
        _validate_relative_attribution_path(
            raw_path
        )
    except AttributionStorageError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    candidate = DATA_DIR / raw_path

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
                "encontrado."
            ),
        ) from exc

    try:
        resolved.relative_to(
            EXAMS_DIR.resolve(
                strict=False
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail=(
                "O mapa está fora da "
                "raiz de exames."
            ),
        ) from exc

    if not resolved.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "O mapa de atribuição não "
                "é um arquivo válido."
            ),
        )

    return resolved


def delete_attribution_file_safely(
    file_path: Path,
) -> None:
    """Remove somente um mapa pertencente à raiz canônica."""

    serialized = serialize_gradcam_path(
        file_path
    )

    resolved = (
        DATA_DIR
        / serialized
    ).resolve(
        strict=False
    )

    resolved.unlink(
        missing_ok=True
    )
