"""Testes do mapa composto orientado pelo ensemble."""

import unittest

import numpy as np
import torch

from app.explainability.gradcam import (
    MODEL_ORDER,
    calculate_normalized_branch_cam,
    combine_branch_cams,
)


class EnsembleGradcamTests(
    unittest.TestCase
):
    def test_branch_cam_is_resized_and_normalized(
        self,
    ):
        activation = torch.tensor(
            [
                [
                    [
                        [1.0, 2.0],
                        [3.0, 4.0],
                    ],
                    [
                        [4.0, 3.0],
                        [2.0, 1.0],
                    ],
                ]
            ],
            dtype=torch.float32,
        )

        gradient = torch.tensor(
            [
                [
                    [
                        [1.0, 1.0],
                        [1.0, 1.0],
                    ],
                    [
                        [0.5, 0.5],
                        [0.5, 0.5],
                    ],
                ]
            ],
            dtype=torch.float32,
        )

        cam, raw_maximum = (
            calculate_normalized_branch_cam(
                activation,
                gradient,
                output_size=(4, 4),
            )
        )

        self.assertEqual(
            cam.shape,
            (4, 4),
        )

        self.assertGreater(
            raw_maximum,
            0.0,
        )

        self.assertGreaterEqual(
            float(cam.min()),
            0.0,
        )

        self.assertAlmostEqual(
            float(cam.max()),
            1.0,
            places=6,
        )

    def test_branch_cam_returns_zero_for_zero_signal(
        self,
    ):
        activation = torch.ones(
            (1, 2, 2, 2),
            dtype=torch.float32,
        )

        gradient = torch.zeros_like(
            activation
        )

        cam, raw_maximum = (
            calculate_normalized_branch_cam(
                activation,
                gradient,
                output_size=(4, 4),
            )
        )

        self.assertEqual(
            raw_maximum,
            0.0,
        )

        self.assertTrue(
            np.array_equal(
                cam,
                np.zeros(
                    (4, 4),
                    dtype=np.float32,
                ),
            )
        )

    def test_combination_uses_local_weights(
        self,
    ):
        branch_cams = {
            "resnet50": np.array(
                [
                    [1.0, 0.0],
                    [0.0, 0.0],
                ],
                dtype=np.float32,
            ),
            "efficientnet_b4": np.array(
                [
                    [0.0, 1.0],
                    [0.0, 0.0],
                ],
                dtype=np.float32,
            ),
            "pvt_v2_b2": np.array(
                [
                    [0.0, 0.0],
                    [1.0, 0.0],
                ],
                dtype=np.float32,
            ),
        }

        weights = {
            "resnet50": 0.5,
            "efficientnet_b4": 0.3,
            "pvt_v2_b2": 0.2,
        }

        combined = combine_branch_cams(
            branch_cams,
            weights,
        )

        self.assertIsNotNone(
            combined
        )

        self.assertAlmostEqual(
            float(combined.max()),
            1.0,
            places=6,
        )

        self.assertAlmostEqual(
            float(combined[0, 1]),
            0.6,
            places=6,
        )

        self.assertAlmostEqual(
            float(combined[1, 0]),
            0.4,
            places=6,
        )

    def test_zero_combination_is_unavailable(
        self,
    ):
        branch_cams = {
            model_name: np.zeros(
                (2, 2),
                dtype=np.float32,
            )
            for model_name in MODEL_ORDER
        }

        weights = {
            "resnet50": 0.4,
            "efficientnet_b4": 0.3,
            "pvt_v2_b2": 0.3,
        }

        self.assertIsNone(
            combine_branch_cams(
                branch_cams,
                weights,
            )
        )


if __name__ == "__main__":
    unittest.main()
