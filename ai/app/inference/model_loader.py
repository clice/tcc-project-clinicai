"""
Responsável pelo carregamento do modelo de IA.
"""

from pathlib import Path

import torch
import torch.nn as nn

from app.config import MODEL_PATH


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class MockClassifier(nn.Module):
    """
    Modelo temporário apenas para validar
    integração com PyTorch.
    """

    def __init__(self):
        super().__init__()

        self.flatten = nn.Flatten()

        self.linear = nn.Linear(224 * 224 * 3, 2)

    def forward(self, x):
        x = self.flatten(x)

        return self.linear(x)


def load_model() -> nn.Module:
    """
    Carrega o modelo da IA.

    Nesta etapa:
    - usa modelo mock;
    - prepara estrutura para modelos reais.
    """

    model = MockClassifier()

    model.to(DEVICE)

    model.eval()

    return model


model = load_model()