"""
Interface comum a qualquer modelo preditivo do ClinicAI.

Qualquer arquitetura nova (CNN, Transformer, ensemble, ou algo totalmente
diferente no futuro) implementa esta interface e se registra em
`registry.py` — o resto do sistema (`predictor.py`, `main.py`) não precisa
saber nada sobre a arquitetura específica por trás de cada nome.
"""

from abc import ABC, abstractmethod

import numpy as np


class BasePredictor(ABC):
    """
    Contrato mínimo que todo modelo preditivo do ClinicAI deve cumprir.
    """

    #: Nome curto e estável do modelo (usado como chave no registro e
    #: retornado na resposta da API — ex: "resnet50", "ensemble_stacking").
    name: str

    #: Domínio clínico ao qual este modelo se aplica (ex: "gastrointestinal",
    #: "head_ct", "mammography"). Usado para rotear a predição certa
    #: conforme o tipo de exame — ver `app.inference.domain_registry`.
    domain: str

    @abstractmethod
    def predict_proba(self, image_tensor) -> np.ndarray:
        """
        Executa a inferência sobre uma imagem já pré-processada.

        Args:
            image_tensor: Tensor de entrada, já no formato esperado pelo
                modelo (normalizado, com dimensão de batch).

        Returns:
            Array numpy com as probabilidades por classe, na ordem
            definida em `app.config.CLASS_LABELS` (índice 0 = normal,
            índice 1 = anormal). Ex: `np.array([0.12, 0.88])`.
        """
        raise NotImplementedError
    