"""Testes da reprodução diferenciável do Ensemble Stacking."""

import unittest
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression

from app.inference.ensemble_stacking import (
    EnsembleStackingPredictor,
)


class TinyBinaryModel(torch.nn.Module):
    """Modelo mínimo determinístico para testar gradientes."""

    def __init__(
        self,
        first_scale: float,
        second_scale: float,
    ):
        super().__init__()

        self.linear = torch.nn.Linear(
            4,
            2,
        )

        with torch.no_grad():
            self.linear.weight.copy_(
                torch.tensor(
                    [
                        [
                            first_scale,
                            -0.2,
                            0.3,
                            -0.1,
                        ],
                        [
                            -0.4,
                            second_scale,
                            -0.2,
                            0.5,
                        ],
                    ],
                    dtype=torch.float32,
                )
            )

            self.linear.bias.copy_(
                torch.tensor(
                    [0.1, -0.2],
                    dtype=torch.float32,
                )
            )

    def forward(
        self,
        image_tensor: torch.Tensor,
    ) -> torch.Tensor:
        flattened = image_tensor.reshape(
            image_tensor.shape[0],
            -1,
        )

        return self.linear(flattened)


class DummyBasePredictor:
    """Adaptador mínimo compatível com o ensemble."""

    def __init__(
        self,
        name: str,
        model: torch.nn.Module,
    ):
        self.name = name
        self._model = model

    def ensure_loaded(self):
        return self._model

    @property
    def torch_model(self):
        return self._model

    @property
    def is_loaded(self):
        return True

    @property
    def artifact_paths(self):
        return ()

    def predict_proba(
        self,
        image_tensor,
    ) -> np.ndarray:
        with torch.no_grad():
            logits = self._model(
                image_tensor
            )

            probabilities = torch.softmax(
                logits,
                dim=1,
            )

        return (
            probabilities
            .cpu()
            .numpy()[0]
        )


def build_meta_classifier():
    """Monta uma regressão logística binária ajustada."""

    classifier = LogisticRegression()

    classifier.classes_ = np.array(
        [0, 1],
        dtype=np.int64,
    )

    classifier.n_features_in_ = 6

    classifier.coef_ = np.array(
        [
            [
                -1.4,
                1.3,
                -1.2,
                1.1,
                -0.9,
                0.8,
            ]
        ],
        dtype=np.float64,
    )

    classifier.intercept_ = np.array(
        [0.25],
        dtype=np.float64,
    )

    classifier.n_iter_ = np.array(
        [1],
        dtype=np.int32,
    )

    return classifier


def build_ensemble():
    predictors = [
        DummyBasePredictor(
            "resnet50",
            TinyBinaryModel(
                0.7,
                0.9,
            ),
        ),
        DummyBasePredictor(
            "efficientnet_b4",
            TinyBinaryModel(
                1.1,
                0.6,
            ),
        ),
        DummyBasePredictor(
            "pvt_v2_b2",
            TinyBinaryModel(
                0.5,
                1.2,
            ),
        ),
    ]

    ensemble = EnsembleStackingPredictor(
        name="ensemble_stacking",
        domain="gastrointestinal",
        base_predictors=predictors,
        meta_classifier_path=Path(
            "/tmp/meta-classifier-unused.joblib"
        ),
    )

    ensemble._meta_classifier = (
        build_meta_classifier()
    )

    return ensemble, predictors


def build_image_tensor():
    return torch.tensor(
        [
            [
                [
                    [0.2, 0.8],
                    [0.4, 0.6],
                ]
            ]
        ],
        dtype=torch.float32,
    )


class EnsembleDifferentiableTests(
    unittest.TestCase
):
    def test_differentiable_output_matches_sklearn(
        self,
    ):
        ensemble, _ = build_ensemble()
        image_tensor = build_image_tensor()

        original_probabilities = (
            ensemble.predict_proba(
                image_tensor
            )
        )

        differentiable = (
            ensemble.predict_differentiable(
                image_tensor
            )
        )

        reproduced_probabilities = (
            differentiable
            .final_probabilities
            .detach()
            .cpu()
            .numpy()[0]
        )

        np.testing.assert_allclose(
            reproduced_probabilities,
            original_probabilities,
            rtol=0.0,
            atol=1e-12,
        )

        self.assertEqual(
            differentiable.meta_features.shape,
            (1, 6),
        )

        self.assertEqual(
            set(differentiable.base_logits),
            {
                "resnet50",
                "efficientnet_b4",
                "pvt_v2_b2",
            },
        )

    def test_final_logit_reaches_all_base_models(
        self,
    ):
        ensemble, predictors = build_ensemble()
        image_tensor = build_image_tensor()

        differentiable = (
            ensemble.predict_differentiable(
                image_tensor
            )
        )

        differentiable.decision_logit.sum().backward()

        for predictor in predictors:
            gradients = [
                parameter.grad
                for parameter
                in predictor.torch_model.parameters()
            ]

            self.assertTrue(
                all(
                    gradient is not None
                    for gradient in gradients
                )
            )

            self.assertTrue(
                any(
                    float(
                        gradient
                        .abs()
                        .max()
                        .detach()
                        .cpu()
                    )
                    > 0.0
                    for gradient in gradients
                )
            )

    def test_local_evidence_weights_are_normalized(
        self,
    ):
        ensemble, _ = build_ensemble()
        image_tensor = build_image_tensor()

        differentiable = (
            ensemble.predict_differentiable(
                image_tensor
            )
        )

        predicted_class = int(
            torch.argmax(
                differentiable.final_probabilities,
                dim=1,
            )[0]
        )

        evidence, weights = (
            ensemble.calculate_local_evidence_weights(
                base_probabilities=(
                    differentiable
                    .base_probabilities
                ),
                predicted_class=predicted_class,
            )
        )

        expected_models = {
            "resnet50",
            "efficientnet_b4",
            "pvt_v2_b2",
        }

        self.assertEqual(
            set(evidence),
            expected_models,
        )

        self.assertIsNotNone(weights)

        self.assertEqual(
            set(weights),
            expected_models,
        )

        self.assertAlmostEqual(
            sum(weights.values()),
            1.0,
            places=12,
        )

        self.assertTrue(
            all(
                value >= 0.0
                for value in evidence.values()
            )
        )


if __name__ == "__main__":
    unittest.main()
