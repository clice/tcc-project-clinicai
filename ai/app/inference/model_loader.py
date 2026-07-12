"""
Utilitários genéricos de carregamento de modelos.

Antes, este arquivo tinha a arquitetura ResNet-50 e o carregamento
hardcoded (inclusive um `model = load_model()` executado na importação
do módulo — um único modelo, sempre carregado, sem opção de escolha).
Agora contém só o que é comum a qualquer modelo: o dispositivo de
execução e a função de carregar um `state_dict` do disco com checagem de
existência. Cada preditor (`TimmCNNPredictor`, `EnsembleStackingPredictor`)
cuida de carregar a própria arquitetura, sob demanda.
"""

from pathlib import Path

import torch

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_torch_state_dict(path: Path, weights_only: bool = True) -> dict:
    """
    Carrega um `state_dict` do disco, com uma mensagem de erro útil se o
    arquivo não existir (em vez do `FileNotFoundError` genérico do
    PyTorch, que não diz onde o serviço esperava encontrar o arquivo).
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Pesos do modelo não encontrados.\nEsperado em: {path}"
        )

    return torch.load(path, map_location=DEVICE, weights_only=weights_only)
