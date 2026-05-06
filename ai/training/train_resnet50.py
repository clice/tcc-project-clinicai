"""
Treinamento inicial da ResNet-50 para o ClinicAI.
"""

from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets" / "gastrointestinal"

TRAIN_DIR = DATASET_DIR / "train"

VAL_DIR = DATASET_DIR / "val"

MODEL_OUTPUT_PATH = BASE_DIR / "app" / "models" / "model.pt"

BATCH_SIZE = 8

NUM_EPOCHS = 5

LEARNING_RATE = 0.0001

IMAGE_SIZE = (224, 224)


transform = transforms.Compose(
    [
        transforms.Resize(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


train_dataset = datasets.ImageFolder(
    root=TRAIN_DIR,
    transform=transform,
)

val_dataset = datasets.ImageFolder(
    root=VAL_DIR,
    transform=transform,
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


model = models.resnet50(weights="IMAGENET1K_V1")

in_features = model.fc.in_features

model.fc = nn.Linear(in_features, 2)

model.to(DEVICE)


criterion = nn.CrossEntropyLoss()

optimizer = Adam(
    model.parameters(),
    lr=LEARNING_RATE,
)


def train():
    """
    Executa o treinamento do modelo.
    """

    print("Starting training...")

    for epoch in range(NUM_EPOCHS):

        model.train()

        running_loss = 0.0

        for images, labels in train_loader:

            images = images.to(DEVICE)

            labels = labels.to(DEVICE)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(outputs, labels)

            loss.backward()

            optimizer.step()

            running_loss += loss.item()

        epoch_loss = running_loss / len(train_loader)

        print(f"Epoch {epoch + 1}/{NUM_EPOCHS}")
        print(f"Loss: {epoch_loss:.4f}")

    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), MODEL_OUTPUT_PATH)

    print(f"Model saved at: {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    train()