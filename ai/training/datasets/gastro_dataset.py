"""
Dataset customizado para imagens gastrointestinais.
"""

from pathlib import Path

import cv2
import torch
from torch.utils.data import Dataset
from torchvision import transforms

from training.preprocessing.pipeline import (
    preprocess_for_training,
)


class GastroDataset(Dataset):
    """
    Dataset customizado para exames endoscópicos.
    """

    def __init__(self, image_paths, labels, image_size=(224, 224)):
        self.image_paths = image_paths

        self.labels = labels

        self.transform = transforms.Compose(
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

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, index):

        image_path = self.image_paths[index]

        label = self.labels[index]

        image_bgr = cv2.imread(str(image_path))

        image_rgb = cv2.cvtColor(
            image_bgr,
            cv2.COLOR_BGR2RGB,
        )

        processed_image = preprocess_for_training(
            image_rgb
        )

        image_tensor = self.transform(
            processed_image
        )

        return image_tensor, torch.tensor(label)
