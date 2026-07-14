#!/usr/bin/env python3
"""Gera o manifesto com tamanho e SHA-256 dos modelos do ClinicAI."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ARTEFATOS = (
    "resnet50.pt",
    "efficientnet_b4.pt",
    "pvt_v2_b2.pt",
    "meta_classificador.joblib",
)


def calcular_sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--models-dir", type=Path, default=Path("ai/models/exported/gastrointestinal"))
    parser.add_argument(
        "--output", type=Path,
        default=Path("ai/models/exported/gastrointestinal/manifesto_modelos.json"),
    )
    args = parser.parse_args()
    faltantes = [nome for nome in ARTEFATOS if not (args.models_dir / nome).is_file()]
    if faltantes:
        parser.error(f"artefatos ausentes em {args.models_dir}: {', '.join(faltantes)}")
    manifesto = {
        "schema_version": 1,
        "release_tag": args.release_tag,
        "model_version": args.model_version,
        "domain": "gastrointestinal",
        "artifacts": [
            {
                "name": nome,
                "size_bytes": (args.models_dir / nome).stat().st_size,
                "sha256": calcular_sha256(args.models_dir / nome),
            }
            for nome in ARTEFATOS
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifesto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Manifesto gerado em {args.output}")


if __name__ == "__main__":
    main()

