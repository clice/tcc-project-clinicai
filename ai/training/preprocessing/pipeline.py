"""
Pipeline de pré-processamento para imagens endoscópicas.

Fiel ao protocolo de Pedro Viana (2026), validado no notebook de treino
do Ensemble Stacking do ClinicAI:
1. extração da região de interesse (remove bordas escuras);
2. remoção de reflexos especulares (máscara HSV + inpainting).

Não inclui melhoria de contraste (CLAHE) — essa etapa existiu numa versão
anterior deste módulo, mas nunca fez parte do protocolo documentado na
monografia nem do pipeline usado para treinar os modelos atuais. Foi
removida por fidelidade entre treino e inferência: usar um pipeline
diferente do que gerou os pesos treinados produziria predições
sistematicamente enviesadas, sem nenhum erro visível.
"""

import cv2
import numpy as np

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
