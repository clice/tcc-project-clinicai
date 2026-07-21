"""Pré-processamento validado das imagens recebidas pelo serviço de IA."""

import io

import numpy as np
from PIL import Image, UnidentifiedImageError
from torchvision import transforms

from app.config import (
    ALLOWED_INFERENCE_IMAGE_FORMATS,
    MAX_INFERENCE_IMAGE_BYTES,
    MAX_INFERENCE_IMAGE_HEIGHT,
    MAX_INFERENCE_IMAGE_PIXELS,
    MAX_INFERENCE_IMAGE_WIDTH,
    NORMALIZE_MEAN,
    NORMALIZE_STD,
    TARGET_IMAGE_SIZE,
)
from training.preprocessing.pipeline import preprocess_for_training


class InvalidImageError(ValueError):
    """A entrada não representa uma imagem JPEG/PNG válida para inferência."""


inference_transform = transforms.Compose(
    [
        transforms.ToPILImage(),
        transforms.Resize(TARGET_IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD),
    ]
)


def decode_image(image_bytes: bytes) -> Image.Image:
    if not image_bytes:
        raise InvalidImageError("A imagem enviada está vazia.")
    if len(image_bytes) > MAX_INFERENCE_IMAGE_BYTES:
        raise InvalidImageError("A imagem excede o limite de tamanho da inferência.")

    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            image_format = (source.format or "").upper()
            if image_format not in ALLOWED_INFERENCE_IMAGE_FORMATS:
                raise InvalidImageError("Apenas imagens JPEG e PNG são aceitas.")
            width, height = source.size
            if (
                width <= 0
                or height <= 0
                or width > MAX_INFERENCE_IMAGE_WIDTH
                or height > MAX_INFERENCE_IMAGE_HEIGHT
                or width * height > MAX_INFERENCE_IMAGE_PIXELS
            ):
                raise InvalidImageError("As dimensões da imagem excedem o limite permitido.")
            source.load()
            return source.convert("RGB")
    except InvalidImageError:
        raise
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError("O arquivo enviado não é uma imagem válida.") from exc


def preprocess_image(image_bytes: bytes):
    image = decode_image(image_bytes)
    image_array = np.array(image)
    processed_array = preprocess_for_training(image_array)
    image_tensor = inference_transform(processed_array)
    return image_tensor.unsqueeze(0)
