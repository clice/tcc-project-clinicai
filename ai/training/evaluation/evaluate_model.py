"""
Avaliação do modelo treinado.
"""

from pathlib import Path

import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader
from torchvision import models

from training.datasets.build_dataset import (
    build_train_validation_split,
)
from training.datasets.gastro_dataset import (
    GastroDataset,
)


DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATASET_DIR = (
    BASE_DIR
    / "datasets"
    / "gastrointestinal"
)

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "exported"
    / "model.pt"
)

BATCH_SIZE = 8


def create_model():
    """
    Cria arquitetura da ResNet50.
    """

    model = models.resnet50(weights=None)

    in_features = model.fc.in_features

    model.fc = nn.Linear(
        in_features,
        2,
    )

    return model


def create_validation_loader():
    """
    Cria DataLoader de validação.
    """

    (
        _train_paths,
        val_paths,
        _train_labels,
        val_labels,
    ) = build_train_validation_split(
        DATASET_DIR
    )

    val_dataset = GastroDataset(
        val_paths,
        val_labels,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    return val_loader


def evaluate():
    """
    Executa avaliação do modelo.
    """

    model = create_model()

    model.load_state_dict(
        torch.load(
            MODEL_PATH,
            map_location=DEVICE,
            weights_only=True,
        )
    )

    model.to(DEVICE)

    model.eval()

    val_loader = create_validation_loader()

    all_predictions = []

    all_labels = []

    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(DEVICE)

            outputs = model(images)

            probabilities = torch.softmax(
                outputs,
                dim=1,
            )

            predictions = torch.argmax(
                probabilities,
                dim=1,
            )

            all_predictions.extend(
                predictions.cpu().numpy()
            )

            all_labels.extend(
                labels.numpy()
            )

    accuracy = accuracy_score(
        all_labels,
        all_predictions,
    )

    precision = precision_score(
        all_labels,
        all_predictions,
    )

    recall = recall_score(
        all_labels,
        all_predictions,
    )

    f1 = f1_score(
        all_labels,
        all_predictions,
    )

    matrix = confusion_matrix(
        all_labels,
        all_predictions,
    )

    report = classification_report(
        all_labels,
        all_predictions,
        target_names=[
            "normal",
            "abnormal",
        ],
    )

    print("\n=== Evaluation Metrics ===\n")

    print(f"Accuracy : {accuracy:.4f}")

    print(f"Precision: {precision:.4f}")

    print(f"Recall   : {recall:.4f}")

    print(f"F1-score : {f1:.4f}")

    print("\n=== Confusion Matrix ===\n")

    print(matrix)

    print("\n=== Classification Report ===\n")

    print(report)


if __name__ == "__main__":
    evaluate()
