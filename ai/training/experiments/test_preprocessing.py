"""
Teste visual do pipeline de pré-processamento.
"""

from pathlib import Path

import cv2
import matplotlib.pyplot as plt

from training.preprocessing.pipeline import (
    load_and_preprocess_image,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_IMAGE = BASE_DIR / "datasets" / "test_image.jpg"

OUTPUT_IMAGE = (
    BASE_DIR
    / "training"
    / "experiments"
    / "outputs"
    / "preprocessed_image.jpg"
)


def main():
    """
    Executa o teste do pipeline.
    """

    processed_image = load_and_preprocess_image(
        str(INPUT_IMAGE)
    )

    cv2.imwrite(
        str(OUTPUT_IMAGE),
        cv2.cvtColor(processed_image, cv2.COLOR_RGB2BGR),
    )

    plt.figure(figsize=(8, 8))

    plt.imshow(processed_image)

    plt.title("Imagem Pré-processada")

    plt.axis("off")

    plt.show()

    print(f"Imagem salva em: {OUTPUT_IMAGE}")


if __name__ == "__main__":
    main()
    