"""
Treinamento da ResNet50 para o ClinicAI.
"""

import random
import time
from pathlib import Path

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
EARLY_STOPPING_PATIENCE = 4

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets" / "gastrointestinal"

CHECKPOINT_DIR = BASE_DIR / "models" / "checkpoints"

BEST_MODEL_PATH = CHECKPOINT_DIR / "best_model.pt"

FINAL_MODEL_PATH = BASE_DIR / "models" / "exported" / "model.pt"

REPORTS_DIR = BASE_DIR / "reports"

METRICS_DIR = REPORTS_DIR / "metrics"

FIGURES_DIR = REPORTS_DIR / "figures"

CSV_HISTORY_PATH = METRICS_DIR / "training_history.csv"

TRAINING_CURVE_PATH = FIGURES_DIR / "training_curves.png"

# =========================================================
# SEED
# =========================================================

torch.manual_seed(SEED)
random.seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# =========================================================
# DATASET
# =========================================================


def create_dataloaders():
    """
    Cria DataLoaders de treino e validação.
    """

    (
        train_paths,
        val_paths,
        train_labels,
        val_labels,
    ) = build_train_validation_split(DATASET_DIR)

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
        num_workers=2,
        pin_memory=torch.cuda.is_available(),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=2,
        pin_memory=torch.cuda.is_available(),
    )

    return train_loader, val_loader


# =========================================================
# MODELO
# =========================================================


def create_model():
    """
    Cria ResNet50 binária usando transfer learning.
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


# =========================================================
# TREINO
# =========================================================


def get_gpu_memory_info():
    """
    Retorna uso de memória da GPU em GB.
    """

    if not torch.cuda.is_available():
        return 0.0, 0.0

    allocated = torch.cuda.memory_allocated() / 1024**3
    reserved = torch.cuda.memory_reserved() / 1024**3

    return allocated, reserved


def train():
    """
    Executa treinamento do modelo.
    """

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

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
    epochs_without_improvement = 0
    history = []

    print(f"\nTraining on: {DEVICE}")

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)

        total_memory = (
            torch.cuda.get_device_properties(0).total_memory
            / 1024**3
        )

        print(f"GPU: {gpu_name}")
        print(f"VRAM total: {total_memory:.2f} GB")

    training_start_time = time.time()

    for epoch in range(NUM_EPOCHS):
        epoch_start_time = time.time()

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

        # =========================
        # TRAIN
        # =========================

        model.train()
        train_loss = 0.0

        for images, labels in train_loader:
            images = images.to(
                DEVICE,
                non_blocking=True,
            )

            labels = labels.to(
                DEVICE,
                non_blocking=True,
            )

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
                images = images.to(
                    DEVICE,
                    non_blocking=True,
                )

                labels = labels.to(
                    DEVICE,
                    non_blocking=True,
                )

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

        epoch_time = time.time() - epoch_start_time
        current_lr = optimizer.param_groups[0]["lr"]

        gpu_memory_allocated, gpu_memory_reserved = get_gpu_memory_info()

        gpu_peak_memory = 0.0

        if torch.cuda.is_available():
            gpu_peak_memory = (
                torch.cuda.max_memory_allocated()
                / 1024**3
            )

        # =========================
        # LOG
        # =========================

        print(f"\nEpoch {epoch + 1}/{NUM_EPOCHS}")
        print(f"Train Loss: {train_loss:.4f}")
        print(f"Val Loss: {val_loss:.4f}")
        print(f"Val Accuracy: {val_accuracy:.4f}")
        print(f"Epoch Time: {epoch_time:.2f}s")
        print(f"Learning Rate: {current_lr:.8f}")

        if torch.cuda.is_available():
            print(
                f"GPU Memory Allocated: {gpu_memory_allocated:.2f} GB"
            )
            print(
                f"GPU Memory Reserved : {gpu_memory_reserved:.2f} GB"
            )
            print(
                f"GPU Peak Memory     : {gpu_peak_memory:.2f} GB"
            )

        history.append(
            {
                "epoch": epoch + 1,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_accuracy": val_accuracy,
                "epoch_time_seconds": round(epoch_time, 2),
                "learning_rate": current_lr,
                "gpu_memory_allocated_gb": round(
                    gpu_memory_allocated,
                    2,
                ),
                "gpu_memory_reserved_gb": round(
                    gpu_memory_reserved,
                    2,
                ),
                "gpu_peak_memory_gb": round(
                    gpu_peak_memory,
                    2,
                ),
            }
        )

        # =========================
        # BEST MODEL
        # =========================

        if val_loss < best_val_loss:
            
            best_val_loss = val_loss

            epochs_without_improvement = 0

            torch.save(
                model.state_dict(),
                BEST_MODEL_PATH,
            )

            print("Best model updated.")

        else:

            epochs_without_improvement += 1

            print(
                f"No improvement for "
                f"{epochs_without_improvement} epoch(s)."
            )
            
        # =========================
        # EARLY STOPPING
        # =========================

        if (
            epochs_without_improvement
            >= EARLY_STOPPING_PATIENCE
        ):

            print(
                "\nEarly stopping triggered."
            )

            break

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

    # =====================================================
    # TOTAL TIME
    # =====================================================

    total_training_time = time.time() - training_start_time

    print(
        f"\nTotal training time: {total_training_time:.2f}s"
    )

    print(
        f"Total training time: {total_training_time / 60:.2f}min"
    )


if __name__ == "__main__":
    train()
    