"""
Pipeline de pré-processamento para imagens endoscópicas.

Este módulo combina as etapas principais usadas antes do treinamento:
- extração da região de interesse;
- remoção de reflexos especulares;
- melhoria de contraste.
"""

import cv2
import numpy as np

from training.preprocessing.enhancement import enhance_image
from training.preprocessing.roi import extract_roi
from training.preprocessing.specular import remove_specular_highlights


def preprocess_for_training(image: np.ndarray) -> np.ndarray:
    """
    Aplica o pipeline completo de pré-processamento em uma imagem.

    Args:
        image: Imagem no formato RGB.

    Returns:
        Imagem pré-processada no formato RGB.
    """

    image = extract_roi(image)

    image = remove_specular_highlights(image)

    image = enhance_image(image)

    return image


def load_and_preprocess_image(image_path: str) -> np.ndarray:
    """
    Carrega uma imagem do disco e aplica o pipeline completo.

    Args:
        image_path: Caminho da imagem.

    Returns:
        Imagem pré-processada no formato RGB.
    """

    image_bgr = cv2.imread(image_path)

    if image_bgr is None:
        raise ValueError(f"Não foi possível carregar a imagem: {image_path}")

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    return preprocess_for_training(image_rgb)
