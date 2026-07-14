"""
Preditor genérico para qualquer arquitetura disponível na biblioteca
`timm` (CNNs e Vision Transformers).

Cobre hoje ResNet-50, EfficientNet-B4 e PVTv2-B2 (domínio gastrointestinal)
— mas serve para qualquer outro modelo do `timm`, de qualquer domínio,
sem precisar de código novo: basta instanciar com o nome do modelo e o
caminho dos pesos treinados (ver `app/inference/domains/`).
"""

from pathlib import Path

import numpy as np
import timm
import torch

from app.inference.base import BasePredictor
from app.inference.model_loader import DEVICE, load_torch_state_dict


class TimmCNNPredictor(BasePredictor):
    """
    Carrega um modelo `timm` sob demanda (lazy loading — só na primeira
    predição, não na importação do módulo) e mantém em memória depois.
    """

    def __init__(
        self,
        name: str,
        domain: str,
        timm_model_name: str,
        weights_path: Path,
        num_classes: int = 2,
    ):
        self.name = name
        self.domain = domain
        self.timm_model_name = timm_model_name
        self.weights_path = Path(weights_path)
        self.num_classes = num_classes
        self._model: torch.nn.Module | None = None

    def _ensure_loaded(self) -> torch.nn.Module:
        if self._model is None:
            model = timm.create_model(
                self.timm_model_name,
                pretrained=False,
                num_classes=self.num_classes,
            )
            state_dict = load_torch_state_dict(self.weights_path)
            model.load_state_dict(state_dict)
            model.to(DEVICE)
            model.eval()
            self._model = model
            print(f"[{self.name}] modelo carregado em {DEVICE} ({self.weights_path})")
        return self._model

    @property
    def torch_model(self) -> torch.nn.Module:
        """Acesso ao modelo PyTorch subjacente — usado pelo Grad-CAM, que
        precisa de uma camada específica do modelo, não só das
        probabilidades finais."""
        return self._ensure_loaded()

    def predict_proba(self, image_tensor) -> np.ndarray:
        model = self._ensure_loaded()

        with torch.no_grad():
            outputs = model(image_tensor.to(DEVICE))
            logits = outputs.logits if hasattr(outputs, "logits") else outputs
            probabilities = torch.softmax(logits, dim=1)

        return probabilities.cpu().numpy()[0]
    