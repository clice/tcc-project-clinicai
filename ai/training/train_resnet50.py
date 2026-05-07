"""
Treinamento da ResNet-50 para o ClinicAI.
"""

from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import Adam
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

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = (
    BASE_DIR
    / "datasets"
    / "gastrointestinal"
)

MODEL_OUTPUT_PATH = (
    BASE_DIR
    / "models"
    / "exported"
    / "model.pt"
)

BATCH_SIZE = 8

NUM_EPOCHS = 5

LEARNING_RATE = 0.0001


def create_dataloaders():
    """
    Cria DataLoaders de treino e validação.
    """

    (
        train_paths,
        val_paths,
        train_labels,
        val_labels,
    ) = build_train_validation_split(
        DATASET_DIR
    )

    train_dataset = GastroDataset(
        train_paths,
        train_labels,
    )

    val_dataset = GastroDataset(
        val_paths,
        val_labels,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    return train_loader, val_loader


def create_model():
    """
    Cria ResNet50 binária.
    """

    model = models.resnet50(
        weights="IMAGENET1K_V1"
    )

    in_features = model.fc.in_features

    model.fc = nn.Linear(
        in_features,
        2,
    )

    return model


def train():
    """
    Executa treinamento do modelo.
    """

    train_loader, val_loader = create_dataloaders()

    model = create_model()

    model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()

    optimizer = Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    print("Starting training...")

    for epoch in range(NUM_EPOCHS):

        model.train()

        running_loss = 0.0

        for images, labels in train_loader:

            images = images.to(DEVICE)

            labels = labels.to(DEVICE)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(
                outputs,
                labels,
            )

            loss.backward()

            optimizer.step()

            running_loss += loss.item()

        epoch_loss = (
            running_loss
            / len(train_loader)
        )

        print(
            f"Epoch {epoch + 1}/{NUM_EPOCHS}"
        )

        print(
            f"Loss: {epoch_loss:.4f}"
        )

    MODEL_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    torch.save(
        model.state_dict(),
        MODEL_OUTPUT_PATH,
    )

    print(
        f"Model saved at: {MODEL_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    train()
