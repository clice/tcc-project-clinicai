"""
Teste do builder de dataset.
"""

from pathlib import Path

from training.datasets.build_dataset import (
    build_train_validation_split,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATASET_DIR = (
    BASE_DIR
    / "datasets"
    / "gastrointestinal"
)


def main():

    (
        train_paths,
        val_paths,
        train_labels,
        val_labels,
    ) = build_train_validation_split(
        DATASET_DIR
    )

    print(f"Train samples: {len(train_paths)}")

    print(f"Validation samples: {len(val_paths)}")

    print(f"Train labels: {train_labels[:5]}")

    print(f"Validation labels: {val_labels[:5]}")


if __name__ == "__main__":
    main()