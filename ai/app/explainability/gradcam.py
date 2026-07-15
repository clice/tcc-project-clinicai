"""Geração de Grad-CAM para os domínios que possuem explicador registrado."""

from io import BytesIO
from uuid import uuid4

import cv2
import numpy as np
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import (
    preprocess_image as gradcam_preprocess_image,
    show_cam_on_image,
)

from app.config import GRADCAM_DIR, NORMALIZE_MEAN, NORMALIZE_STD, TARGET_IMAGE_SIZE
from app.inference.model_loader import DEVICE
from app.inference.domains.gastrointestinal import resnet50
from training.preprocessing.pipeline import preprocess_for_training

GRADCAM_DIR.mkdir(parents=True, exist_ok=True)
GRADCAM_SUPPORTED_DOMAINS = frozenset({"gastrointestinal"})


def generate_gradcam_from_bytes(image_bytes: bytes, *, domain: str) -> str | None:
    """Gera Grad-CAM da ResNet-50 para o domínio gastrointestinal."""
    if domain not in GRADCAM_SUPPORTED_DOMAINS:
        return None

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image_array = preprocess_for_training(np.array(image))
    resized = cv2.resize(image_array, TARGET_IMAGE_SIZE)
    rgb_image = resized.astype(np.float32) / 255.0
    input_tensor = gradcam_preprocess_image(
        rgb_image,
        mean=NORMALIZE_MEAN,
        std=NORMALIZE_STD,
    ).to(DEVICE)

    model = resnet50.torch_model
    target_layers = [model.layer4[-1]]
    cam = GradCAM(model=model, target_layers=target_layers)
    grayscale_cam = cam(input_tensor=input_tensor)[0]
    visualization = show_cam_on_image(rgb_image, grayscale_cam, use_rgb=True)

    output_path = GRADCAM_DIR / f"{uuid4()}.jpg"
    written = cv2.imwrite(
        str(output_path),
        cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR),
    )
    if not written:
        raise RuntimeError("Não foi possível persistir o Grad-CAM gerado.")
    return str(output_path)
