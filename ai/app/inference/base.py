"""Interface comum aos preditores registrados no serviço de IA."""

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class BasePredictor(ABC):
    """Contrato mínimo de inferência e carregamento observável."""

    name: str
    domain: str

    @abstractmethod
    def predict_proba(self, image_tensor) -> np.ndarray:
        """Retorna as probabilidades na ordem das classes do domínio."""
        raise NotImplementedError

    def ensure_loaded(self):
        """Carrega os artefatos necessários e mantém o preditor em memória."""
        return None

    @property
    def is_loaded(self) -> bool:
        """Indica se todos os artefatos necessários já foram carregados."""
        return False

    @property
    def artifact_paths(self) -> tuple[Path, ...]:
        """Lista os artefatos físicos necessários por este preditor."""
        return ()
