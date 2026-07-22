"""Ausência de armazenamento operacional permanente no serviço de IA."""

import unittest

from app import config
from app.schemas import PredictionResponse


class NoPersistentStorageTests(
    unittest.TestCase
):
    def test_configuration_has_no_operational_storage_paths(
        self,
    ) -> None:
        removed_attributes = (
            "DATA_DIR",
            "STORAGE_DIR",
            "GRADCAM_DIR",
            "PREDICTIONS_DIR",
            "TEMP_DIR",
            "AI_STORAGE_DIR",
            "LEGACY_STORAGE_DIR",
        )

        for attribute in removed_attributes:
            with self.subTest(
                attribute=attribute
            ):
                self.assertFalse(
                    hasattr(
                        config,
                        attribute,
                    ),
                    (
                        "A configuração da IA não deve "
                        "declarar armazenamento operacional: "
                        f"{attribute}"
                    ),
                )

    def test_public_contract_transfers_attribution_content(
        self,
    ) -> None:
        fields = set(
            PredictionResponse.model_fields
        )

        expected_gradcam_fields = {
            "gradcam_available",
            "gradcam_base64",
            "gradcam_mime_type",
            "gradcam_sha256",
        }

        actual_gradcam_fields = {
            field
            for field in fields
            if field.startswith(
                "gradcam"
            )
        }

        self.assertEqual(
            actual_gradcam_fields,
            expected_gradcam_fields,
        )

        self.assertNotIn(
            "gradcam_path",
            fields,
        )

    def test_model_artifacts_remain_configured(
        self,
    ) -> None:
        artifacts = (
            config
            .MODEL_ARTIFACTS_BY_DOMAIN[
                "gastrointestinal"
            ]
        )

        self.assertEqual(
            len(artifacts),
            4,
        )

        self.assertEqual(
            config.ACTIVE_MODEL_BY_DOMAIN[
                "gastrointestinal"
            ],
            "ensemble_stacking",
        )


if __name__ == "__main__":
    unittest.main()
