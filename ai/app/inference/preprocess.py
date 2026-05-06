"""
Pré-processamento das imagens de exames.

Este módulo será responsável por preparar as imagens
antes da inferência do modelo.
"""

from io import BytesIO

import torch
from PIL import Image
from torchvision import transforms

from app.config import TARGET_IMAGE_SIZE


transform = transforms.Compose(
    [
        transforms.Resize(TARGET_IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    """
    Realiza o pré-processamento da imagem para 
    entrada na ResNet-50.
    """

    # Converte a imagem para RGB
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    image_tensor = transform(image)

    image_tensor = image_tensor.unsqueeze(0)

    return image_tensor