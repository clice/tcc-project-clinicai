"""CHK-12 — contrato multi-domínio, readiness e carregamento dos artefatos."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import torch
from fastapi import HTTPException, UploadFile

from app.inference.ensemble_stacking import EnsembleStackingPredictor
from app.inference.model_loader import select_device
from app.inference.preprocess import InvalidImageError, preprocess_image
from app.inference.registry import UnsupportedExamTypeError, resolve_exam_domain
from app.inference.timm_predictor import TimmCNNPredictor


class DummyTorchModel:
    def load_state_dict(self, _state_dict):
        return None

    def to(self, _device):
        return self

    def eval(self):
        return self


class DummyMetaClassifier:
    def predict_proba(self, _features):
        return np.array([[0.25, 0.75]])


class ServiceContractTests(unittest.TestCase):
    def test_exam_type_is_explicit_and_resolves_gastrointestinal(self):
        self.assertEqual(resolve_exam_domain("endoscopy"), "gastrointestinal")
        self.assertEqual(resolve_exam_domain(" COLONOSCOPY "), "gastrointestinal")
        with self.assertRaises(UnsupportedExamTypeError):
            resolve_exam_domain(None)
        with self.assertRaises(UnsupportedExamTypeError):
            resolve_exam_domain("mammography")

    def test_device_selection_supports_cpu_and_gpu(self):
        self.assertEqual(select_device(cuda_available=False), torch.device("cpu"))
        self.assertEqual(select_device(cuda_available=True), torch.device("cuda"))

    def test_ensemble_loads_three_weights_and_meta_classifier(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            weight_paths = [root / name for name in ("a.pt", "b.pt", "c.pt")]
            meta_path = root / "meta.joblib"
            for path in (*weight_paths, meta_path):
                path.write_bytes(b"artifact")

            predictors = [
                TimmCNNPredictor(
                    name=f"model_{index}",
                    domain="gastrointestinal",
                    timm_model_name="resnet50",
                    weights_path=path,
                )
                for index, path in enumerate(weight_paths)
            ]
            ensemble = EnsembleStackingPredictor(
                name="ensemble_stacking",
                domain="gastrointestinal",
                base_predictors=predictors,
                meta_classifier_path=meta_path,
            )

            with patch(
                "app.inference.timm_predictor.timm.create_model",
                side_effect=lambda *args, **kwargs: DummyTorchModel(),
            ) as create_model, patch(
                "app.inference.timm_predictor.load_torch_state_dict",
                return_value={},
            ) as load_state, patch(
                "app.inference.ensemble_stacking.joblib.load",
                return_value=DummyMetaClassifier(),
            ) as load_meta:
                ensemble.ensure_loaded()

            self.assertTrue(ensemble.is_loaded)
            self.assertEqual(len(ensemble.artifact_paths), 4)
            self.assertEqual(create_model.call_count, 3)
            self.assertEqual(load_state.call_count, 3)
            load_meta.assert_called_once_with(meta_path)

    def test_runtime_requires_manifest_and_exactly_four_artifacts(self):
        from app.inference import runtime

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = tuple(root / name for name in ("a.pt", "b.pt", "c.pt", "meta.joblib"))
            for path in artifacts:
                path.write_bytes(b"artifact")
            manifest = root / "manifesto_modelos.json"
            manifest.write_text(
                json.dumps(
                    {
                        "domain": "gastrointestinal",
                        "model_version": "models-v1",
                        "artifacts": [{"name": path.name} for path in artifacts],
                    }
                ),
                encoding="utf-8",
            )
            fake_predictor = SimpleNamespace(
                name="ensemble_stacking",
                domain="gastrointestinal",
                is_loaded=False,
                artifact_paths=artifacts,
            )

            def ensure_loaded():
                fake_predictor.is_loaded = True

            fake_predictor.ensure_loaded = ensure_loaded
            runtime._RUNTIME_STATE.update(
                initialized=False,
                ready=False,
                error=None,
                loaded_at=None,
                model_versions={},
            )

            with patch.dict(
                runtime.ACTIVE_MODEL_BY_DOMAIN,
                {"gastrointestinal": "ensemble_stacking"},
                clear=True,
            ), patch.dict(
                runtime.CLASS_LABELS_BY_DOMAIN,
                {"gastrointestinal": {0: "normal", 1: "abnormal"}},
                clear=True,
            ), patch.dict(
                runtime.MODEL_ARTIFACTS_BY_DOMAIN,
                {"gastrointestinal": artifacts},
                clear=True,
            ), patch.dict(
                runtime.MODEL_MANIFEST_BY_DOMAIN,
                {"gastrointestinal": manifest},
                clear=True,
            ), patch(
                "app.inference.runtime.get_predictor",
                return_value=fake_predictor,
            ), patch(
                "app.inference.runtime.describe_device",
                return_value={"type": "cpu", "value": "cpu", "cuda_available": False},
            ):
                snapshot = runtime.initialize_runtime(force=True)

            self.assertTrue(snapshot["ready"])
            self.assertEqual(snapshot["artifact_summary"], {"expected": 4, "loaded": 4})
            self.assertEqual(snapshot["domains"]["gastrointestinal"]["model_version"], "models-v1")

    def test_invalid_image_is_rejected(self):
        with self.assertRaises(InvalidImageError):
            preprocess_image(b"not-an-image")

    def test_prediction_uses_domain_classes_and_manifest_version(self):
        from app.inference import predictor as predictor_module

        fake_predictor = SimpleNamespace(
            name="ensemble_stacking",
            domain="gastrointestinal",
            predict_proba=Mock(return_value=np.array([0.1, 0.9])),
        )
        with patch.object(
            predictor_module,
            "resolve_active_predictor",
            return_value=fake_predictor,
        ), patch.object(
            predictor_module,
            "preprocess_image",
            return_value=object(),
        ), patch.object(
            predictor_module,
            "generate_gradcam_from_bytes",
            return_value="/app/storage/gradcam/result.jpg",
        ) as gradcam, patch.object(
            predictor_module,
            "model_version_for_domain",
            return_value="models-v1.2.3",
        ):
            result = predictor_module.predict_image(b"image", "colonoscopy")

        self.assertEqual(result["exam_type"], "colonoscopy")
        self.assertEqual(result["exam_domain"], "gastrointestinal")
        self.assertEqual(result["prediction_class"], 1)
        self.assertEqual(result["label"], "abnormal")
        self.assertEqual(result["model_name"], "ensemble_stacking")
        self.assertEqual(result["model_version"], "models-v1.2.3")
        self.assertEqual(result["confidence"], 0.9)
        self.assertTrue(result["gradcam_available"])
        gradcam.assert_called_once_with(b"image", domain="gastrointestinal")

    def test_health_and_models_endpoints_expose_runtime_contract(self):
        from app import main as main_module

        health_payload = {
            "status": "ok",
            "service": "clinicai-ai",
            "ready": True,
            "initialized": True,
            "error": None,
            "loaded_at": "2026-07-15T00:00:00+00:00",
            "device": {"type": "cpu", "value": "cpu", "cuda_available": False},
            "artifact_summary": {"expected": 4, "loaded": 4},
            "domains": {},
        }
        model_payload = {
            "ready": True,
            "device": health_payload["device"],
            "domains": {
                "gastrointestinal": {
                    "active_model": "ensemble_stacking",
                    "classes": {0: "normal", 1: "abnormal"},
                }
            },
        }
        with patch.object(main_module, "runtime_snapshot", return_value=health_payload):
            response = main_module.health_check()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.body)["artifact_summary"]["loaded"], 4)

        with patch.object(main_module, "model_catalog", return_value=model_payload):
            self.assertEqual(
                main_module.list_models()["domains"]["gastrointestinal"]["active_model"],
                "ensemble_stacking",
            )

    def test_predict_endpoint_returns_422_for_invalid_image(self):
        from app import main as main_module

        upload = UploadFile(file=BytesIO(b"invalid"), filename="invalid.png")
        with patch.object(main_module, "is_runtime_ready", return_value=True):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(main_module.predict_exam_image(upload, "endoscopy"))
        self.assertEqual(error.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
