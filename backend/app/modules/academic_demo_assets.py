"""Instalação e validação dos ativos versionados da massa acadêmica."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.modules.exams.file_storage import (
    build_exam_storage_dir,
    serialize_exam_file_path,
)

if TYPE_CHECKING:
    from app.modules.exams.model import Exam


BUNDLED_DEMO_ASSETS_DIR = (
    Path(__file__).resolve().parents[2]
    / "demo_assets"
)
DEMO_ASSET_MANIFEST = (
    BUNDLED_DEMO_ASSETS_DIR
    / "manifest.json"
)
DEMO_FILE_MODE = 0o600


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as source:
        for chunk in iter(
            lambda: source.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def get_demo_manifest() -> dict[str, Any]:
    """Carrega o manifesto v2 da massa acadêmica."""

    try:
        payload = json.loads(
            DEMO_ASSET_MANIFEST.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise RuntimeError(
            "O manifesto dos ativos acadêmicos "
            "não pôde ser carregado."
        ) from exc

    if payload.get("schema_version") != 2:
        raise RuntimeError(
            "Versão inesperada do manifesto "
            "dos ativos acadêmicos."
        )

    clinics = payload.get("clinics")
    exams = payload.get("exams")

    if (
        not isinstance(clinics, list)
        or len(clinics) != 3
    ):
        raise RuntimeError(
            "O manifesto acadêmico deve conter "
            "três clínicas."
        )

    if (
        not isinstance(exams, list)
        or len(exams) != 90
    ):
        raise RuntimeError(
            "O manifesto acadêmico deve conter "
            "90 exames."
        )

    exam_keys = [
        item.get("exam_key")
        for item in exams
        if isinstance(item, dict)
    ]

    if (
        len(exam_keys) != 90
        or len(set(exam_keys)) != 90
    ):
        raise RuntimeError(
            "As chaves dos exames acadêmicos "
            "devem ser únicas."
        )

    return payload


def get_demo_exam_definitions() -> tuple[
    dict[str, Any],
    ...,
]:
    """Retorna os 90 exames definidos no manifesto."""

    return tuple(
        get_demo_manifest()["exams"]
    )


def _bundled_asset_path(
    entry: dict[str, Any],
    *,
    expected_kind: str,
) -> Path:
    """Resolve e valida um ativo declarado no manifesto."""

    if entry.get("kind") != expected_kind:
        raise RuntimeError(
            "Tipo inesperado de ativo acadêmico: "
            f"{entry.get('kind')!r}."
        )

    relative_path = Path(
        str(entry.get("path", ""))
    )

    if (
        not relative_path.parts
        or relative_path.is_absolute()
        or ".." in relative_path.parts
    ):
        raise RuntimeError(
            "Caminho inválido no manifesto: "
            f"{relative_path}."
        )

    root = BUNDLED_DEMO_ASSETS_DIR.resolve(
        strict=True
    )
    source = (
        root / relative_path
    ).resolve(strict=True)

    try:
        source.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(
            "Ativo acadêmico fora do diretório "
            "versionado."
        ) from exc

    if (
        source.is_symlink()
        or not source.is_file()
    ):
        raise RuntimeError(
            f"Ativo acadêmico inválido: {source}."
        )

    if _sha256(source) != str(
        entry.get("sha256", "")
    ):
        raise RuntimeError(
            "Hash divergente no ativo acadêmico: "
            f"{source.name}."
        )

    if source.stat().st_size != int(
        entry.get("size_bytes", -1)
    ):
        raise RuntimeError(
            "Tamanho divergente no ativo acadêmico: "
            f"{source.name}."
        )

    return source


def verify_bundled_demo_assets() -> dict[str, str]:
    """Valida as 90 imagens e os 72 mapas versionados."""

    hashes: dict[str, str] = {}

    for definition in get_demo_exam_definitions():
        source_entry = definition["source_asset"]
        source = _bundled_asset_path(
            source_entry,
            expected_kind="exam_image",
        )
        relative_source = source.relative_to(
            BUNDLED_DEMO_ASSETS_DIR
        ).as_posix()

        if relative_source in hashes:
            raise RuntimeError(
                "Imagem acadêmica repetida no manifesto: "
                f"{relative_source}."
            )

        hashes[relative_source] = str(
            source_entry["sha256"]
        )

        analysis = definition.get("analysis")

        if analysis is None:
            continue

        gradcam_entry = analysis[
            "gradcam_asset"
        ]
        gradcam = _bundled_asset_path(
            gradcam_entry,
            expected_kind="gradcam",
        )
        relative_gradcam = gradcam.relative_to(
            BUNDLED_DEMO_ASSETS_DIR
        ).as_posix()

        if relative_gradcam in hashes:
            raise RuntimeError(
                "Mapa acadêmico repetido no manifesto: "
                f"{relative_gradcam}."
            )

        hashes[relative_gradcam] = str(
            gradcam_entry["sha256"]
        )

    if len(hashes) != 162:
        raise RuntimeError(
            "A massa acadêmica deve possuir "
            "162 ativos únicos."
        )

    return hashes


def _copy_if_missing(
    source: Path,
    target: Path,
    entry: dict[str, Any],
) -> Path:
    """Copia sem sobrescrever nem aceitar destino divergente."""

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if target.exists():
        if (
            target.is_symlink()
            or not target.is_file()
        ):
            raise RuntimeError(
                f"Destino acadêmico inválido: {target}."
            )

        if (
            _sha256(target)
            != str(entry["sha256"])
            or target.stat().st_size
            != int(entry["size_bytes"])
        ):
            raise RuntimeError(
                "Destino acadêmico já existe com "
                f"conteúdo diferente: {target}."
            )

        return target.resolve(strict=True)

    try:
        with (
            source.open("rb") as input_file,
            target.open("xb") as output_file,
        ):
            for chunk in iter(
                lambda: input_file.read(
                    1024 * 1024
                ),
                b"",
            ):
                output_file.write(chunk)

            output_file.flush()
            os.fsync(output_file.fileno())

        os.chmod(
            target,
            DEMO_FILE_MODE,
        )
    except Exception:
        target.unlink(missing_ok=True)
        raise

    return target.resolve(strict=True)


def exam_asset_target(
    exam: "Exam",
    asset_entry: dict[str, Any],
) -> Path:
    """Calcula o destino determinístico da imagem demo."""

    _bundled_asset_path(
        asset_entry,
        expected_kind="exam_image",
    )

    storage_dir = build_exam_storage_dir(
        clinic_id=exam.clinic_id,
        patient_id=exam.patient_id,
        exam_id=exam.id,
    )

    return storage_dir / str(
        asset_entry["name"]
    )


def install_exam_asset(
    exam: "Exam",
    asset_entry: dict[str, Any],
    *,
    assign_fields: bool,
) -> Path:
    """Instala a imagem acadêmica no volume persistente."""

    source = _bundled_asset_path(
        asset_entry,
        expected_kind="exam_image",
    )
    target = _copy_if_missing(
        source,
        exam_asset_target(
            exam,
            asset_entry,
        ),
        asset_entry,
    )

    if assign_fields:
        exam.file_path = (
            serialize_exam_file_path(
                target
            )
        )
        exam.file_name = str(
            asset_entry["name"]
        )
        exam.file_mime_type = "image/jpeg"

    return target


def bundled_gradcam_path(
    asset_entry: dict[str, Any],
) -> Path:
    """Retorna um mapa versionado e validado."""

    return _bundled_asset_path(
        asset_entry,
        expected_kind="gradcam",
    )
