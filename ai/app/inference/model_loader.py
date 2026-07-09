"""
Carregamento do modelo treinado do ClinicAI.
"""

from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models


# =========================================================
# CONFIGURAÇÕES
# =========================================================

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

NUM_CLASSES = 2


# =========================================================
# MODELO
# =========================================================

def create_model() -> nn.Module:
    """
    Cria arquitetura ResNet50 binária.
    """

    model = models.resnet50(
        weights=None
    )

    in_features = model.fc.in_features

    model.fc = nn.Linear(
        in_features,
        NUM_CLASSES,
    )

    return model


# =========================================================
# LOAD
# =========================================================

def load_model() -> nn.Module:
    """
    Carrega modelo treinado do disco.
    """

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            (
                "Modelo treinado não encontrado.\n"
                f"Esperado em: {MODEL_PATH}"
            )
        )

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

    print(
        f"\nModelo carregado com sucesso em: {DEVICE}"
    )

    return model


# =========================================================
# SINGLETON
# =========================================================

model = load_model()
