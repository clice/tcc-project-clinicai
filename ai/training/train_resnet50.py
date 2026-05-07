"""
Treinamento da ResNet50 para o ClinicAI.
"""

from pathlib import Path
import random

import matplotlib.pyplot as plt
import pandas as pd
import torch
import torch.nn as nn

from sklearn.metrics import accuracy_score

from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from torchvision import models

from training.datasets.build_dataset import (
    build_train_validation_split,
)

from training.datasets.gastro_dataset import (
    GastroDataset,
)

# =========================================================
# CONFIGURAÇÕES
# =========================================================

SEED = 42

BATCH_SIZE = 8

NUM_EPOCHS = 10

LEARNING_RATE = 0.0001

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = (
    BASE_DIR
    / "datasets"
    / "gastrointestinal"
)

CHECKPOINT_DIR = (
    BASE_DIR
    / "models"
    / "checkpoints"
)

BEST_MODEL_PATH = (
    CHECKPOINT_DIR
    / "best_model.pt"
)

FINAL_MODEL_PATH = (
    BASE_DIR
    / "models"
    / "exported"
    / "model.pt"
)

REPORTS_DIR = (
    BASE_DIR
    / "reports"
)

METRICS_DIR = (
    REPORTS_DIR
    / "metrics"
)

FIGURES_DIR = (
    REPORTS_DIR
    / "figures"
)

CSV_HISTORY_PATH = (
    METRICS_DIR
    / "training_history.csv"
)

TRAINING_CURVE_PATH = (
    FIGURES_DIR
    / "training_curves.png"
)

# =========================================================
# SEED
# =========================================================

torch.manual_seed(SEED)

random.seed(SEED)

# =========================================================
# DATASET
# =========================================================


def create_dataloaders():

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
        train=True,
    )

    val_dataset = GastroDataset(
        val_paths,
        val_labels,
        train=False,
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


# =========================================================
# MODELO
# =========================================================


def create_model():

    model = models.resnet50(
        weights="IMAGENET1K_V1"
    )

    in_features = model.fc.in_features

    model.fc = nn.Linear(
        in_features,
        2,
    )

    return model


# =========================================================
# TREINO
# =========================================================


def train():

    METRICS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CHECKPOINT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    train_loader, val_loader = create_dataloaders()

    model = create_model()

    model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()

    optimizer = Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="min",
        patience=2,
        factor=0.5,
    )

    best_val_loss = float("inf")

    history = []

    print(f"\nTraining on: {DEVICE}")

    for epoch in range(NUM_EPOCHS):

        # =========================
        # TRAIN
        # =========================

        model.train()

        train_loss = 0.0

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

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # =========================
        # VALIDATION
        # =========================

        model.eval()

        val_loss = 0.0

        predictions = []

        targets = []

        with torch.no_grad():

            for images, labels in val_loader:

                images = images.to(DEVICE)

                labels = labels.to(DEVICE)

                outputs = model(images)

                loss = criterion(
                    outputs,
                    labels,
                )

                val_loss += loss.item()

                preds = torch.argmax(
                    outputs,
                    dim=1,
                )

                predictions.extend(
                    preds.cpu().numpy()
                )

                targets.extend(
                    labels.cpu().numpy()
                )

        val_loss /= len(val_loader)

        val_accuracy = accuracy_score(
            targets,
            predictions,
        )

        scheduler.step(val_loss)

        print(
            f"\nEpoch {epoch + 1}/{NUM_EPOCHS}"
        )

        print(
            f"Train Loss: {train_loss:.4f}"
        )

        print(
            f"Val Loss: {val_loss:.4f}"
        )

        print(
            f"Val Accuracy: {val_accuracy:.4f}"
        )

        history.append(
            {
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_accuracy": val_accuracy,
            }
        )

        # =========================
        # BEST MODEL
        # =========================

        if val_loss < best_val_loss:

            best_val_loss = val_loss

            torch.save(
                model.state_dict(),
                BEST_MODEL_PATH,
            )

            print(
                "Best model updated."
            )

    # =====================================================
    # EXPORT FINAL
    # =====================================================

    model.load_state_dict(
        torch.load(
            BEST_MODEL_PATH,
            map_location=DEVICE,
            weights_only=True,
        )
    )

    torch.save(
        model.state_dict(),
        FINAL_MODEL_PATH,
    )

    print(
        f"\nFinal model exported to:\n{FINAL_MODEL_PATH}"
    )

    # =====================================================
    # SAVE HISTORY CSV
    # =====================================================

    history_df = pd.DataFrame(history)

    history_df.to_csv(
        CSV_HISTORY_PATH,
        index=False,
    )

    print(
        f"\nTraining history saved at:\n{CSV_HISTORY_PATH}"
    )

    # =====================================================
    # PLOT CURVES
    # =====================================================

    plt.figure(figsize=(10, 5))

    plt.plot(
        history_df["epoch"],
        history_df["train_loss"],
        label="Train Loss",
    )

    plt.plot(
        history_df["epoch"],
        history_df["val_loss"],
        label="Validation Loss",
    )

    plt.xlabel("Epoch")

    plt.ylabel("Loss")

    plt.title("Training Curves")

    plt.legend()

    plt.tight_layout()

    plt.savefig(TRAINING_CURVE_PATH)

    plt.close()

    print(
        f"\nTraining curves saved at:\n{TRAINING_CURVE_PATH}"
    )


if __name__ == "__main__":
    train()