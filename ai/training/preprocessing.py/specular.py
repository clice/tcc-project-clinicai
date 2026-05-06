"""
Remoção simples de reflexos especulares.

Reflexos são brilhos intensos causados pela luz do endoscópio.
"""

import cv2
import numpy as np


def remove_specular_highlights(image: np.ndarray) -> np.ndarray:
    """
    Atenua regiões muito brilhantes da imagem.
    """
    
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    h, s, v = cv2.split(hsv)
    
    _, mask = csv.threshold(v, 230, 255, cv2.THRESH_BINARY)
    
    inpainted = cv2.inpaint(
        image,
        mask,
        inpaintRadius=3,
        flags=cv2.INPAINT_TELEA,
    )
    
    return inpainted
