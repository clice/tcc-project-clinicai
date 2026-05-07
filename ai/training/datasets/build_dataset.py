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

    if not dataset_dir.exists():
        raise FileNotFoundError(
            f"Diretório do dataset não encontrado: {dataset_dir}"
        )

    for class_name, class_index in CLASS_MAPPING.items():
        class_dir = dataset_dir / class_name

        if not class_dir.exists():
            raise FileNotFoundError(
                f"Pasta da classe não encontrada: {class_dir}"
            )

        for image_path in class_dir.rglob("*"):
            if not image_path.is_file():
                continue

            if image_path.suffix.lower() not in VALID_EXTENSIONS:
                continue

            image_paths.append(image_path)
            labels.append(class_index)

    if len(image_paths) == 0:
        raise ValueError(
            "Nenhuma imagem foi encontrada no dataset. "
            f"Verifique se existem imagens em: {dataset_dir}/normal e {dataset_dir}/abnormal"
        )

    return image_paths, labels


def build_train_validation_split(
    dataset_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
):
    """
    Cria separação treino/validação.
    """

    image_paths, labels = collect_image_paths(dataset_dir)

    class_counts = {
        class_name: labels.count(class_index)
        for class_name, class_index in CLASS_MAPPING.items()
    }

    for class_name, count in class_counts.items():
        if count < 2:
            raise ValueError(
                f"A classe '{class_name}' possui apenas {count} imagem(ns). "
                "Para usar divisão estratificada, cada classe precisa ter pelo menos 2 imagens."
            )

    train_paths, val_paths, train_labels, val_labels = train_test_split(
        image_paths,
        labels,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    print("\n=== Dataset split ===")
    print(f"Total de imagens: {len(image_paths)}")
    print(f"Treino: {len(train_paths)}")
    print(f"Validação: {len(val_paths)}")
    print(f"Normal: {class_counts['normal']}")
    print(f"Abnormal: {class_counts['abnormal']}")

    return train_paths, val_paths, train_labels, val_labels
