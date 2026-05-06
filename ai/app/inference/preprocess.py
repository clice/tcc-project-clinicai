"""
Pré-processamento das imagens de exames.

Este módulo será responsável por preparar as imagens
antes da inferência do modelo.
"""

from io import BytesIO

import numpy as np
import torch
from PIL import Image

from app.config import TARGET_IMAGE_SIZE


def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """
    Realiza o pré-processamento básico da imagem
    para entrada no modelo PyTorch.

    Etapas:
    - leitura da imagem;
    - conversão para RGB;
    - redimensionamento;
    - normalização.
    """

    # Converte a imagem para RGB
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    # Redimensiona a imagem
    image = image.resize(TARGET_IMAGE_SIZE)

    image_array = np.array(image).astype(np.float32)

    image_array /= 255.0
    
    image_tensor = torch.tensor(image_array)
    
    image_tensor = image_tensor.permute(2, 0, 1)
    
    image_tensor = image_tensor.unsqueeze(0)

    return image_tensor