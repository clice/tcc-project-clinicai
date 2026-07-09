"""
Melhoria de contraste da imagem.
"""

import cv2
import numpy as np


def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    Melhora contraste usando CLAHE.
    """

    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    cl = clahe.apply(l)

    enhanced_lab = cv2.merge((cl, a, b))

    enhanced_image = cv2.cvtColor(
        enhanced_lab,
        cv2.COLOR_LAB2RGB,
    )

    return enhanced_image
