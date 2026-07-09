"""
Pré-processamento usado na inferência da IA.

Importante:
Este arquivo deve manter o mesmo pipeline usado no treinamento,
para evitar diferença entre treino e produção.
"""

import io

from PIL import Image
from torchvision import transforms

from training.preprocessing.pipeline import preprocess_for_training


IMAGE_SIZE = (224, 224)

NORMALIZE_MEAN = [0.485, 0.456, 0.406]

NORMALIZE_STD = [0.229, 0.224, 0.225]


inference_transform = transforms.Compose(
    [
        transforms.ToPILImage(),
        transforms.Resize(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=NORMALIZE_MEAN,
            std=NORMALIZE_STD,
        ),
    ]
)


def preprocess_image(image_bytes: bytes):
    """
    Recebe uma imagem em bytes e retorna tensor pronto para o modelo.

    Pipeline:
    1. Abre imagem recebida pela API.
    2. Converte para RGB.
    3. Aplica o mesmo pré-processamento usado no treinamento.
    4. Redimensiona.
    5. Normaliza com padrão ImageNet.
    6. Adiciona dimensão de batch.
    """

    image = Image.open(
        io.BytesIO(image_bytes)
    ).convert("RGB")

    image_array = preprocess_for_training(
        image=image_to_numpy(image)
    )

    image_tensor = inference_transform(
        image_array
    )

    return image_tensor.unsqueeze(0)


def image_to_numpy(image: Image.Image):
    """
    Converte imagem PIL para array numpy.
    """

    import numpy as np

    return np.array(image)