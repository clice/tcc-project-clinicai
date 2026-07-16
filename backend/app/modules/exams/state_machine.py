"""Máquina de estados autoritativa do ciclo de exames do ClinicAI.

A tabela deste módulo é a fonte única para transições de estado. Serviços e
rotas não devem atribuir ``status_id`` diretamente sem validar uma ação aqui.
"""

from __future__ import annotations

from enum import StrEnum

from fastapi import HTTPException

from app.common.constants import StatusName


class ExamTransitionAction(StrEnum):
    """Ações de domínio que podem alterar o estado de um exame."""

    CREATE = "create"
    START_PROCESSING = "start_processing"
    CANCEL = "cancel"
    RESTORE = "restore"
    REPLACE_FILE = "replace_file"
    ANALYSIS_SUCCEEDED = "analysis_succeeded"
    ANALYSIS_FAILED = "analysis_failed"
    REVIEW_CONFIRM = "review_confirm"
    REVIEW_DIVERGENCE = "review_divergence"


# (estado atual, ação) -> próximo estado. ``None`` representa um exame ainda
# inexistente. Auto-transições aparecem somente quando a ação tem efeito real
# no recurso (por exemplo, substituir a imagem mantém o estado pending).
EXAM_TRANSITION_TABLE: dict[tuple[str | None, ExamTransitionAction], str] = {
    (None, ExamTransitionAction.CREATE): StatusName.PENDING.value,
    (StatusName.PENDING.value, ExamTransitionAction.START_PROCESSING): StatusName.PROCESSING.value,
    (StatusName.PENDING.value, ExamTransitionAction.CANCEL): StatusName.CANCELED.value,
    (StatusName.PENDING.value, ExamTransitionAction.REPLACE_FILE): StatusName.PENDING.value,
    (StatusName.PROCESSING.value, ExamTransitionAction.CANCEL): StatusName.CANCELED.value,
    (
        StatusName.PROCESSING.value,
        ExamTransitionAction.ANALYSIS_SUCCEEDED,
    ): StatusName.AWAITING_REVIEW.value,
    (StatusName.PROCESSING.value, ExamTransitionAction.ANALYSIS_FAILED): StatusName.FAILED.value,
    (StatusName.FAILED.value, ExamTransitionAction.RESTORE): StatusName.PENDING.value,
    (StatusName.FAILED.value, ExamTransitionAction.REPLACE_FILE): StatusName.PENDING.value,
    (StatusName.CANCELED.value, ExamTransitionAction.RESTORE): StatusName.PENDING.value,
    (
        StatusName.AWAITING_REVIEW.value,
        ExamTransitionAction.REVIEW_CONFIRM,
    ): StatusName.COMPLETED.value,
    (
        StatusName.AWAITING_REVIEW.value,
        ExamTransitionAction.REVIEW_DIVERGENCE,
    ): StatusName.COMPLETED_WITH_DIVERGENCE.value,
}

EXAM_STATUS_NAMES = frozenset(
    {
        StatusName.PENDING.value,
        StatusName.PROCESSING.value,
        StatusName.AWAITING_REVIEW.value,
        StatusName.COMPLETED.value,
        StatusName.COMPLETED_WITH_DIVERGENCE.value,
        StatusName.FAILED.value,
        StatusName.CANCELED.value,
    }
)

FINAL_EXAM_STATUSES = frozenset(
    {
        StatusName.COMPLETED.value,
        StatusName.COMPLETED_WITH_DIVERGENCE.value,
    }
)

EDITABLE_EXAM_STATUSES = frozenset(
    {
        StatusName.PENDING.value,
        StatusName.FAILED.value,
    }
)


def get_transition_target(
    current_status: str | None,
    action: ExamTransitionAction,
) -> str:
    """Retorna o próximo estado ou rejeita a transição com HTTP 409."""

    target = EXAM_TRANSITION_TABLE.get((current_status, action))
    if target is None:
        current_label = current_status or "inexistente"
        raise HTTPException(
            status_code=409,
            detail=(
                f"Transição de exame não permitida: estado '{current_label}', "
                f"ação '{action.value}'."
            ),
        )

    return target


def ensure_exam_is_editable(current_status: str | None) -> None:
    """Permite edição somente antes da análise ou depois de uma falha."""

    if current_status not in EDITABLE_EXAM_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="Os dados do exame não podem ser editados no estado atual.",
        )


def transition_audit_payload(
    *,
    old_status_id: int,
    old_status_name: str,
    new_status_id: int,
    new_status_name: str,
    action: ExamTransitionAction,
    **extra: object,
) -> tuple[dict[str, object], dict[str, object]]:
    """Padroniza os dados usados pelo histórico de status baseado em auditoria."""

    old_data: dict[str, object] = {
        "status_id": old_status_id,
        "status_name": old_status_name,
    }
    new_data: dict[str, object] = {
        "status_id": new_status_id,
        "status_name": new_status_name,
        "transition_action": action.value,
        **extra,
    }
    return old_data, new_data
