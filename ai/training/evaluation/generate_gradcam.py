"""
Geração de GradCAM para o modelo treinado.

** VERSÃO EXPLORATÓRIA ANTIGA — NÃO É O PROTOCOLO OFICIAL **
Script para o modelo antigo (torchvision.models.resnet50 direto, não
timm), anterior ao trabalho de fidelidade ao protocolo de Pedro Viana.
Mantido apenas como referência histórica — a explicabilidade oficial do
ClinicAI está em `app/explainability/gradcam.py`.

Atenção: o import abaixo (`from ai.app.config import TARGET_IMAGE_SIZE`)
usa um caminho que não bate com a convenção do resto do projeto (`from
app.config import ...`) e provavelmente falha se executado no mesmo
ambiente/contêiner que os demais scripts — não foi corrigido de
propósito, para preservar este arquivo exatamente como estava.
"""

from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import (
    preprocess_image,
    show_cam_on_image,
)
from torchvision import models

from ai.app.config import TARGET_IMAGE_SIZE


DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "exported"
    / "model.pt"
)

INPUT_IMAGE = (
    BASE_DIR
    / "datasets"
    / "test_image.jpg"
)

OUTPUT_DIR = (
    BASE_DIR
    / "training"
    / "experiments"
    / "outputs"
)

OUTPUT_IMAGE = (
    OUTPUT_DIR
    / "gradcam_result.jpg"
)


def create_model():
    """
    Cria arquitetura da ResNet50.
    """

    model = models.resnet50(weights=None)

    in_features = model.fc.in_features

    model.fc = nn.Linear(
        in_features,
        2,
    )

    return model


def load_model():
    """
    Carrega modelo treinado.
    """

    model = create_model()

    model.load_state_dict(
        torch.load(
            MODEL_PATH,
            map_location=DEVICE,
            weights_only=True,
        )
    )

    model.to(DEVICE)

    model.eval()

    return model


def generate_gradcam():
    """
    Gera visualização GradCAM.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = load_model()

    image = Image.open(INPUT_IMAGE).convert("RGB")

    image = image.resize(TARGET_IMAGE_SIZE)

    rgb_image = np.array(image).astype(np.float32) / 255.0

    input_tensor = preprocess_image(
        rgb_image,
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    )

    target_layers = [model.layer4[-1]]

    cam = GradCAM(
        model=model,
        target_layers=target_layers,
    )

    grayscale_cam = cam(
        input_tensor=input_tensor
    )[0]

    visualization = show_cam_on_image(
        rgb_image,
        grayscale_cam,
        use_rgb=True,
    )

    cv2.imwrite(
        str(OUTPUT_IMAGE),
        cv2.cvtColor(
            visualization,
            cv2.COLOR_RGB2BGR,
        ),
    )

    plt.figure(figsize=(8, 8))

    plt.imshow(visualization)

    plt.title("GradCAM")

    plt.axis("off")

    plt.show()

    print(
        f"\nGradCAM salvo em:\n{OUTPUT_IMAGE}"
    )


if __name__ == "__main__":
    generate_gradcam()
    