"""
Preditor do Ensemble Stacking: combina as probabilidades de múltiplos
modelos base através de um meta-classificador (Regressão Logística),
exatamente como validado no notebook de treino do ClinicAI.
"""

from pathlib import Path

import joblib
import numpy as np

from app.inference.base import BasePredictor


class EnsembleStackingPredictor(BasePredictor):
    """
    IMPORTANTE — ordem dos modelos base:
    A ordem em que `base_predictors` é passada precisa ser EXATAMENTE a
    mesma ordem usada para treinar o meta-classificador (ver
    `manifesto_inferencia.json`, gerado pelo notebook de treino, campo
    `ordem_dos_modelos`). Trocar a ordem aqui produz predições erradas
    sem nenhum erro visível — o meta-classificador simplesmente aprende a
    associar cada posição do vetor a um modelo específico.
    """

    name = "ensemble_stacking"

    def __init__(self, base_predictors: list[BasePredictor], meta_classifier_path: Path):
        self.base_predictors = base_predictors
        self.meta_classifier_path = Path(meta_classifier_path)
        self._meta_classifier = None

    def _ensure_loaded(self):
        if self._meta_classifier is None:
            if not self.meta_classifier_path.exists():
                raise FileNotFoundError(
                    f"Meta-classificador não encontrado em: {self.meta_classifier_path}"
                )
            self._meta_classifier = joblib.load(self.meta_classifier_path)
            print(f"[{self.name}] meta-classificador carregado ({self.meta_classifier_path})")
        return self._meta_classifier

    def predict_proba(self, image_tensor) -> np.ndarray:
        meta_classifier = self._ensure_loaded()

        # Uma predição por modelo base, na ordem em que foram registrados.
        probabilidades_por_modelo = [
            predictor.predict_proba(image_tensor) for predictor in self.base_predictors
        ]

        # Concatena em um único vetor de meta-atributos (6 valores, no
        # caso de 3 modelos binários) — mesma lógica do notebook de treino.
        meta_features = np.concatenate(probabilidades_por_modelo).reshape(1, -1)

        return meta_classifier.predict_proba(meta_features)[0]
    