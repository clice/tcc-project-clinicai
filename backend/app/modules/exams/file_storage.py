"""Validação e armazenamento seguro das imagens de exames.

A entrada do usuário é usada somente para conferir a extensão declarada. O
caminho físico e o nome persistido são gerados pelo backend.
"""

from __future__ import annotations

import hashlib
import os
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.config import settings


UPLOAD_DIR = Path(settings.upload_dir) / "exams"
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024
MAX_IMAGE_WIDTH = settings.max_image_width_px
MAX_IMAGE_HEIGHT = settings.max_image_height_px
MAX_IMAGE_PIXELS = settings.max_image_pixels

DIRECTORY_MODE = 0o750
FILE_MODE = 0o640
MAX_NAME_ATTEMPTS = 10

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"

ALLOWED_EXTENSIONS_BY_MIME = {
    "image/jpeg": frozenset({".jpg", ".jpeg"}),
    "image/png": frozenset({".png"}),
}


@dataclass(frozen=True)
class ValidatedExamImage:
    """Conteúdo validado e metadados derivados dos bytes reais."""

    data: bytes
    mime_type: str
    extension: str
    width: int
    height: int
    sha256: str

    @property
    def size_bytes(self) -> int:
        return len(self.data)


def _http_error(status_code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)


def _validate_dimensions(width: int, height: int) -> None:
    if width <= 0 or height <= 0:
        raise _http_error(400, "A imagem possui dimensões inválidas.")

    if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
        raise _http_error(
            413,
            (
                "Dimensões da imagem acima do limite permitido: "
                f"{MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT} pixels."
            ),
        )

    if width * height > MAX_IMAGE_PIXELS:
        raise _http_error(
            413,
            f"A imagem excede o limite de {MAX_IMAGE_PIXELS} pixels.",
        )


def _parse_png(data: bytes) -> tuple[int, int]:
    """Valida assinatura, chunks, CRC, stream IDAT e dimensões de PNG."""

    if not data.startswith(PNG_SIGNATURE):
        raise _http_error(415, "A assinatura do arquivo não corresponde a PNG.")

    offset = len(PNG_SIGNATURE)
    width = height = None
    bit_depth = color_type = interlace = None
    idat_parts: list[bytes] = []
    seen_ihdr = False
    seen_iend = False
    chunk_index = 0

    while offset < len(data):
        if len(data) - offset < 12:
            raise _http_error(400, "Arquivo PNG corrompido ou truncado.")

        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4

        if crc_end > len(data):
            raise _http_error(400, "Arquivo PNG corrompido ou truncado.")

        chunk_data = data[data_start:data_end]
        expected_crc = struct.unpack(">I", data[data_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(chunk_data, actual_crc) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            raise _http_error(400, "Arquivo PNG corrompido: CRC inválido.")

        if chunk_index == 0 and chunk_type != b"IHDR":
            raise _http_error(400, "Arquivo PNG inválido: IHDR ausente.")

        if chunk_type == b"IHDR":
            if seen_ihdr or length != 13:
                raise _http_error(400, "Arquivo PNG inválido: IHDR incorreto.")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if compression != 0 or filtering != 0 or interlace not in {0, 1}:
                raise _http_error(400, "Arquivo PNG usa parâmetros não suportados.")
            seen_ihdr = True
            _validate_dimensions(width, height)

        elif chunk_type == b"IDAT":
            if not seen_ihdr or seen_iend:
                raise _http_error(400, "Arquivo PNG possui ordem de chunks inválida.")
            idat_parts.append(chunk_data)

        elif chunk_type == b"IEND":
            if length != 0 or not seen_ihdr or not idat_parts:
                raise _http_error(400, "Arquivo PNG inválido: IEND incorreto.")
            seen_iend = True
            offset = crc_end
            if offset != len(data):
                raise _http_error(400, "Arquivo PNG contém dados após o chunk IEND.")
            break

        offset = crc_end
        chunk_index += 1

    if not seen_iend or width is None or height is None:
        raise _http_error(400, "Arquivo PNG corrompido ou incompleto.")

    # O protótipo aceita apenas PNG não entrelaçado para permitir verificação
    # determinística do tamanho decodificado sem carregar a imagem inteira.
    if interlace != 0:
        raise _http_error(415, "PNG entrelaçado não é aceito para exames.")

    valid_bit_depths = {
        0: {1, 2, 4, 8, 16},
        2: {8, 16},
        3: {1, 2, 4, 8},
        4: {8, 16},
        6: {8, 16},
    }
    if color_type not in valid_bit_depths or bit_depth not in valid_bit_depths[color_type]:
        raise _http_error(400, "Arquivo PNG possui profundidade de cor inválida.")

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    row_bytes = (width * channels * bit_depth + 7) // 8
    expected_decoded_size = (row_bytes + 1) * height

    try:
        decompressor = zlib.decompressobj()
        decoded_size = 0
        for part in idat_parts:
            pending = part
            while pending:
                remaining = expected_decoded_size + 1 - decoded_size
                if remaining <= 0:
                    raise _http_error(400, "Arquivo PNG possui conteúdo descompactado inválido.")
                output = decompressor.decompress(pending, min(65536, remaining))
                decoded_size += len(output)
                pending = decompressor.unconsumed_tail
                if not output and not pending:
                    break

        remaining = expected_decoded_size + 1 - decoded_size
        if remaining <= 0:
            raise _http_error(400, "Arquivo PNG possui conteúdo descompactado inválido.")
        decoded_size += len(decompressor.flush(remaining))
    except zlib.error as exc:
        raise _http_error(400, "Arquivo PNG corrompido: stream IDAT inválido.") from exc

    if not decompressor.eof or decoded_size != expected_decoded_size:
        raise _http_error(400, "Arquivo PNG corrompido: dados de pixels incompletos.")

    return width, height


def _parse_jpeg(data: bytes) -> tuple[int, int]:
    """Valida estrutura de segmentos e extrai dimensões de JPEG."""

    if not data.startswith(JPEG_SIGNATURE):
        raise _http_error(415, "A assinatura do arquivo não corresponde a JPEG.")

    if len(data) < 8 or data[:2] != b"\xff\xd8":
        raise _http_error(400, "Arquivo JPEG corrompido ou truncado.")

    offset = 2
    width = height = None
    seen_sos = False
    seen_eoi = False
    seen_quantization = False

    standalone_markers = {0x01, *range(0xD0, 0xD8)}
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }

    while offset < len(data):
        if data[offset] != 0xFF:
            raise _http_error(400, "Arquivo JPEG possui marcador inválido.")

        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            raise _http_error(400, "Arquivo JPEG truncado após marcador.")

        marker = data[offset]
        offset += 1

        if marker == 0xD9:
            seen_eoi = True
            if offset != len(data):
                raise _http_error(400, "Arquivo JPEG contém dados após EOI.")
            break

        if marker in standalone_markers:
            continue

        if marker == 0x00 or marker == 0xD8:
            raise _http_error(400, "Arquivo JPEG possui sequência de marcadores inválida.")

        if offset + 2 > len(data):
            raise _http_error(400, "Arquivo JPEG truncado em segmento.")
        segment_length = struct.unpack(">H", data[offset : offset + 2])[0]
        if segment_length < 2:
            raise _http_error(400, "Arquivo JPEG possui segmento inválido.")

        segment_start = offset + 2
        segment_end = offset + segment_length
        if segment_end > len(data):
            raise _http_error(400, "Arquivo JPEG corrompido ou truncado.")
        segment = data[segment_start:segment_end]

        if marker == 0xDB:
            seen_quantization = True

        if marker in sof_markers:
            if len(segment) < 6:
                raise _http_error(400, "Arquivo JPEG possui SOF inválido.")
            precision = segment[0]
            height = struct.unpack(">H", segment[1:3])[0]
            width = struct.unpack(">H", segment[3:5])[0]
            components = segment[5]
            if precision not in {8, 12} or components not in {1, 3, 4}:
                raise _http_error(400, "Arquivo JPEG possui parâmetros de imagem inválidos.")
            _validate_dimensions(width, height)

        offset = segment_end

        if marker == 0xDA:
            seen_sos = True
            entropy_start = offset
            while offset < len(data) - 1:
                if data[offset] != 0xFF:
                    offset += 1
                    continue

                next_byte = data[offset + 1]
                if next_byte == 0x00 or 0xD0 <= next_byte <= 0xD7:
                    offset += 2
                    continue
                if next_byte == 0xD9:
                    if offset == entropy_start:
                        raise _http_error(400, "Arquivo JPEG não contém dados de imagem.")
                    offset += 2
                    seen_eoi = True
                    if offset != len(data):
                        raise _http_error(400, "Arquivo JPEG contém dados após EOI.")
                    break

                # Um novo segmento pode aparecer entre scans progressivos.
                break

            if seen_eoi:
                break

    if width is None or height is None or not seen_sos or not seen_eoi:
        raise _http_error(400, "Arquivo JPEG corrompido ou incompleto.")
    if not seen_quantization:
        raise _http_error(400, "Arquivo JPEG inválido: tabela de quantização ausente.")

    return width, height


def _detect_and_parse(data: bytes) -> tuple[str, str, int, int]:
    if data.startswith(PNG_SIGNATURE):
        width, height = _parse_png(data)
        return "image/png", ".png", width, height

    if data.startswith(JPEG_SIGNATURE):
        width, height = _parse_jpeg(data)
        return "image/jpeg", ".jpg", width, height

    raise _http_error(415, "O conteúdo enviado não é uma imagem JPG ou PNG válida.")


def validate_exam_file(file: UploadFile) -> ValidatedExamImage:
    """Valida tamanho, MIME real, extensão, assinatura e integridade."""

    original_filename = file.filename or ""
    extension = Path(original_filename).suffix.lower()
    if not extension:
        raise _http_error(415, "O arquivo deve possuir extensão JPG, JPEG ou PNG.")

    declared_mime = (file.content_type or "").split(";", 1)[0].strip().lower()
    if declared_mime not in ALLOWED_EXTENSIONS_BY_MIME:
        raise _http_error(415, "Tipo declarado não permitido. Use JPG ou PNG.")

    file.file.seek(0)
    data = file.file.read(MAX_FILE_SIZE + 1)
    file.file.seek(0)

    if not data:
        raise _http_error(400, "Arquivo vazio não é permitido.")
    if len(data) > MAX_FILE_SIZE:
        raise _http_error(
            413,
            f"Arquivo muito grande. Tamanho máximo permitido: {settings.max_upload_size_mb} MB.",
        )

    real_mime, canonical_extension, width, height = _detect_and_parse(data)

    if declared_mime != real_mime:
        raise _http_error(415, "O tipo MIME declarado não corresponde ao conteúdo real do arquivo.")

    if extension not in ALLOWED_EXTENSIONS_BY_MIME[real_mime]:
        raise _http_error(415, "A extensão não corresponde ao conteúdo real da imagem.")

    return ValidatedExamImage(
        data=data,
        mime_type=real_mime,
        extension=canonical_extension,
        width=width,
        height=height,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def _ensure_secure_directory(path: Path) -> Path:
    base_dir = UPLOAD_DIR.resolve()
    base_dir.mkdir(parents=True, exist_ok=True, mode=DIRECTORY_MODE)
    os.chmod(base_dir, DIRECTORY_MODE)

    candidate = path.resolve(strict=False)
    try:
        candidate.relative_to(base_dir)
    except ValueError as exc:
        raise _http_error(403, "Diretório de armazenamento inválido.") from exc

    current = base_dir
    relative_parts = candidate.relative_to(base_dir).parts
    for part in relative_parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise _http_error(403, "Diretório de armazenamento contém link simbólico.")
        current.mkdir(exist_ok=True, mode=DIRECTORY_MODE)
        os.chmod(current, DIRECTORY_MODE)

    return candidate


def build_exam_storage_dir(*, clinic_id: int, patient_id: int, exam_id: int) -> Path:
    """Cria a hierarquia interna sem usar o nome original do arquivo."""

    return _ensure_secure_directory(
        UPLOAD_DIR / str(clinic_id) / str(patient_id) / str(exam_id)
    )


def store_validated_exam_file(
    image: ValidatedExamImage,
    *,
    clinic_id: int,
    patient_id: int,
    exam_id: int,
) -> Path:
    """Grava com nome aleatório e criação exclusiva para impedir sobrescrita."""

    storage_dir = build_exam_storage_dir(
        clinic_id=clinic_id,
        patient_id=patient_id,
        exam_id=exam_id,
    )

    last_error: OSError | None = None
    for _ in range(MAX_NAME_ATTEMPTS):
        file_path = storage_dir / f"{uuid4().hex}{image.extension}"
        try:
            with file_path.open("xb") as output:
                output.write(image.data)
                output.flush()
                os.fsync(output.fileno())
            os.chmod(file_path, FILE_MODE)
            return file_path
        except FileExistsError as exc:
            last_error = exc
            continue
        except OSError:
            file_path.unlink(missing_ok=True)
            raise

    raise _http_error(500, "Não foi possível gerar um nome físico exclusivo para o arquivo.") from last_error


def resolve_safe_exam_file_path(file_path: str) -> Path:
    """Resolve somente arquivos regulares internos e rejeita path traversal."""

    base_dir = UPLOAD_DIR.resolve()
    raw_path = Path(file_path)
    if raw_path.is_symlink():
        raise _http_error(403, "Links simbólicos não são permitidos no armazenamento.")

    resolved_path = raw_path.resolve()
    try:
        resolved_path.relative_to(base_dir)
    except ValueError as exc:
        raise _http_error(403, "Caminho de arquivo inválido.") from exc

    return resolved_path


def delete_exam_file_safely(file_path: str | None) -> bool:
    """Remove apenas arquivo interno e limpa diretórios vazios até a raiz."""

    if not file_path:
        return False

    try:
        resolved_path = resolve_safe_exam_file_path(file_path)
    except HTTPException:
        return False

    if not resolved_path.exists() or not resolved_path.is_file():
        return False

    resolved_path.unlink()
    base_dir = UPLOAD_DIR.resolve()
    parent = resolved_path.parent
    while parent != base_dir:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent

    return True
