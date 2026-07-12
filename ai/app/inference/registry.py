"""
Registro central de modelos preditivos disponíveis no ClinicAI.

Para adicionar um novo modelo no futuro: implemente `BasePredictor`
(em geral, `TimmCNNPredictor` já serve para qualquer arquitetura
disponível na biblioteca `timm`, bastando trocar o nome), instancie em
`models_config.py` e registre aqui com `register(nome, instancia)`.
Nenhum outro arquivo do sistema precisa mudar.
"""

from app.inference.base import BasePredictor

_REGISTRY: dict[str, BasePredictor] = {}


def register(name: str, predictor: BasePredictor) -> None:
    """Registra um modelo preditivo pelo nome."""
    _REGISTRY[name] = predictor


def get_predictor(name: str) -> BasePredictor:
    """
    Busca um modelo preditivo registrado pelo nome.

    Levanta KeyError com a lista de modelos disponíveis se o nome não
    existir — evita uma mensagem genérica de "None não tem tal atributo"
    quando alguém digitar o nome errado em `ACTIVE_MODEL_NAME`.
    """
    if name not in _REGISTRY:
        disponiveis = ", ".join(sorted(_REGISTRY)) or "(nenhum registrado ainda)"
        raise KeyError(f"Modelo '{name}' não registrado. Disponíveis: {disponiveis}")
    return _REGISTRY[name]


def available_models() -> list[str]:
    """Lista os nomes de todos os modelos registrados."""
    return sorted(_REGISTRY)
