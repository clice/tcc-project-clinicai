"""
Responsável pelo carregamento do modelo de IA.
"""

import torch
import torch.nn as nn
from torchvision import models

from app.config import MODEL_PATH


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def create_resnet50_model(num_classes: int = 2)-> nn.Module:
    """
    Cria uma ResNet-50 adaptada para classificação binária.

    A camada final original é substituída para retornar
    duas classes: normal e abnormal.
    """
    
    model = models.resnet50(weights=None)
    
    in_features = model.fc.in_features
    
    model.fc = nn.Linear(in_features, num_classes)
    
    model.fc = nn.Linear(in_features, num_classes)
    
    return model


def load_model() -> nn.Module:
    """
    Carrega o modelo da IA.

    Se existir um arquivo de pesos em MODEL_PATH, ele será carregado.
    Caso contrário, usa uma ResNet-50 sem treinamento específico.
    """

    model = create_resnet50_model(num_classes=2)
    
    if MODEL_PATH.exists():
        state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
        model.load_state_dict(state_dict)

    model.to(DEVICE)
    model.eval()

    return model


model = load_model()