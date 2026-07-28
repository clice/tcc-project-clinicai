#!/usr/bin/env python3
"""
Regenera as análises e os mapas demonstrativos em staging.

O script não altera os ativos oficiais em backend/demo_assets.
Ele produz:

- 72 novos mapas Grad-CAM;
- um manifesto candidato;
- um relatório comparativo entre os modelos antigos e os atuais.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "backend" / "demo_assets"
MANIFEST = ASSETS / "manifest.json"

STAGING = Path(
    os.environ.get(
        "CLINICAI_DEMO_STAGING",
        "/tmp/clinicai-demo-v012",
    )
)

DOMAIN = "gastrointestinal"
EXPECTED_MODEL_VERSION = "0.1.2"
EXPECTED_MODEL_RELEASE = "models-v0.1.2"
EXPECTED_OPERATIONAL_FOLD = 1
EXPECTED_ANALYSIS_COUNT = 72

sys.path.insert(0, str(ROOT / "ai"))

from app.inference.predictor import predict_image
from app.inference.runtime import initialize_runtime


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def safe_relative_path(value: object) -> Path:
    path = Path(str(value))

    if (
        not path.parts
        or path.is_absolute()
        or ".." in path.parts
    ):
        raise RuntimeError(
            f"Caminho relativo inválido: {path}."
        )

    return path


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def recompute_manifest_summary(
    manifest: dict,
) -> dict:
    exams = manifest["exams"]

    prediction_labels = Counter(
        definition["analysis"]["prediction_label"]
        for definition in exams
        if definition.get("analysis") is not None
    )

    source_labels = Counter(
        definition["source_asset"]["label"]
        for definition in exams
    )

    statuses = Counter(
        definition["status"]
        for definition in exams
    )

    reviewed_exams = sum(
        definition.get("review") is not None
        for definition in exams
    )

    source_prediction_divergences = sum(
        definition["source_asset"]["label"]
        != definition["analysis"]["prediction_label"]
        for definition in exams
        if definition.get("analysis") is not None
    )

    manifest["dataset"]["ai_analyses"] = sum(
        definition.get("analysis") is not None
        for definition in exams
    )
    manifest["dataset"]["reviewed_exams"] = (
        reviewed_exams
    )
    manifest["dataset"][
        "real_source_prediction_divergences"
    ] = source_prediction_divergences

    manifest["summary"] = {
        "prediction_labels": dict(
            sorted(prediction_labels.items())
        ),
        "source_labels": dict(
            sorted(source_labels.items())
        ),
        "statuses": dict(
            sorted(statuses.items())
        ),
    }

    return {
        "prediction_labels": dict(
            sorted(prediction_labels.items())
        ),
        "source_labels": dict(
            sorted(source_labels.items())
        ),
        "statuses": dict(
            sorted(statuses.items())
        ),
        "reviewed_exams": reviewed_exams,
        "source_prediction_divergences": (
            source_prediction_divergences
        ),
    }


def main() -> None:
    original_manifest = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )
    candidate_manifest = copy.deepcopy(
        original_manifest
    )

    runtime = initialize_runtime(force=True)

    if not runtime.get("ready"):
        raise RuntimeError(
            "O runtime de IA não ficou pronto: "
            f"{runtime.get('error')}"
        )

    runtime_version = (
        runtime["domains"][DOMAIN]["model_version"]
    )

    if runtime_version != EXPECTED_MODEL_VERSION:
        raise RuntimeError(
            "Versão operacional inesperada: "
            f"{runtime_version!r}; "
            f"esperada {EXPECTED_MODEL_VERSION!r}."
        )

    definitions = [
        definition
        for definition in candidate_manifest["exams"]
        if definition.get("analysis") is not None
    ]

    if len(definitions) != EXPECTED_ANALYSIS_COUNT:
        raise RuntimeError(
            "Quantidade inesperada de análises: "
            f"{len(definitions)}."
        )

    if STAGING.exists():
        for child in STAGING.iterdir():
            if child.is_symlink() or not child.is_dir():
                child.unlink()
            else:
                shutil.rmtree(child)
    else:
        STAGING.mkdir(parents=True)

    STAGING.mkdir(
        parents=True,
        exist_ok=True,
    )
    gradcam_root = STAGING / "gradcam"
    gradcam_root.mkdir(parents=True)

    prediction_changes: list[dict] = []
    review_inconsistencies: list[dict] = []
    generated_paths: set[str] = set()

    for index, definition in enumerate(
        definitions,
        start=1,
    ):
        exam_key = definition["exam_key"]
        analysis = definition["analysis"]
        previous_analysis = copy.deepcopy(analysis)

        source_relative = safe_relative_path(
            definition["source_asset"]["path"]
        )
        source_path = ASSETS / source_relative

        if not source_path.is_file():
            raise RuntimeError(
                f"Imagem ausente em {exam_key}: "
                f"{source_path}."
            )

        started_at = perf_counter()

        result = predict_image(
            source_path.read_bytes(),
            definition["exam_type"],
        )

        processing_time_ms = max(
            1,
            round(
                (perf_counter() - started_at) * 1000
            ),
        )

        if result["model_version"] != (
            EXPECTED_MODEL_VERSION
        ):
            raise RuntimeError(
                f"{exam_key}: versão inesperada "
                f"{result['model_version']!r}."
            )

        if not result["gradcam_available"]:
            raise RuntimeError(
                f"{exam_key}: Grad-CAM indisponível."
            )

        encoded_gradcam = result.get(
            "gradcam_base64"
        )

        if not encoded_gradcam:
            raise RuntimeError(
                f"{exam_key}: conteúdo Grad-CAM ausente."
            )

        gradcam_bytes = base64.b64decode(
            encoded_gradcam,
            validate=True,
        )

        actual_gradcam_hash = sha256_bytes(
            gradcam_bytes
        )

        if actual_gradcam_hash != result.get(
            "gradcam_sha256"
        ):
            raise RuntimeError(
                f"{exam_key}: hash do Grad-CAM divergente."
            )

        gradcam_relative = safe_relative_path(
            analysis["gradcam_asset"]["path"]
        )
        relative_key = gradcam_relative.as_posix()

        if relative_key in generated_paths:
            raise RuntimeError(
                f"Caminho Grad-CAM repetido: "
                f"{relative_key}."
            )

        generated_paths.add(relative_key)

        target = STAGING / gradcam_relative
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        target.write_bytes(gradcam_bytes)

        prediction_class = int(
            result["prediction_class"]
        )
        prediction_label = str(result["label"])
        confidence = float(result["confidence"])

        analysis.update(
            {
                "prediction_class": prediction_class,
                "prediction_label": prediction_label,
                "confidence": confidence,
                "model_name": str(
                    result["model_name"]
                ),
                "model_version": str(
                    result["model_version"]
                ),
                "device": str(result["device"]),
                "processing_time_ms": (
                    processing_time_ms
                ),
                "attribution_method": result.get(
                    "attribution_method"
                ),
                "attribution_target_layers": (
                    result.get(
                        "attribution_target_layers"
                    )
                ),
                "attribution_local_evidence": (
                    result.get(
                        "attribution_local_evidence"
                    )
                ),
                "attribution_branch_weights": (
                    result.get(
                        "attribution_branch_weights"
                    )
                ),
                "attribution_branch_cam_raw_maxima": (
                    result.get(
                        "attribution_branch_cam_raw_maxima"
                    )
                ),
                "attribution_unavailable_reason": (
                    result.get(
                        "attribution_unavailable_reason"
                    )
                ),
            }
        )

        analysis["gradcam_asset"].update(
            {
                "kind": "gradcam",
                "path": relative_key,
                "sha256": actual_gradcam_hash,
                "size_bytes": len(gradcam_bytes),
            }
        )

        previous_class = int(
            previous_analysis["prediction_class"]
        )
        previous_label = str(
            previous_analysis["prediction_label"]
        )

        if (
            previous_class != prediction_class
            or previous_label != prediction_label
        ):
            prediction_changes.append(
                {
                    "exam_key": exam_key,
                    "source_label": definition[
                        "source_asset"
                    ]["label"],
                    "previous_class": previous_class,
                    "previous_label": previous_label,
                    "current_class": prediction_class,
                    "current_label": prediction_label,
                    "previous_confidence": (
                        previous_analysis["confidence"]
                    ),
                    "current_confidence": confidence,
                }
            )

        review = definition.get("review")

        if review is not None:
            reviewed_label = str(
                review["reviewed_label"]
            )
            expected_agreement = (
                reviewed_label == prediction_label
            )
            expected_status = (
                "completed"
                if expected_agreement
                else "completed_with_divergence"
            )

            stored_agreement = bool(
                review["agrees_with_ai"]
            )
            stored_status = str(
                definition["status"]
            )

            if (
                stored_agreement
                != expected_agreement
                or stored_status
                != expected_status
            ):
                review_inconsistencies.append(
                    {
                        "exam_key": exam_key,
                        "prediction_label": (
                            prediction_label
                        ),
                        "reviewed_label": (
                            reviewed_label
                        ),
                        "stored_agreement": (
                            stored_agreement
                        ),
                        "expected_agreement": (
                            expected_agreement
                        ),
                        "stored_status": (
                            stored_status
                        ),
                        "expected_status": (
                            expected_status
                        ),
                    }
                )

                review["review_notes"] = (
                    "Resultado da IA confirmado "
                    "na revisão demonstrativa."
                    if expected_agreement
                    else
                    "Resultado da IA divergente "
                    "da revisão demonstrativa."
                )

            review["agrees_with_ai"] = (
                expected_agreement
            )
            definition["status"] = (
                expected_status
            )

        print(
            f"[{index:02d}/{len(definitions)}] "
            f"{exam_key}: "
            f"{previous_label} → {prediction_label} | "
            f"confiança={confidence:.4f} | "
            f"{processing_time_ms} ms",
            flush=True,
        )

    candidate_manifest["model"].update(
        {
            "name": "ensemble_stacking",
            "version": EXPECTED_MODEL_VERSION,
            "release": EXPECTED_MODEL_RELEASE,
            "operational_fold": (
                EXPECTED_OPERATIONAL_FOLD
            ),
            "training_protocol": (
                "viana_codigo_kfold3_roi_sh_da"
            ),
        }
    )

    current_summary = recompute_manifest_summary(
        candidate_manifest
    )

    comparison = {
        "model_before": original_manifest.get(
            "model"
        ),
        "model_after": candidate_manifest.get(
            "model"
        ),
        "analyzed_exams": len(definitions),
        "generated_gradcams": len(
            generated_paths
        ),
        "prediction_change_count": len(
            prediction_changes
        ),
        "prediction_changes": (
            prediction_changes
        ),
        "review_inconsistency_count": len(
            review_inconsistencies
        ),
        "review_inconsistencies": (
            review_inconsistencies
        ),
        "candidate_summary": current_summary,
    }

    write_json(
        STAGING / "manifest.json",
        candidate_manifest,
    )
    write_json(
        STAGING / "comparison.json",
        comparison,
    )

    print()
    print(
        f"Staging concluído em: {STAGING}"
    )
    print(
        f"Mapas gerados: {len(generated_paths)}"
    )
    print(
        "Predições alteradas: "
        f"{len(prediction_changes)}"
    )
    print(
        "Revisões identificadas e reconciliadas: "
        f"{len(review_inconsistencies)}"
    )
    print(
        "Divergências entre rótulo de origem e "
        "predição atual: "
        f"{current_summary['source_prediction_divergences']}"
    )


if __name__ == "__main__":
    main()
