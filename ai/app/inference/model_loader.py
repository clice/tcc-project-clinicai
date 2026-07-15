"""Seleção de dispositivo e carregamento seguro dos pesos PyTorch."""

from pathlib import Path

import torch


def select_device(cuda_available: bool | None = None) -> torch.device:
    """Seleciona CUDA quando disponível; caso contrário, usa CPU."""
    available = torch.cuda.is_available() if cuda_available is None else cuda_available
    return torch.device("cuda" if available else "cpu")


DEVICE = select_device()


def describe_device(device: torch.device = DEVICE) -> dict[str, object]:
    """Expõe informações estáveis para /health e /models."""
    details: dict[str, object] = {
        "type": device.type,
        "value": str(device),
        "cuda_available": bool(torch.cuda.is_available()),
    }
    if device.type == "cuda" and torch.cuda.is_available():
        index = device.index or 0
        details.update(
            {
                "index": index,
                "name": torch.cuda.get_device_name(index),
                "device_count": torch.cuda.device_count(),
            }
        )
    return details


def load_torch_state_dict(path: Path, weights_only: bool = True) -> dict:
    """Carrega um state_dict no dispositivo selecionado."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Pesos do modelo não encontrados.\nEsperado em: {path}")
    return torch.load(path, map_location=DEVICE, weights_only=weights_only)
