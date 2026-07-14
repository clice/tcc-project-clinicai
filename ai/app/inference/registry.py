"""
Registro central de modelos preditivos disponíveis no ClinicAI.

Indexado por (domínio, nome) — não só por nome — porque dois domínios
clínicos diferentes podem ter um modelo com o mesmo nome (ex: uma
ResNet-50 para gastrointestinal e outra para tomografia de cabeça). Sem
esse namespace, registrar o segundo domínio sobrescreveria o primeiro
silenciosamente, sem nenhum erro.

Para adicionar um modelo novo: implemente `BasePredictor` (em geral,
`TimmCNNPredictor` já serve para qualquer arquitetura da biblioteca
`timm`), garanta que `predictor.domain` e `predictor.name` estejam
preenchidos, e registre com `register(predictor)` em
`app/inference/domains/<seu_dominio>.py`. Ver `domains/README.md`.
"""

from app.inference.base import BasePredictor

_REGISTRY: dict[tuple[str, str], BasePredictor] = {}


def register(predictor: BasePredictor) -> None:
    """Registra um modelo preditivo pela chave (domain, name)."""
    _REGISTRY[(predictor.domain, predictor.name)] = predictor


def get_predictor(domain: str, name: str) -> BasePredictor:
    """
    Busca um modelo preditivo registrado por domínio + nome.

    Levanta KeyError com a lista de modelos disponíveis naquele domínio
    se a combinação não existir — evita uma mensagem genérica quando
    alguém digitar o nome errado em `ACTIVE_MODEL_BY_DOMAIN`.
    """
    key = (domain, name)
    if key not in _REGISTRY:
        disponiveis = [n for d, n in _REGISTRY if d == domain]
        disponiveis_str = ", ".join(sorted(disponiveis)) or "(nenhum modelo registrado para este domínio)"
        raise KeyError(
            f"Modelo '{name}' não registrado para o domínio '{domain}'. "
            f"Disponíveis nesse domínio: {disponiveis_str}"
        )
    return _REGISTRY[key]


def available_domains() -> list[str]:
    """Lista os domínios clínicos que têm ao menos um modelo registrado."""
    return sorted({domain for domain, _ in _REGISTRY})


def available_models(domain: str | None = None) -> list[str]:
    """
    Lista os modelos registrados. Se `domain` for informado, restringe a
    esse domínio; senão, lista todos como "domínio.nome".
    """
    if domain is not None:
        return sorted(name for d, name in _REGISTRY if d == domain)
    return sorted(f"{d}.{name}" for d, name in _REGISTRY)


def resolve_active_predictor(exam_type: str | None) -> BasePredictor:
    """
    Resolve, a partir do tipo de exame (campo `exam_type` vindo do
    backend), qual modelo preditivo deve ser usado.

    Fluxo: exam_type -> domínio clínico (`EXAM_TYPE_TO_DOMAIN`) -> nome
    do modelo ativo naquele domínio (`ACTIVE_MODEL_BY_DOMAIN`) -> modelo
    registrado. Se `exam_type` for None ou não estiver mapeado, usa
    `DEFAULT_DOMAIN`.
    """
    from app.config import ACTIVE_MODEL_BY_DOMAIN, DEFAULT_DOMAIN, EXAM_TYPE_TO_DOMAIN

    domain = EXAM_TYPE_TO_DOMAIN.get(exam_type, DEFAULT_DOMAIN) if exam_type else DEFAULT_DOMAIN

    if domain not in ACTIVE_MODEL_BY_DOMAIN:
        raise KeyError(
            f"Domínio '{domain}' não tem modelo ativo configurado em "
            f"ACTIVE_MODEL_BY_DOMAIN. Domínios com modelo ativo: "
            f"{', '.join(sorted(ACTIVE_MODEL_BY_DOMAIN)) or '(nenhum)'}"
        )

    model_name = ACTIVE_MODEL_BY_DOMAIN[domain]
    return get_predictor(domain, model_name)
