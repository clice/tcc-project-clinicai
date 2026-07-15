"""Preditor do Ensemble Stacking do ClinicAI."""

from pathlib import Path
from threading import Lock

import joblib
import numpy as np

from app.inference.base import BasePredictor


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
        self.meta_classifier_path = Path(meta_classifier_path)
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
                            f"Meta-classificador não encontrado em: {self.meta_classifier_path}"
                        )
                    self._meta_classifier = joblib.load(self.meta_classifier_path)
                    print(
                        f"[{self.domain}.{self.name}] meta-classificador carregado "
                        f"({self.meta_classifier_path})"
                    )
        return self._meta_classifier

    def _ensure_loaded(self):
        return self.ensure_loaded()

    @property
    def is_loaded(self) -> bool:
        return self._meta_classifier is not None and all(
            predictor.is_loaded for predictor in self.base_predictors
        )

    @property
    def artifact_paths(self) -> tuple[Path, ...]:
        paths: list[Path] = []
        for predictor in self.base_predictors:
            paths.extend(predictor.artifact_paths)
        paths.append(self.meta_classifier_path)
        return tuple(paths)

    def predict_proba(self, image_tensor) -> np.ndarray:
        meta_classifier = self.ensure_loaded()
        probabilities = [
            predictor.predict_proba(image_tensor) for predictor in self.base_predictors
        ]
        meta_features = np.concatenate(probabilities).reshape(1, -1)
        return meta_classifier.predict_proba(meta_features)[0]
