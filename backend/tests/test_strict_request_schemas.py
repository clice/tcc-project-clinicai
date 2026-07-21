"""Testes de rejeição de campos desconhecidos nos payloads da API."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.modules.ai_analyses.schema import AIAnalysisCreate, AIAnalysisUpdate
from app.modules.auth.schema import RefreshTokenRequest
from app.modules.clinics.schema import ClinicCreate, ClinicUpdate
from app.modules.exams.schema import ExamCreate, ExamMedicalReview, ExamUpdate
from app.modules.patients.schema import PatientCreate, PatientUpdate
from app.modules.permissions.schema import PermissionUpdate
from app.modules.role_permissions.schema import (
    RolePermissionCreate,
    RolePermissionSyncRequest,
    RolePermissionUpdate,
)
from app.modules.roles.schema import RoleUpdate
from app.modules.statuses.schema import StatusUpdate
from app.modules.users.schema import (
    UserAdminUpdate,
    UserCreate,
    UserPasswordUpdate,
    UserSelfUpdate,
)


REQUEST_MODELS = (
    AIAnalysisCreate,
    AIAnalysisUpdate,
    RefreshTokenRequest,
    ClinicCreate,
    ClinicUpdate,
    ExamCreate,
    ExamUpdate,
    ExamMedicalReview,
    PatientCreate,
    PatientUpdate,
    PermissionUpdate,
    RolePermissionCreate,
    RolePermissionUpdate,
    RolePermissionSyncRequest,
    RoleUpdate,
    StatusUpdate,
    UserCreate,
    UserAdminUpdate,
    UserSelfUpdate,
    UserPasswordUpdate,
)


@pytest.mark.parametrize("request_model", REQUEST_MODELS)
def test_all_request_models_forbid_unknown_fields(request_model: type) -> None:
    """Garante que nenhum payload mapeado volte ao comportamento permissivo."""

    assert request_model.model_config.get("extra") == "forbid"


@pytest.mark.parametrize(
    ("request_model", "payload", "immutable_field"),
    (
        (PermissionUpdate, {"display_name": "Visualizar exames"}, "module"),
        (RoleUpdate, {"display_name": "Médico"}, "name"),
        (StatusUpdate, {"display_name": "Ativo"}, "name"),
        (RolePermissionSyncRequest, {"permission_ids": [1, 2]}, "role_id"),
    ),
)
def test_sensitive_models_reject_immutable_or_unknown_fields(
    request_model: type,
    payload: dict,
    immutable_field: str,
) -> None:
    """Confirma a rejeição dos exemplos de campos imutáveis do RBAC-08."""

    with pytest.raises(ValidationError) as error:
        request_model.model_validate({**payload, immutable_field: "valor indevido"})

    validation_error = error.value.errors()[0]
    assert validation_error["type"] == "extra_forbidden"
    assert validation_error["loc"] == (immutable_field,)
    assert validation_error["msg"] == "Extra inputs are not permitted"


def test_fastapi_returns_422_with_clear_error_for_unknown_field() -> None:
    """Valida o contrato HTTP exposto ao cliente da API."""

    app = FastAPI()

    @app.patch("/permissions")
    def update_permission(payload: PermissionUpdate) -> dict:
        return payload.model_dump(exclude_unset=True)

    response = TestClient(app).patch(
        "/permissions",
        json={"display_name": "Visualizar exames", "module": "users"},
    )

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["type"] == "extra_forbidden"
    assert error["loc"] == ["body", "module"]
    assert error["msg"] == "Extra inputs are not permitted"

    permission_schema = app.openapi()["components"]["schemas"]["PermissionUpdate"]
    assert permission_schema["additionalProperties"] is False


@pytest.mark.parametrize("field_name", ("findings", "conclusion"))
def test_exam_update_rejects_medical_review_fields_with_422(
    field_name: str,
) -> None:
    """Achados e conclusão pertencem exclusivamente à rota de revisão médica."""

    app = FastAPI()

    @app.patch("/exams/{exam_id}")
    def update_exam_route(exam_id: int, payload: ExamUpdate) -> dict:
        return {
            "exam_id": exam_id,
            **payload.model_dump(exclude_unset=True),
        }

    response = TestClient(app).patch(
        "/exams/1",
        json={
            field_name: "Conteúdo clínico enviado pela rota incorreta.",
        },
    )

    assert response.status_code == 422

    error = response.json()["detail"][0]

    assert error["type"] == "extra_forbidden"
    assert error["loc"] == ["body", field_name]
    assert error["msg"] == "Extra inputs are not permitted"
