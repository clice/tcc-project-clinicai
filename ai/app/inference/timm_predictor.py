"""Preditor genérico para arquiteturas da biblioteca timm."""

from pathlib import Path
from threading import Lock

import numpy as np
import timm
import torch

from app.inference.base import BasePredictor
from app.inference.model_loader import DEVICE, load_torch_state_dict


class TimmCNNPredictor(BasePredictor):
    """Carrega uma arquitetura e seu state_dict uma única vez."""

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
        self._load_lock = Lock()

    def ensure_loaded(self) -> torch.nn.Module:
        if self._model is None:
            with self._load_lock:
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
                    print(f"[{self.domain}.{self.name}] carregado em {DEVICE}")
        return self._model

    # Compatibilidade com chamadas internas anteriores.
    def _ensure_loaded(self) -> torch.nn.Module:
        return self.ensure_loaded()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def artifact_paths(self) -> tuple[Path, ...]:
        return (self.weights_path,)

    @property
    def torch_model(self) -> torch.nn.Module:
        return self.ensure_loaded()

    def predict_proba(self, image_tensor) -> np.ndarray:
        model = self.ensure_loaded()
        with torch.no_grad():
            outputs = model(image_tensor.to(DEVICE))
            logits = outputs.logits if hasattr(outputs, "logits") else outputs
            probabilities = torch.softmax(logits, dim=1)
        return probabilities.cpu().numpy()[0]
