"""
Geração de GradCAM durante a inferência.
"""

from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import (
    preprocess_image as gradcam_preprocess_image,
    show_cam_on_image,
)
from uuid import uuid4

from app.config import GRADCAM_DIR
from app.config import BASE_DIR, TARGET_IMAGE_SIZE
from app.inference.model_loader import model


def generate_gradcam_from_bytes(image_bytes: bytes) -> str:
    """
    Gera GradCAM a partir dos bytes da imagem enviada para a API.
    """
    
    GRADCAM_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    gradcam_filename = f"{uuid4()}.jpg"

    gradcam_path = (
        GRADCAM_DIR
        / gradcam_filename
    )

    image = Image.open(
        __import__("io").BytesIO(image_bytes)
    ).convert("RGB")

    image = image.resize(TARGET_IMAGE_SIZE)

    rgb_image = np.array(image).astype(np.float32) / 255.0

    input_tensor = gradcam_preprocess_image(
        rgb_image,
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    )

    target_layers = [model.layer4[-1]]

    cam = GradCAM(
        model=model,
        target_layers=target_layers,
    )

    grayscale_cam = cam(input_tensor=input_tensor)[0]

    visualization = show_cam_on_image(
        rgb_image,
        grayscale_cam,
        use_rgb=True,
    )

    cv2.imwrite(
        str(gradcam_path),
        cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR),
    )

    return str(gradcam_path)
