"""Configuração da raiz de dados do serviço de IA."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class StorageConfigurationTests(
    unittest.TestCase
):
    def read_paths(
        self,
        configured_data_dir: str | None,
    ) -> dict[str, str]:
        environment = os.environ.copy()

        if configured_data_dir is None:
            environment.pop(
                "CLINICAI_DATA_DIR",
                None,
            )
        else:
            environment[
                "CLINICAI_DATA_DIR"
            ] = configured_data_dir

        code = """
import json
from app import config

print(
    json.dumps(
        {
            "data": str(config.DATA_DIR),
            "storage": str(config.STORAGE_DIR),
            "attribution": str(config.GRADCAM_DIR),
            "predictions": str(config.PREDICTIONS_DIR),
            "temporary": str(config.TEMP_DIR),
        },
        sort_keys=True,
    )
)
"""

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                code,
            ],
            cwd=str(
                Path(__file__).resolve().parents[1]
            ),
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )

        return json.loads(
            result.stdout.strip()
        )

    def test_explicit_data_root_uses_new_layout(
        self,
    ) -> None:
        root = Path(
            "/tmp/clinicai-data"
        )

        paths = self.read_paths(
            str(root)
        )

        self.assertEqual(
            paths["data"],
            str(root),
        )
        self.assertEqual(
            paths["storage"],
            str(root),
        )
        self.assertEqual(
            paths["attribution"],
            str(
                root
                / "attribution"
            ),
        )
        self.assertEqual(
            paths["predictions"],
            str(
                root
                / "predictions"
            ),
        )
        self.assertEqual(
            paths["temporary"],
            str(
                root
                / "temporary"
            ),
        )

    def test_missing_environment_keeps_legacy_layout(
        self,
    ) -> None:
        paths = self.read_paths(
            None
        )

        self.assertTrue(
            paths[
                "attribution"
            ].endswith(
                "/storage/gradcam"
            )
        )
        self.assertTrue(
            paths[
                "predictions"
            ].endswith(
                "/storage/predictions"
            )
        )
        self.assertTrue(
            paths[
                "temporary"
            ].endswith(
                "/storage/temp"
            )
        )


if __name__ == "__main__":
    unittest.main()
