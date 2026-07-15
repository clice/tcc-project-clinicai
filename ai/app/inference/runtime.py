"""Inicialização, readiness e catálogo observável do serviço de IA."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from app.config import (
    ACTIVE_MODEL_BY_DOMAIN,
    CLASS_LABELS_BY_DOMAIN,
    MODEL_ARTIFACTS_BY_DOMAIN,
    MODEL_MANIFEST_BY_DOMAIN,
    MODEL_VERSION_FALLBACK,
)
from app.inference.model_loader import describe_device
from app.inference.registry import (
    available_models,
    exam_types_for_domain,
    get_predictor,
)

_RUNTIME_LOCK = Lock()
_RUNTIME_STATE: dict[str, object] = {
    "initialized": False,
    "ready": False,
    "error": None,
    "loaded_at": None,
    "model_versions": {},
}


def _read_manifest(domain: str) -> dict:
    path = MODEL_MANIFEST_BY_DOMAIN.get(domain)
    if path is None or not path.is_file():
        raise FileNotFoundError(f"Manifesto do domínio '{domain}' não encontrado em: {path}")

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Manifesto inválido para o domínio '{domain}'.") from exc

    if manifest.get("domain") != domain:
        raise RuntimeError(
            f"Manifesto informa domínio '{manifest.get('domain')}', esperado '{domain}'."
        )

    model_version = str(manifest.get("model_version") or "").strip()
    if not model_version:
        raise RuntimeError(f"Manifesto do domínio '{domain}' não informa model_version.")

    expected_names = {path.name for path in MODEL_ARTIFACTS_BY_DOMAIN.get(domain, ())}
    manifest_names = {
        str(item.get("name"))
        for item in manifest.get("artifacts", [])
        if isinstance(item, dict)
    }
    missing = sorted(expected_names - manifest_names)
    if missing:
        raise RuntimeError(
            f"Manifesto do domínio '{domain}' não descreve: {', '.join(missing)}."
        )

    return manifest


def _artifact_rows(domain: str, loaded: bool) -> list[dict[str, object]]:
    return [
        {
            "name": path.name,
            "path": str(path),
            "exists": path.is_file(),
            "loaded": bool(loaded and path.is_file()),
        }
        for path in MODEL_ARTIFACTS_BY_DOMAIN.get(domain, ())
    ]


def initialize_runtime(force: bool = False) -> dict[str, object]:
    """Carrega os modelos ativos e seus quatro artefatos antes da inferência."""
    with _RUNTIME_LOCK:
        if _RUNTIME_STATE["initialized"] and not force:
            return runtime_snapshot()

        _RUNTIME_STATE.update(
            {
                "initialized": True,
                "ready": False,
                "error": None,
                "loaded_at": None,
                "model_versions": {},
            }
        )

        versions: dict[str, str] = {}
        try:
            for domain, model_name in ACTIVE_MODEL_BY_DOMAIN.items():
                labels = CLASS_LABELS_BY_DOMAIN.get(domain)
                if not labels:
                    raise RuntimeError(f"Domínio '{domain}' não possui classes configuradas.")

                expected_artifacts = MODEL_ARTIFACTS_BY_DOMAIN.get(domain, ())
                if not expected_artifacts:
                    raise RuntimeError(
                        f"Domínio '{domain}' não possui artefatos declarados."
                    )
                if domain == "gastrointestinal" and len(expected_artifacts) != 4:
                    raise RuntimeError(
                        "O domínio gastrointestinal deve declarar os três pesos base "
                        "e o meta-classificador (quatro artefatos)."
                    )

                missing = [str(path) for path in expected_artifacts if not path.is_file()]
                if missing:
                    raise FileNotFoundError(
                        "Artefatos ausentes para o domínio "
                        f"'{domain}': {', '.join(missing)}"
                    )

                manifest = _read_manifest(domain)
                predictor = get_predictor(domain, model_name)
                predictor.ensure_loaded()
                if not predictor.is_loaded:
                    raise RuntimeError(
                        f"Preditor ativo '{domain}.{model_name}' não confirmou o carregamento."
                    )
                if set(predictor.artifact_paths) != set(expected_artifacts):
                    raise RuntimeError(
                        f"Preditor '{domain}.{model_name}' não referencia os quatro "
                        "artefatos declarados para o domínio."
                    )
                versions[domain] = str(manifest["model_version"])

            _RUNTIME_STATE.update(
                {
                    "ready": True,
                    "loaded_at": datetime.now(timezone.utc).isoformat(),
                    "model_versions": versions,
                }
            )
        except Exception as exc:  # readiness deve permanecer consultável
            _RUNTIME_STATE["error"] = f"{type(exc).__name__}: {exc}"

        return runtime_snapshot()


def runtime_snapshot() -> dict[str, object]:
    ready = bool(_RUNTIME_STATE["ready"])
    domains: dict[str, object] = {}
    total = 0
    loaded = 0
    versions = dict(_RUNTIME_STATE.get("model_versions", {}))

    for domain, model_name in ACTIVE_MODEL_BY_DOMAIN.items():
        try:
            predictor = get_predictor(domain, model_name)
            predictor_loaded = predictor.is_loaded
        except Exception:
            predictor_loaded = False
        rows = _artifact_rows(domain, predictor_loaded)
        total += len(rows)
        loaded += sum(1 for row in rows if row["loaded"])
        domains[domain] = {
            "active_model": model_name,
            "model_version": versions.get(domain, MODEL_VERSION_FALLBACK),
            "loaded": predictor_loaded,
            "artifacts": rows,
        }

    return {
        "status": "ok" if ready else "not_ready",
        "service": "clinicai-ai",
        "initialized": bool(_RUNTIME_STATE["initialized"]),
        "ready": ready,
        "error": _RUNTIME_STATE["error"],
        "loaded_at": _RUNTIME_STATE["loaded_at"],
        "device": describe_device(),
        "artifact_summary": {"expected": total, "loaded": loaded},
        "domains": domains,
    }


def model_catalog() -> dict[str, object]:
    snapshot = runtime_snapshot()
    versions = dict(_RUNTIME_STATE.get("model_versions", {}))
    domains: dict[str, object] = {}

    for domain, active_model in ACTIVE_MODEL_BY_DOMAIN.items():
        try:
            predictor = get_predictor(domain, active_model)
            predictor_loaded = predictor.is_loaded
        except Exception:
            predictor_loaded = False
        domains[domain] = {
            "active_model": active_model,
            "available_models": available_models(domain),
            "exam_types": exam_types_for_domain(domain),
            "classes": CLASS_LABELS_BY_DOMAIN.get(domain, {}),
            "model_version": versions.get(domain, MODEL_VERSION_FALLBACK),
            "loaded": predictor_loaded,
            "artifacts": _artifact_rows(domain, predictor_loaded),
        }

    return {
        "ready": snapshot["ready"],
        "device": snapshot["device"],
        "domains": domains,
    }


def model_version_for_domain(domain: str) -> str:
    versions = dict(_RUNTIME_STATE.get("model_versions", {}))
    return versions.get(domain, MODEL_VERSION_FALLBACK)


def is_runtime_ready() -> bool:
    return bool(_RUNTIME_STATE["ready"])
