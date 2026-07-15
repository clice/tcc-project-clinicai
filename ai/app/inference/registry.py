"""Registro central e roteamento explícito dos modelos do ClinicAI."""

from app.inference.base import BasePredictor

_REGISTRY: dict[tuple[str, str], BasePredictor] = {}


class UnsupportedExamTypeError(ValueError):
    """O tipo de exame não foi informado ou não possui domínio configurado."""


class ModelConfigurationError(RuntimeError):
    """A configuração aponta para um domínio/modelo não registrado."""


def register(predictor: BasePredictor) -> None:
    _REGISTRY[(predictor.domain, predictor.name)] = predictor


def get_predictor(domain: str, name: str) -> BasePredictor:
    key = (domain, name)
    if key not in _REGISTRY:
        available = [model for registered_domain, model in _REGISTRY if registered_domain == domain]
        raise ModelConfigurationError(
            f"Modelo '{name}' não registrado para o domínio '{domain}'. "
            f"Disponíveis: {', '.join(sorted(available)) or '(nenhum)'}."
        )
    return _REGISTRY[key]


def available_domains() -> list[str]:
    return sorted({domain for domain, _ in _REGISTRY})


def available_models(domain: str | None = None) -> list[str]:
    if domain is not None:
        return sorted(name for registered_domain, name in _REGISTRY if registered_domain == domain)
    return sorted(f"{domain}.{name}" for domain, name in _REGISTRY)


def registered_predictors(domain: str | None = None) -> list[BasePredictor]:
    predictors = [
        predictor
        for (registered_domain, _), predictor in _REGISTRY.items()
        if domain is None or registered_domain == domain
    ]
    return sorted(predictors, key=lambda item: (item.domain, item.name))


def normalize_exam_type(exam_type: str | None) -> str:
    normalized = (exam_type or "").strip().lower()
    if not normalized:
        raise UnsupportedExamTypeError("exam_type é obrigatório para selecionar o domínio clínico.")
    return normalized


def resolve_exam_domain(exam_type: str | None) -> str:
    from app.config import EXAM_TYPE_TO_DOMAIN

    normalized = normalize_exam_type(exam_type)
    domain = EXAM_TYPE_TO_DOMAIN.get(normalized)
    if domain is None:
        supported = ", ".join(sorted(EXAM_TYPE_TO_DOMAIN))
        raise UnsupportedExamTypeError(
            f"Tipo de exame '{normalized}' não suportado. Tipos aceitos: {supported}."
        )
    return domain


def exam_types_for_domain(domain: str) -> list[str]:
    from app.config import EXAM_TYPE_TO_DOMAIN

    return sorted(
        exam_type
        for exam_type, mapped_domain in EXAM_TYPE_TO_DOMAIN.items()
        if mapped_domain == domain
    )


def resolve_active_predictor(exam_type: str | None) -> BasePredictor:
    from app.config import ACTIVE_MODEL_BY_DOMAIN

    domain = resolve_exam_domain(exam_type)
    model_name = ACTIVE_MODEL_BY_DOMAIN.get(domain)
    if model_name is None:
        raise ModelConfigurationError(
            f"Domínio '{domain}' não possui modelo ativo configurado."
        )
    return get_predictor(domain, model_name)
