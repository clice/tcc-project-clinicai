"""
Extração de região de interesse (ROI).

Remove bordas escuras comuns em imagens endoscópicas.
"""

import cv2
import numpy as np


def extract_roi(image: np.ndarray) -> np.ndarray:
    """
    Extrai a região útil da imagem endoscópica.

    Remove áreas muito escuras das bordas.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    _, threshold = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(
        threshold,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    if not contours:
        return image

    largest_contour = max(contours, key=cv2.contourArea)

    x, y, w, h = cv2.boundingRect(largest_contour)

    roi = image[y:y + h, x:x + w]

    return roi