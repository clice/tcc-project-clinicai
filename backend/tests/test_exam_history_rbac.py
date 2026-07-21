"""Cobertura RBAC e contratual do histórico de exames (RF36)."""

import inspect
from types import SimpleNamespace

from fastapi.routing import APIRoute

from app.modules.ai_analyses.service import create_ai_analysis
from app.modules.exams.router import router as exams_router
from app.modules.exams.schema import ExamHistoryResponse
from app.modules.exams.service import get_exam_history


def find_history_route() -> APIRoute:
    return next(
        route
        for route in exams_router.routes
        if isinstance(route, APIRoute)
        and route.path == "/exams/{exam_id}/history"
        and "GET" in route.methods
    )


def test_exam_history_route_requires_exam_read_permission() -> None:
    route = find_history_route()
    permission_names = {
        getattr(dependency.call, "required_permission_name", None)
        for dependency in route.dependant.dependencies
    }

    assert "exams:read" in permission_names
    assert route.response_model is ExamHistoryResponse

    response_fields = ExamHistoryResponse.model_fields["items"].annotation.__args__[0].model_fields
    assert "ip_address" not in response_fields
    assert "user_agent" not in response_fields


def test_exam_history_validates_exam_scope_before_reading_logs(monkeypatch) -> None:
    exam = SimpleNamespace(id=7, clinic_id=1, doctor_id=10)
    current_user = SimpleNamespace(id=10)
    calls = []

    monkeypatch.setattr(
        "app.modules.exams.service.get_exam_model_by_id",
        lambda **kwargs: exam,
    )

    def validate_scope(**kwargs):
        calls.append(("scope", kwargs["exam"].id, kwargs["current_user"].id))

    monkeypatch.setattr(
        "app.modules.exams.service.validate_user_can_access_exam",
        validate_scope,
    )
    monkeypatch.setattr(
        "app.modules.exams.service.list_entity_audit_logs",
        lambda **kwargs: {
            "items": [],
            "total": 0,
            "limit": kwargs["limit"],
            "offset": 0,
        },
    )

    result = get_exam_history(db=SimpleNamespace(), exam_id=7, current_user=current_user)

    assert calls == [("scope", 7, 10)]
    assert result == {"items": [], "total": 0, "limit": 200, "offset": 0}


def test_successful_ai_analysis_registers_exam_history_event() -> None:
    """A transição para awaiting_review precisa aparecer no histórico RF36."""

    source = inspect.getsource(create_ai_analysis)

    assert source.count("action=AuditAction.RUN_AI_ANALYSIS") >= 2
    assert "entity=AuditEntity.EXAM" in source
    assert "entity_id=exam.id" in source
