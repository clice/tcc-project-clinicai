"""
Dataset customizado para imagens gastrointestinais.
"""

import cv2
import torch

from torch.utils.data import Dataset

from torchvision import transforms

from training.preprocessing.pipeline import (
    preprocess_for_training,
)


# =========================================================
# TRANSFORMS
# =========================================================

def build_train_transform(image_size):
    """
    Transformações usadas no treino.

    Inclui Data Augmentation fiel ao protocolo de Pedro Viana (2026),
    validado no notebook de treino: flip horizontal, flip vertical e
    rotação de até 10 graus. Não inclui ColorJitter nem RandomAffine —
    esses dois eram adições próprias de uma versão anterior deste módulo,
    removidas por não fazerem parte do protocolo documentado na
    monografia.
    """

    return transforms.Compose(
        [
            transforms.ToPILImage(),

            transforms.Resize(image_size),

            transforms.RandomHorizontalFlip(
                p=0.5
            ),

            transforms.RandomVerticalFlip(
                p=0.5
            ),

            transforms.RandomRotation(
                degrees=10
            ),

            transforms.ToTensor(),

            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )


def build_validation_transform(image_size):
    """
    Transformações usadas na validação.

    Sem augmentation.
    """

    return transforms.Compose(
        [
            transforms.ToPILImage(),

            transforms.Resize(image_size),

            transforms.ToTensor(),

            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )


# =========================================================
# DATASET
# =========================================================

class GastroDataset(Dataset):
    """
    Dataset customizado para exames endoscópicos.
    """

    def __init__(
        self,
        image_paths,
        labels,
        image_size=(224, 224),
        train=True,
    ):

        self.image_paths = image_paths

        self.labels = labels

        self.train = train

        if train:

            self.transform = build_train_transform(
                image_size
            )

        else:

            self.transform = build_validation_transform(
                image_size
            )

    def __len__(self):

        return len(self.image_paths)

    def __getitem__(self, index):

        image_path = self.image_paths[index]

        label = self.labels[index]

        image_bgr = cv2.imread(
            str(image_path)
        )

        image_rgb = cv2.cvtColor(
            image_bgr,
            cv2.COLOR_BGR2RGB,
        )

        # =================================================
        # PREPROCESSAMENTO MÉDICO
        # =================================================

        processed_image = preprocess_for_training(
            image_rgb
        )

        # =================================================
        # TRANSFORM
        # =================================================

        image_tensor = self.transform(
            processed_image
        )

        return (
            image_tensor,
            torch.tensor(label),
        )
        