"""
Extração de região de interesse (ROI).

Algoritmo exato de Pedro Viana (2026), replicado com fidelidade a partir
do notebook de treino do ClinicAI: varre da borda para o centro, na
linha/coluna do meio da imagem, procurando o primeiro pixel acima do
limiar, e recorta o retângulo formado pelas 4 bordas encontradas.

Importante: essa checagem (`np.any(pixel > pop)`) compara a intensidade
bruta dos pixels, não depende da ordem dos canais (RGB ou BGR) — funciona
igual nos dois casos, ao contrário da remoção de reflexo especular
(specular.py), que precisou ser adaptada.
"""

import numpy as np


def extract_roi(image: np.ndarray, pop: int = 0) -> np.ndarray:
    """
    Extrai a região útil da imagem endoscópica, removendo bordas escuras.

    Args:
        image: Imagem RGB (ou BGR — o resultado é o mesmo).
        pop: Limiar de intensidade usado para distinguir borda de conteúdo
            útil (0 = qualquer pixel não totalmente preto já conta).

    Returns:
        Imagem recortada. Se o recorte degenerar (limiar muito agressivo
        numa imagem atípica), retorna a imagem original sem recorte —
        mesma salvaguarda usada no notebook de treino.
    """
    h, w, _ = image.shape
    top, bottom, left, right = 0, h, 0, w

    for y in range(0, h, 10):
        if np.any(image[y, w // 2] > pop):
            top = y
            break
    for y in range(h - 1, 0, -10):
        if np.any(image[y, w // 2] > pop):
            bottom = y
            break
    for x in range(0, w, 10):
        if np.any(image[h // 2, x] > pop):
            left = x
            break
    for x in range(w - 1, 0, -10):
        if np.any(image[h // 2, x] > pop):
            right = x
            break

    roi = image[top:bottom, left:right]

    if roi.size == 0:
        return image

    return roi