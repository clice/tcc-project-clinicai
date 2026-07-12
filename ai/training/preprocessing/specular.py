"""
Remoção de reflexos especulares (brilhos intensos causados pela luz do
endoscópio).

Algoritmo exato de Pedro Viana (2026), replicado com fidelidade a partir
do notebook de treino do ClinicAI: máscara HSV para pixels muito claros e
pouco saturados (brilho 220-255, saturação 0-60), seguida de inpainting
de Telea com raio 7.

Nota sobre espaço de cor: o código original de Pedro Viana trabalha em
BGR (convenção nativa do OpenCV). O restante do módulo `ai/` trabalha em
RGB (ver `gastro_dataset.py`, `pipeline.py`). Como a detecção de reflexo
especular depende de brilho (V) e saturação (S) — ambos invariantes à
troca de posição entre os canais R e B, já que são calculados a partir do
máximo/mínimo dos três canais, não de qual é "vermelho" ou "azul" — usar
`COLOR_RGB2HSV` aqui produz o mesmo resultado prático que `COLOR_BGR2HSV`
seguido de conversão de volta. Verificado: reflexos especulares aparecem
como regiões quase brancas (R≈G≈B altos), onde a ordem dos canais não
muda nem o brilho nem a saturação calculados.
"""

import cv2
import numpy as np


def remove_specular_highlights(image: np.ndarray) -> np.ndarray:
    """
    Atenua reflexos especulares via máscara HSV + inpainting.

    Args:
        image: Imagem RGB.

    Returns:
        Imagem RGB com os reflexos especulares removidos por inpainting.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, (0, 0, 220), (180, 60, 255))
    result = cv2.inpaint(image, mask, 7, cv2.INPAINT_TELEA)
    return result
