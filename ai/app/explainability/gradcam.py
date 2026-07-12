"""
Geração de Grad-CAM para explicabilidade das predições do ClinicAI.

Limitação importante, já documentada na monografia: o Grad-CAM é gerado
sobre a ResNet-50 especificamente, não sobre o Ensemble Stacking como um
todo. Isso acontece porque:
1. A PVTv2-B2 é um Vision Transformer, sem a noção de "camada
   convolucional alvo" que o Grad-CAM clássico precisa — explicar um
   Transformer exigiria uma técnica diferente (ex: mapas de atenção).
2. Mesmo entre as duas CNNs (ResNet-50 e EfficientNet-B4), o mapa de uma
   explica só aquele modelo, não a decisão final do meta-classificador,
   que combina as três saídas.

Ou seja: o Grad-CAM aqui é um apoio visual sobre uma das três entradas do
ensemble, não uma prova causal da decisão final. Isso deve continuar
sendo comunicado ao usuário na interface (já é, na tela de Revisão
Médica do frontend).

Limitação adicional: esta função está amarrada especificamente à
ResNet-50 do domínio gastrointestinal (`app.inference.domains.
gastrointestinal.resnet50`). Se um domínio novo for adicionado (ver
`app/inference/domains/README.md`), o Grad-CAM dele não vai funcionar
automaticamente — esta função precisará ser generalizada para receber
qual modelo/domínio usar como base.
"""

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


def generate_gradcam_from_bytes(image_bytes: bytes) -> str:
    """
    Gera o Grad-CAM da ResNet-50 para uma imagem enviada à API.

    Returns:
        Caminho do arquivo de imagem gerado (JPG), dentro de
        `app.config.GRADCAM_DIR`.
    """
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image = np.array(image)

    image = preprocess_for_training(image)
    image = cv2.resize(image, TARGET_IMAGE_SIZE)

    rgb_image = image.astype(np.float32) / 255.0

    input_tensor = gradcam_preprocess_image(
        rgb_image,
        mean=NORMALIZE_MEAN,
        std=NORMALIZE_STD,
    ).to(DEVICE)

    # Acessa o modelo PyTorch por trás do preditor registrado — o Grad-CAM
    # precisa da última camada convolucional, algo que só faz sentido
    # pedir a uma CNN específica, não à interface genérica BasePredictor.
    model = resnet50.torch_model
    target_layers = [model.layer4[-1]]

    cam = GradCAM(model=model, target_layers=target_layers)
    grayscale_cam = cam(input_tensor=input_tensor)[0]

    visualization = show_cam_on_image(rgb_image, grayscale_cam, use_rgb=True)

    filename = f"{uuid4()}.jpg"
    output_path = GRADCAM_DIR / filename

    cv2.imwrite(str(output_path), cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR))

    return str(output_path)
