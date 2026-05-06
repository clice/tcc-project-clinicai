"""
Pré-processamento das imagens de exames.

Este módulo será responsável por preparar as imagens
antes da inferência do modelo.
"""

from io import BytesIO

import numpy as np
from PIL import Image

from app.config import TARGET_IMAGE_SIZE


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Realiza o pré-processamento básico da imagem.

    Etapas:
    - leitura da imagem;
    - conversão para RGB;
    - redimensionamento;
    - normalização.

    Retorna:
        numpy.ndarray: imagem processada.
    """

    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    image = image.resize(TARGET_IMAGE_SIZE)

    image_array = np.array(image).astype(np.float32)

    image_array /= 255.0

    return image_array