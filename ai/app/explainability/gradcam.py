"""Geração de mapas de atribuição visual do ClinicAI."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import (
    preprocess_image as gradcam_preprocess_image,
    show_cam_on_image,
)

from app.config import (
    NORMALIZE_MEAN,
    NORMALIZE_STD,
    TARGET_IMAGE_SIZE,
)
from app.inference.domains.gastrointestinal import (
    ensemble_stacking,
    resnet50,
)
from app.inference.model_loader import DEVICE
from app.inference.preprocess import preprocess_image
from training.preprocessing.pipeline import (
    preprocess_for_training,
)


GRADCAM_SUPPORTED_DOMAINS = frozenset(
    {"gastrointestinal"}
)


def generate_gradcam_from_bytes(
    image_bytes: bytes,
    *,
    domain: str,
) -> bytes | None:
    """Gera o Grad-CAM em memória para o domínio gastrointestinal."""

    if domain not in GRADCAM_SUPPORTED_DOMAINS:
        return None

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    image_array = preprocess_for_training(
        np.array(image)
    )

    resized = cv2.resize(
        image_array,
        TARGET_IMAGE_SIZE,
    )

    rgb_image = (
        resized.astype(np.float32)
        / 255.0
    )

    input_tensor = (
        gradcam_preprocess_image(
            rgb_image,
            mean=NORMALIZE_MEAN,
            std=NORMALIZE_STD,
        )
        .to(DEVICE)
    )

    model = resnet50.torch_model
    target_layers = [
        model.layer4[-1]
    ]

    cam = GradCAM(
        model=model,
        target_layers=target_layers,
    )

    grayscale_cam = cam(
        input_tensor=input_tensor
    )[0]

    visualization = (
        build_attribution_visualization(
            image_array,
            grayscale_cam,
        )
    )

    success, encoded = cv2.imencode(
        ".jpg",
        cv2.cvtColor(
            visualization,
            cv2.COLOR_RGB2BGR,
        ),
    )

    if not success:
        raise RuntimeError(
            "Não foi possível codificar o Grad-CAM gerado."
        )

    return encoded.tobytes()


ATTRIBUTION_METHOD = (
    "weighted_base_gradcam_oriented_by_"
    "ensemble_stacking_v1"
)

SUPPORTED_DOMAINS = frozenset(
    {"gastrointestinal"}
)

MODEL_ORDER = (
    "resnet50",
    "efficientnet_b4",
    "pvt_v2_b2",
)

TARGET_LAYER_NAMES = {
    "resnet50": "layer4[-1]",
    "efficientnet_b4": "blocks[-1]",
    "pvt_v2_b2": "stages[-1]",
}

MINIMUM_CAM_VALUE = 1e-12


@dataclass(frozen=True)
class EnsembleAttributionResult:
    """Resultado serializável da explicabilidade do ensemble."""

    image_bytes: bytes | None
    final_probabilities: tuple[float, float]
    predicted_class: int
    method: str
    target_layers: dict[str, str]
    local_evidence: dict[str, float]
    branch_weights: dict[str, float] | None
    branch_cam_raw_maxima: dict[str, float] | None
    unavailable_reason: str | None = None


def calculate_normalized_branch_cam(
    activation: torch.Tensor,
    gradient: torch.Tensor,
    *,
    output_size: tuple[int, int],
) -> tuple[np.ndarray, float]:
    """
    Calcula o Grad-CAM normalizado de um modelo-base.

    ``output_size`` usa a ordem ``(altura, largura)`` esperada
    pelo ``torch.nn.functional.interpolate``.
    """

    if activation.ndim != 4:
        raise RuntimeError(
            "A ativação usada pelo Grad-CAM deve possuir "
            f"quatro dimensões; recebido {tuple(activation.shape)}."
        )

    if gradient.shape != activation.shape:
        raise RuntimeError(
            "Ativação e gradiente devem possuir o mesmo formato."
        )

    channel_weights = gradient.mean(
        dim=(2, 3),
        keepdim=True,
    )

    raw_cam = torch.relu(
        (
            channel_weights
            * activation
        ).sum(
            dim=1,
            keepdim=True,
        )
    )

    raw_maximum = float(
        raw_cam
        .max()
        .detach()
        .cpu()
    )

    resized_cam = F.interpolate(
        raw_cam,
        size=output_size,
        mode="bilinear",
        align_corners=False,
    )[0, 0]

    resized_maximum = float(
        resized_cam
        .max()
        .detach()
        .cpu()
    )

    if resized_maximum <= MINIMUM_CAM_VALUE:
        normalized = torch.zeros_like(
            resized_cam
        )
    else:
        normalized = (
            resized_cam
            / resized_maximum
        )

    return (
        normalized
        .detach()
        .cpu()
        .numpy()
        .astype(np.float32),
        raw_maximum,
    )


def combine_branch_cams(
    branch_cams: dict[str, np.ndarray],
    branch_weights: dict[str, float],
) -> np.ndarray | None:
    """Combina os mapas normalizados usando os pesos locais."""

    if set(branch_weights) != set(MODEL_ORDER):
        raise RuntimeError(
            "Os pesos locais não correspondem aos "
            "três modelos-base esperados."
        )

    missing_cams = [
        model_name
        for model_name in MODEL_ORDER
        if model_name not in branch_cams
    ]

    if missing_cams:
        raise RuntimeError(
            "Mapas ausentes para: "
            + ", ".join(missing_cams)
        )

    first_shape = branch_cams[
        MODEL_ORDER[0]
    ].shape

    combined = np.zeros(
        first_shape,
        dtype=np.float64,
    )

    for model_name in MODEL_ORDER:
        cam = np.asarray(
            branch_cams[model_name],
            dtype=np.float64,
        )

        if cam.shape != first_shape:
            raise RuntimeError(
                "Todos os mapas dos modelos-base devem "
                "possuir o mesmo formato."
            )

        weight = float(
            branch_weights[model_name]
        )

        if not np.isfinite(weight) or weight < 0.0:
            raise RuntimeError(
                "Os pesos locais devem ser finitos "
                "e não negativos."
            )

        combined += weight * cam

    combined = np.maximum(
        combined,
        0.0,
    )

    maximum = float(
        combined.max()
    )

    if maximum <= MINIMUM_CAM_VALUE:
        return None

    return (
        combined
        / maximum
    ).astype(np.float32)


def _prepare_processed_image(
    image_bytes: bytes,
) -> np.ndarray:
    """Obtém a ROI pré-processada sem alterar sua proporção visual."""

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    return preprocess_for_training(
        np.asarray(image)
    )


def crop_attribution_to_visual_roi(
    processed_image: np.ndarray,
    attribution_map: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Remove bordas escuras apenas da representação visual.

    A entrada usada pelo modelo permanece inalterada. A imagem e o mapa
    restaurado são recortados pelos mesmos limites para preservar o
    alinhamento espacial da atribuição.
    """

    if attribution_map.shape != processed_image.shape[:2]:
        raise ValueError(
            "O mapa restaurado deve possuir as dimensões da imagem."
        )

    intensity = processed_image.max(
        axis=2
    )

    content_mask = (
        intensity > 20
    ).astype(np.uint8)

    closing_kernel = np.ones(
        (11, 11),
        dtype=np.uint8,
    )

    content_mask = cv2.morphologyEx(
        content_mask,
        cv2.MORPH_CLOSE,
        closing_kernel,
    )

    (
        component_count,
        _labels,
        statistics,
        _centroids,
    ) = cv2.connectedComponentsWithStats(
        content_mask,
        8,
    )

    if component_count <= 1:
        return processed_image, attribution_map

    component = 1 + int(
        np.argmax(
            statistics[
                1:,
                cv2.CC_STAT_AREA,
            ]
        )
    )

    x, y, width, height, area = (
        int(value)
        for value in statistics[component]
    )

    image_area = float(
        processed_image.shape[0]
        * processed_image.shape[1]
    )

    if area / image_area < 0.20:
        return processed_image, attribution_map

    row_slice = slice(
        y,
        y + height,
    )
    column_slice = slice(
        x,
        x + width,
    )

    return (
        processed_image[
            row_slice,
            column_slice,
        ],
        attribution_map[
            row_slice,
            column_slice,
        ],
    )


def build_attribution_visualization(
    processed_image: np.ndarray,
    attribution_map: np.ndarray,
) -> np.ndarray:
    """
    Sobrepõe o mapa sobre a área endoscópica sem deformação visual.

    O modelo continua recebendo a entrada configurada em TARGET_IMAGE_SIZE.
    Somente a representação visual restaura a proporção e remove as bordas
    escuras residuais do pré-processamento replicado de Viana.
    """

    if (
        processed_image.ndim != 3
        or processed_image.shape[2] != 3
    ):
        raise ValueError(
            "A imagem processada deve possuir três canais RGB."
        )

    if attribution_map.ndim != 2:
        raise ValueError(
            "O mapa de atribuição deve possuir duas dimensões."
        )

    height, width = processed_image.shape[:2]

    restored_map = cv2.resize(
        attribution_map,
        (width, height),
        interpolation=cv2.INTER_LINEAR,
    )

    restored_map = np.clip(
        restored_map,
        0.0,
        1.0,
    ).astype(np.float32)

    visual_image, visual_map = (
        crop_attribution_to_visual_roi(
            processed_image,
            restored_map,
        )
    )

    rgb_image = (
        visual_image.astype(np.float32)
        / 255.0
    )

    return show_cam_on_image(
        rgb_image,
        visual_map,
        use_rgb=True,
    )

def _resolve_target_layers():
    """Resolve as camadas espaciais dos três modelos-base."""

    predictors = {
        predictor.name: predictor
        for predictor
        in ensemble_stacking.base_predictors
    }

    missing_predictors = [
        model_name
        for model_name in MODEL_ORDER
        if model_name not in predictors
    ]

    if missing_predictors:
        raise RuntimeError(
            "Modelos-base ausentes no ensemble: "
            + ", ".join(missing_predictors)
        )

    resnet_model = predictors[
        "resnet50"
    ].torch_model

    efficientnet_model = predictors[
        "efficientnet_b4"
    ].torch_model

    pvt_model = predictors[
        "pvt_v2_b2"
    ].torch_model

    return (
        (
            "resnet50",
            TARGET_LAYER_NAMES["resnet50"],
            resnet_model.layer4[-1],
        ),
        (
            "efficientnet_b4",
            TARGET_LAYER_NAMES[
                "efficientnet_b4"
            ],
            efficientnet_model.blocks[-1],
        ),
        (
            "pvt_v2_b2",
            TARGET_LAYER_NAMES[
                "pvt_v2_b2"
            ],
            pvt_model.stages[-1],
        ),
    )


def generate_ensemble_attribution_from_bytes(
    image_bytes: bytes,
    *,
    domain: str,
) -> EnsembleAttributionResult | None:
    """
    Gera um mapa composto orientado pela classe final do ensemble.

    Cada arquitetura produz um Grad-CAM para o logit da classe
    escolhida pelo Ensemble Stacking. Os três mapas são combinados
    pelas evidências locais positivas do metaclassificador.
    """

    if domain not in SUPPORTED_DOMAINS:
        return None

    target_layer_specs = (
        _resolve_target_layers()
    )

    captured_activations: dict[
        str,
        torch.Tensor,
    ] = {}

    hook_handles = []

    def make_hook(model_name: str):
        def hook(
            _module,
            _inputs,
            output,
        ):
            if not isinstance(
                output,
                torch.Tensor,
            ):
                raise RuntimeError(
                    "A camada-alvo de "
                    f"{model_name} não retornou tensor."
                )

            if output.ndim != 4:
                raise RuntimeError(
                    "A camada-alvo de "
                    f"{model_name} retornou "
                    f"{tuple(output.shape)}, esperado 4D."
                )

            captured_activations[
                model_name
            ] = output

        return hook

    for (
        model_name,
        _layer_name,
        target_layer,
    ) in target_layer_specs:
        hook_handles.append(
            target_layer.register_forward_hook(
                make_hook(model_name)
            )
        )

    try:
        image_tensor = preprocess_image(
            image_bytes
        )

        differentiable = (
            ensemble_stacking
            .predict_differentiable(
                image_tensor
            )
        )

        final_probabilities_tensor = (
            differentiable
            .final_probabilities[0]
        )

        predicted_class = int(
            torch.argmax(
                final_probabilities_tensor
            )
            .detach()
            .cpu()
        )

        local_evidence, branch_weights = (
            ensemble_stacking
            .calculate_local_evidence_weights(
                base_probabilities=(
                    differentiable
                    .base_probabilities
                ),
                predicted_class=predicted_class,
            )
        )

        final_probabilities = tuple(
            float(value)
            for value in (
                final_probabilities_tensor
                .detach()
                .cpu()
                .numpy()
            )
        )

        if branch_weights is None:
            return EnsembleAttributionResult(
                image_bytes=None,
                final_probabilities=(
                    final_probabilities[0],
                    final_probabilities[1],
                ),
                predicted_class=predicted_class,
                method=ATTRIBUTION_METHOD,
                target_layers=dict(
                    TARGET_LAYER_NAMES
                ),
                local_evidence=local_evidence,
                branch_weights=None,
                branch_cam_raw_maxima=None,
                unavailable_reason=(
                    "Nenhum modelo-base apresentou "
                    "evidência local positiva para a "
                    "classe final do ensemble."
                ),
            )

        missing_activations = [
            model_name
            for model_name in MODEL_ORDER
            if model_name
            not in captured_activations
        ]

        if missing_activations:
            raise RuntimeError(
                "Ativações não capturadas para: "
                + ", ".join(
                    missing_activations
                )
            )

        branch_targets = tuple(
            differentiable
            .base_logits[model_name][
                0,
                predicted_class,
            ]
            for model_name in MODEL_ORDER
        )

        activations = tuple(
            captured_activations[
                model_name
            ]
            for model_name in MODEL_ORDER
        )

        branch_gradients = torch.autograd.grad(
            outputs=branch_targets,
            inputs=activations,
            grad_outputs=tuple(
                torch.ones_like(target)
                for target in branch_targets
            ),
            retain_graph=False,
            create_graph=False,
            allow_unused=False,
        )

        output_size = (
            TARGET_IMAGE_SIZE[1],
            TARGET_IMAGE_SIZE[0],
        )

        branch_cams: dict[
            str,
            np.ndarray,
        ] = {}

        branch_cam_raw_maxima: dict[
            str,
            float,
        ] = {}

        for (
            model_name,
            activation,
            gradient,
        ) in zip(
            MODEL_ORDER,
            activations,
            branch_gradients,
            strict=True,
        ):
            cam, raw_maximum = (
                calculate_normalized_branch_cam(
                    activation,
                    gradient,
                    output_size=output_size,
                )
            )

            branch_cams[model_name] = cam

            branch_cam_raw_maxima[
                model_name
            ] = raw_maximum

        combined_cam = combine_branch_cams(
            branch_cams,
            branch_weights,
        )

        if combined_cam is None:
            return EnsembleAttributionResult(
                image_bytes=None,
                final_probabilities=(
                    final_probabilities[0],
                    final_probabilities[1],
                ),
                predicted_class=predicted_class,
                method=ATTRIBUTION_METHOD,
                target_layers=dict(
                    TARGET_LAYER_NAMES
                ),
                local_evidence=local_evidence,
                branch_weights=branch_weights,
                branch_cam_raw_maxima=(
                    branch_cam_raw_maxima
                ),
                unavailable_reason=(
                    "A composição dos mapas não produziu "
                    "uma atribuição espacial mensurável."
                ),
            )

        processed_image = (
            _prepare_processed_image(
                image_bytes
            )
        )

        visualization = (
            build_attribution_visualization(
                processed_image,
                combined_cam,
            )
        )

        success, encoded = cv2.imencode(
            ".jpg",
            cv2.cvtColor(
                visualization,
                cv2.COLOR_RGB2BGR,
            ),
        )

        if not success:
            raise RuntimeError(
                "Não foi possível codificar o mapa "
                "de atribuição composto."
            )

        return EnsembleAttributionResult(
            image_bytes=encoded.tobytes(),
            final_probabilities=(
                final_probabilities[0],
                final_probabilities[1],
            ),
            predicted_class=predicted_class,
            method=ATTRIBUTION_METHOD,
            target_layers=dict(
                TARGET_LAYER_NAMES
            ),
            local_evidence=local_evidence,
            branch_weights=branch_weights,
            branch_cam_raw_maxima=(
                branch_cam_raw_maxima
            ),
            unavailable_reason=None,
        )

    finally:
        for handle in hook_handles:
            handle.remove()
