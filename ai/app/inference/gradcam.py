"""
Geração de GradCAM para inferência do ClinicAI.
"""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np

from PIL import Image

from pytorch_grad_cam import GradCAM

from pytorch_grad_cam.utils.image import (
    preprocess_image as gradcam_preprocess_image,
    show_cam_on_image,
)

from training.preprocessing.pipeline import (
    preprocess_for_training,
)

from app.config import TARGET_IMAGE_SIZE

from app.inference.model_loader import (
    DEVICE,
    model,
)

# =========================================================
# DIRETÓRIO
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

GRADCAM_OUTPUT_DIR = (
    BASE_DIR
    / "reports"
    / "gradcam"
)

GRADCAM_OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# =========================================================
# FUNÇÃO
# =========================================================


def generate_gradcam_from_bytes(
    image_bytes: bytes,
) -> str:
    """
    Gera GradCAM para imagem enviada à API.
    """

    # =====================================================
    # LOAD IMAGE
    # =====================================================

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    image = np.array(image)

    # =====================================================
    # PREPROCESSING MÉDICO
    # =====================================================

    image = preprocess_for_training(image)

    # =====================================================
    # RESIZE
    # =====================================================

    image = cv2.resize(
        image,
        TARGET_IMAGE_SIZE,
    )

    rgb_image = image.astype(np.float32) / 255.0

    # =====================================================
    # TENSOR
    # =====================================================

    input_tensor = gradcam_preprocess_image(
        rgb_image,
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ).to(DEVICE)

    # =====================================================
    # TARGET LAYER
    # =====================================================

    target_layers = [
        model.layer4[-1]
    ]

    # =====================================================
    # CAM
    # =====================================================

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

    # =====================================================
    # SAVE
    # =====================================================

    filename = f"{uuid4()}.jpg"

    output_path = (
        GRADCAM_OUTPUT_DIR
        / filename
    )

    cv2.imwrite(
        str(output_path),
        cv2.cvtColor(
            visualization,
            cv2.COLOR_RGB2BGR,
        ),
    )

    return str(output_path)
