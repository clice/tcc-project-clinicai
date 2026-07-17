"""Preditor do Ensemble Stacking do ClinicAI."""

from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import joblib
import numpy as np
import torch

from app.inference.base import BasePredictor


@dataclass(frozen=True)
class DifferentiableEnsembleOutput:
    """Resultado do ensemble mantendo o grafo de gradientes."""

    final_probabilities: torch.Tensor
    decision_logit: torch.Tensor
    meta_features: torch.Tensor
    base_logits: dict[str, torch.Tensor]
    base_probabilities: dict[str, torch.Tensor]


class EnsembleStackingPredictor(BasePredictor):
    """Combina três modelos base com um meta-classificador."""

    def __init__(
        self,
        name: str,
        domain: str,
        base_predictors: list[BasePredictor],
        meta_classifier_path: Path,
    ):
        self.name = name
        self.domain = domain
        self.base_predictors = base_predictors
        self.meta_classifier_path = Path(
            meta_classifier_path
        )
        self._meta_classifier = None
        self._load_lock = Lock()

    def ensure_loaded(self):
        for predictor in self.base_predictors:
            predictor.ensure_loaded()

        if self._meta_classifier is None:
            with self._load_lock:
                if self._meta_classifier is None:
                    if not self.meta_classifier_path.is_file():
                        raise FileNotFoundError(
                            "Meta-classificador não encontrado em: "
                            f"{self.meta_classifier_path}"
                        )

                    self._meta_classifier = joblib.load(
                        self.meta_classifier_path
                    )

                    print(
                        f"[{self.domain}.{self.name}] "
                        "meta-classificador carregado "
                        f"({self.meta_classifier_path})"
                    )

        return self._meta_classifier

    def _ensure_loaded(self):
        return self.ensure_loaded()

    @property
    def is_loaded(self) -> bool:
        return (
            self._meta_classifier is not None
            and all(
                predictor.is_loaded
                for predictor in self.base_predictors
            )
        )

    @property
    def artifact_paths(self) -> tuple[Path, ...]:
        paths: list[Path] = []

        for predictor in self.base_predictors:
            paths.extend(predictor.artifact_paths)

        paths.append(self.meta_classifier_path)

        return tuple(paths)

    def _validated_meta_parameters(
        self,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Valida o contrato binário da regressão logística.

        A ordem esperada é a mesma de ``base_predictors``:
        duas probabilidades por modelo, classes 0 e 1.
        """

        meta_classifier = self.ensure_loaded()

        classes = np.asarray(
            getattr(
                meta_classifier,
                "classes_",
                [],
            )
        )

        if classes.shape != (2,) or not np.array_equal(
            classes,
            np.array([0, 1]),
        ):
            raise RuntimeError(
                "O metaclassificador deve possuir exatamente "
                "as classes binárias [0, 1]."
            )

        expected_features = (
            len(self.base_predictors) * 2
        )

        n_features = getattr(
            meta_classifier,
            "n_features_in_",
            None,
        )

        if n_features != expected_features:
            raise RuntimeError(
                "O metaclassificador possui "
                f"{n_features!r} entradas; eram esperadas "
                f"{expected_features}."
            )

        coefficients = np.asarray(
            getattr(
                meta_classifier,
                "coef_",
                None,
            ),
            dtype=np.float64,
        )

        intercept = np.asarray(
            getattr(
                meta_classifier,
                "intercept_",
                None,
            ),
            dtype=np.float64,
        )

        if coefficients.shape != (
            1,
            expected_features,
        ):
            raise RuntimeError(
                "Formato inválido dos coeficientes do "
                f"metaclassificador: {coefficients.shape}."
            )

        if intercept.shape != (1,):
            raise RuntimeError(
                "Formato inválido do intercepto do "
                f"metaclassificador: {intercept.shape}."
            )

        if (
            not np.isfinite(coefficients).all()
            or not np.isfinite(intercept).all()
        ):
            raise RuntimeError(
                "O metaclassificador contém parâmetros "
                "não finitos."
            )

        return coefficients, intercept

    @staticmethod
    def _extract_logits(output) -> torch.Tensor:
        """Normaliza a saída dos modelos-base para um tensor."""

        logits = (
            output.logits
            if hasattr(output, "logits")
            else output
        )

        if not isinstance(logits, torch.Tensor):
            raise RuntimeError(
                "O modelo-base não retornou um tensor "
                "de logits."
            )

        if logits.ndim != 2 or logits.shape[1] != 2:
            raise RuntimeError(
                "O modelo-base deve retornar logits "
                "no formato [batch, 2]."
            )

        return logits

    def predict_differentiable(
        self,
        image_tensor: torch.Tensor,
    ) -> DifferentiableEnsembleOutput:
        """
        Reproduz o Ensemble Stacking inteiramente em PyTorch.

        Diferentemente de ``predict_proba``, este método não usa
        ``torch.no_grad`` nem converte as saídas intermediárias
        para NumPy. Assim, a saída final mantém o caminho de
        gradientes até os três modelos-base.
        """

        coefficients, intercept = (
            self._validated_meta_parameters()
        )

        base_logits: dict[str, torch.Tensor] = {}
        base_probabilities: dict[
            str,
            torch.Tensor,
        ] = {}

        probability_tensors: list[
            torch.Tensor
        ] = []

        for predictor in self.base_predictors:
            model = predictor.torch_model

            try:
                model_device = next(
                    model.parameters()
                ).device
            except StopIteration:
                model_device = image_tensor.device

            output = model(
                image_tensor.to(model_device)
            )

            logits = self._extract_logits(output)

            probabilities = torch.softmax(
                logits,
                dim=1,
            )

            base_logits[predictor.name] = logits
            base_probabilities[
                predictor.name
            ] = probabilities

            probability_tensors.append(
                probabilities
            )

        meta_features = torch.cat(
            probability_tensors,
            dim=1,
        ).to(dtype=torch.float64)

        coefficients_tensor = torch.as_tensor(
            coefficients,
            dtype=torch.float64,
            device=meta_features.device,
        )

        intercept_tensor = torch.as_tensor(
            intercept,
            dtype=torch.float64,
            device=meta_features.device,
        )

        decision_logit = (
            meta_features
            @ coefficients_tensor.T
            + intercept_tensor
        )

        abnormal_probability = torch.sigmoid(
            decision_logit
        )

        final_probabilities = torch.cat(
            (
                1.0 - abnormal_probability,
                abnormal_probability,
            ),
            dim=1,
        )

        return DifferentiableEnsembleOutput(
            final_probabilities=final_probabilities,
            decision_logit=decision_logit,
            meta_features=meta_features,
            base_logits=base_logits,
            base_probabilities=base_probabilities,
        )

    def calculate_local_evidence_weights(
        self,
        *,
        base_probabilities: dict[
            str,
            torch.Tensor,
        ],
        predicted_class: int,
    ) -> tuple[
        dict[str, float],
        dict[str, float] | None,
    ]:
        """
        Calcula as evidências locais positivas dos modelos-base.

        Retorna as evidências brutas e, quando houver evidência
        positiva, os pesos normalizados. Não cria pesos iguais
        artificialmente quando a soma das evidências é nula.
        """

        if predicted_class not in {0, 1}:
            raise ValueError(
                "A classe prevista deve ser 0 ou 1."
            )

        coefficients, _ = (
            self._validated_meta_parameters()
        )

        coefficient_pairs = coefficients.reshape(
            len(self.base_predictors),
            2,
        )

        branch_deltas = (
            coefficient_pairs[:, 1]
            - coefficient_pairs[:, 0]
        )

        orientation = (
            1.0
            if predicted_class == 1
            else -1.0
        )

        evidence: dict[str, float] = {}

        for predictor, delta in zip(
            self.base_predictors,
            branch_deltas,
            strict=True,
        ):
            probabilities = base_probabilities.get(
                predictor.name
            )

            if probabilities is None:
                raise RuntimeError(
                    "Probabilidades ausentes para "
                    f"{predictor.name}."
                )

            if (
                probabilities.ndim != 2
                or probabilities.shape[0] != 1
                or probabilities.shape[1] != 2
            ):
                raise RuntimeError(
                    "As probabilidades de "
                    f"{predictor.name} devem possuir "
                    "formato [1, 2]."
                )

            abnormal_probability = float(
                probabilities[
                    0,
                    1,
                ]
                .detach()
                .cpu()
            )

            local_value = (
                orientation
                * float(delta)
                * (
                    abnormal_probability
                    - 0.5
                )
            )

            evidence[predictor.name] = max(
                0.0,
                local_value,
            )

        total = sum(evidence.values())

        if total <= 0.0:
            return evidence, None

        weights = {
            name: value / total
            for name, value in evidence.items()
        }

        return evidence, weights

    def predict_proba(
        self,
        image_tensor,
    ) -> np.ndarray:
        """
        Executa o contrato original com o scikit-learn.

        Este caminho é preservado para compatibilidade e para
        validar a equivalência numérica da reprodução PyTorch.
        """

        meta_classifier = self.ensure_loaded()

        probabilities = [
            predictor.predict_proba(
                image_tensor
            )
            for predictor in self.base_predictors
        ]

        meta_features = np.concatenate(
            probabilities
        ).reshape(1, -1)

        return meta_classifier.predict_proba(
            meta_features
        )[0]
