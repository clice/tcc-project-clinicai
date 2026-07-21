#!/usr/bin/env python3
"""Regenera os Grad-CAM demonstrativos em uma área de staging."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "backend" / "demo_assets"
MANIFEST = ASSETS / "manifest.json"
STAGING = Path("/tmp/clinicai-demo-gradcam-staging")

sys.path.insert(0, str(ROOT / "ai"))

from app.explainability.gradcam import (
    crop_attribution_to_visual_roi,
    generate_ensemble_attribution_from_bytes,
)
from training.preprocessing.pipeline import (
    preprocess_for_training,
)


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)

    return digest.hexdigest()


def main():
    manifest = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    if STAGING.exists():
        shutil.rmtree(STAGING)

    output_dir = STAGING / "gradcam"
    output_dir.mkdir(parents=True)

    definitions = [
        item
        for item in manifest["exams"]
        if item.get("analysis")
    ]

    expected_count = manifest["dataset"]["ai_analyses"]

    if len(definitions) != expected_count:
        raise RuntimeError(
            f"Quantidade divergente: {len(definitions)} != {expected_count}"
        )

    for index, definition in enumerate(definitions, start=1):
        analysis = definition["analysis"]
        source = ASSETS / definition["source_asset"]["path"]
        image_bytes = source.read_bytes()

        processed = preprocess_for_training(
            np.asarray(Image.open(source).convert("RGB"))
        )

        visual_image, _visual_map = (
            crop_attribution_to_visual_roi(
                processed,
                np.zeros(
                    processed.shape[:2],
                    dtype=np.float32,
                ),
            )
        )

        expected_height, expected_width = (
            visual_image.shape[:2]
        )

        print(
            f"[{index:02d}/{len(definitions)}] "
            f"{definition['exam_key']} | "
            f"ROI visual {expected_width}x{expected_height}",
            flush=True,
        )

        result = generate_ensemble_attribution_from_bytes(
            image_bytes,
            domain="gastrointestinal",
            output_dir=output_dir,
        )

        if result is None or result.path is None:
            raise RuntimeError(
                f"Mapa ausente em {definition['exam_key']}."
            )

        if result.predicted_class != analysis["prediction_class"]:
            raise RuntimeError(
                f"Classe divergente em {definition['exam_key']}."
            )

        actual_confidence = round(
            max(result.final_probabilities),
            4,
        )

        if actual_confidence != analysis["confidence"]:
            raise RuntimeError(
                f"Confiança divergente em {definition['exam_key']}: "
                f"{actual_confidence} != {analysis['confidence']}"
            )

        generated = Path(result.path)
        target = STAGING / analysis["gradcam_asset"]["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        generated.replace(target)

        with Image.open(target) as output:
            if output.size != (expected_width, expected_height):
                raise RuntimeError(
                    f"Dimensão divergente em {definition['exam_key']}: "
                    f"{output.size} != "
                    f"{(expected_width, expected_height)}"
                )

        analysis["gradcam_asset"]["size_bytes"] = (
            target.stat().st_size
        )
        analysis["gradcam_asset"]["sha256"] = sha256(target)

    (STAGING / "manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"OK: {len(definitions)} mapas validados em {STAGING}."
    )


if __name__ == "__main__":
    main()
