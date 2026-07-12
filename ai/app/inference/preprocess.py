"""
Pré-processamento usado na inferência da IA.

Importante: este arquivo reaproveita o mesmo pipeline usado no
treinamento (`training.preprocessing.pipeline`) e as mesmas constantes de
normalização/tamanho definidas em `app.config` — evita que treino e
inferência divirjam silenciosamente (foi exatamente esse tipo de
divergência, com um pipeline de pré-processamento diferente do usado no
treino, que foi corrigida nesta revisão do módulo).
"""

import io

import numpy as np
from PIL import Image
from torchvision import transforms

from app.config import NORMALIZE_MEAN, NORMALIZE_STD, TARGET_IMAGE_SIZE
from training.preprocessing.pipeline import preprocess_for_training

inference_transform = transforms.Compose(
    [
        transforms.ToPILImage(),
        transforms.Resize(TARGET_IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORMALIZE_MEAN, std=NORMALIZE_STD),
    ]
)


def preprocess_image(image_bytes: bytes):
    """
    Recebe uma imagem em bytes e retorna um tensor pronto para o modelo.

    Pipeline:
    1. Abre a imagem recebida pela API e converte para RGB.
    2. Aplica o mesmo pré-processamento usado no treinamento (extração
       de ROI + remoção de reflexos especulares).
    3. Redimensiona e normaliza com o padrão ImageNet.
    4. Adiciona a dimensão de batch.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_array = np.array(image)

    processed_array = preprocess_for_training(image_array)

    image_tensor = inference_transform(processed_array)

    return image_tensor.unsqueeze(0)
