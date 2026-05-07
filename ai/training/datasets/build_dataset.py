"""
Construção do dataset gastrointestinal.
"""

from pathlib import Path

from sklearn.model_selection import train_test_split


CLASS_MAPPING = {
    "normal": 0,
    "abnormal": 1,
}


VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def collect_image_paths(dataset_dir: Path):
    """
    Coleta caminhos das imagens e labels.
    """

    image_paths = []

    labels = []

    for class_name, class_index in CLASS_MAPPING.items():

        class_dir = dataset_dir / class_name

        if not class_dir.exists():
            continue

        for image_path in class_dir.iterdir():

            if image_path.suffix.lower() not in VALID_EXTENSIONS:
                continue

            image_paths.append(image_path)

            labels.append(class_index)

    return image_paths, labels


def build_train_validation_split(
    dataset_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
):
    """
    Cria separação treino/validação.
    """

    image_paths, labels = collect_image_paths(
        dataset_dir
    )

    (
        train_paths,
        val_paths,
        train_labels,
        val_labels,
    ) = train_test_split(
        image_paths,
        labels,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    return (
        train_paths,
        val_paths,
        train_labels,
        val_labels,
    )