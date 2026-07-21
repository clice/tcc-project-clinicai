"""Propagação segura dos metadados HTTP para a auditoria."""

from datetime import date, datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.request_context import (
    bind_request_audit_context,
    get_request_audit_context,
)
from app.main import attach_request_audit_context
from app.modules.audit_logs.model import AuditLog
from app.modules.audit_logs.service import (
    _query_audit_logs,
    create_audit_log,
)


def test_request_context_is_scoped_and_restored() -> None:
    assert get_request_audit_context() == (
        None,
        None,
    )

    with bind_request_audit_context(
        ip_address="203.0.113.10",
        user_agent="pytest-clinicai",
    ):
        assert get_request_audit_context() == (
            "203.0.113.10",
            "pytest-clinicai",
        )

    assert get_request_audit_context() == (
        None,
        None,
    )


def test_audit_log_inherits_current_request_metadata() -> None:
    db = Mock(spec=Session)

    with bind_request_audit_context(
        ip_address="203.0.113.20",
        user_agent="pytest-clinicai",
    ):
        audit_log = create_audit_log(
            db,
            user_id=1,
            clinic_id=2,
            action="update",
            entity="patient",
            entity_id=3,
        )

    assert audit_log.ip_address == "203.0.113.20"
    assert audit_log.user_agent == "pytest-clinicai"
    db.add.assert_called_once_with(
        audit_log
    )


def test_explicit_metadata_has_precedence_over_context() -> None:
    db = Mock(spec=Session)

    with bind_request_audit_context(
        ip_address="203.0.113.30",
        user_agent="context-agent",
    ):
        audit_log = create_audit_log(
            db,
            user_id=1,
            clinic_id=2,
            action="login_success",
            entity="auth",
            ip_address="127.0.0.1",
            user_agent="explicit-agent",
        )

    assert audit_log.ip_address == "127.0.0.1"
    assert audit_log.user_agent == "explicit-agent"



def test_audit_query_filters_inclusive_date_period(
    db_session,
) -> None:
    before = AuditLog(
        action="period_filter_test",
        entity="test",
        created_at=datetime(
            2026,
            6,
            30,
            23,
            59,
            tzinfo=timezone.utc,
        ),
    )
    inside = AuditLog(
        action="period_filter_test",
        entity="test",
        created_at=datetime(
            2026,
            7,
            20,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )
    after = AuditLog(
        action="period_filter_test",
        entity="test",
        created_at=datetime(
            2026,
            8,
            1,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    )

    db_session.add_all(
        [before, inside, after]
    )
    db_session.flush()

    result = _query_audit_logs(
        db_session,
        action="period_filter_test",
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
    )

    assert result["total"] == 1
    assert result["items"][0]["id"] == inside.id


def test_audit_query_rejects_inverted_period(
    db_session,
) -> None:
    with pytest.raises(
        HTTPException,
        match=(
            "A data inicial não pode ser "
            "posterior à data final"
        ),
    ):
        _query_audit_logs(
            db_session,
            date_from=date(2026, 7, 31),
            date_to=date(2026, 7, 1),
        )



def test_http_middleware_propagates_metadata_to_sync_service() -> None:
    test_app = FastAPI()
    test_app.middleware("http")(
        attach_request_audit_context
    )

    @test_app.get("/audit-context")
    def read_audit_context():
        db = Mock(spec=Session)
        audit_log = create_audit_log(
            db,
            user_id=1,
            clinic_id=2,
            action="update",
            entity="patient",
        )

        return {
            "ip_address": audit_log.ip_address,
            "user_agent": audit_log.user_agent,
        }

    with TestClient(test_app) as client:
        response = client.get(
            "/audit-context",
            headers={
                "user-agent": "pytest-http-context",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "ip_address": "testclient",
        "user_agent": "pytest-http-context",
    }
