"""Invariantes do histórico acadêmico demonstrativo."""

from collections import Counter
from datetime import datetime

import pytest
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.constants import (
    AuditAction,
    AuditEntity,
    StatusName,
)
from app.modules import models  # noqa: F401
from app.modules.ai_analyses import (
    file_storage as attribution_file_storage,
)
from app.modules.audit_logs.model import AuditLog
from app.modules.audit_logs.seed import (
    DEMO_AUDIT_USER_AGENT,
    EXPECTED_DEMO_AUDIT_LOG_COUNT,
)
from app.modules.exams import (
    file_storage as exam_file_storage,
)
from app.modules.seeds import (
    bootstrap_reference_data,
    seed_academic_demo,
)


@pytest.fixture
def isolated_demo_uploads(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    data_root = tmp_path / "data"
    exams_root = data_root / "exams"

    monkeypatch.setattr(
        exam_file_storage,
        "DATA_DIR",
        data_root,
    )
    monkeypatch.setattr(
        exam_file_storage,
        "UPLOAD_DIR",
        exams_root,
    )
    monkeypatch.setattr(
        attribution_file_storage,
        "DATA_DIR",
        data_root,
    )
    monkeypatch.setattr(
        attribution_file_storage,
        "EXAMS_DIR",
        exams_root,
    )

    return exams_root


def demo_logs(db: Session) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.user_agent
            == DEMO_AUDIT_USER_AGENT
        )
        .order_by(
            AuditLog.created_at.asc(),
            AuditLog.id.asc(),
        )
        .all()
    )


def event_key(log: AuditLog) -> str:
    assert isinstance(log.new_data, dict)

    key = log.new_data.get(
        "demo_event_key"
    )

    assert isinstance(key, str)
    assert key

    return key


def expected_exam_actions(
    status_name: str,
) -> list[str]:
    base = [
        AuditAction.CREATE.value,
        AuditAction.UPLOAD.value,
    ]

    if status_name == StatusName.PENDING.value:
        return base

    if status_name == StatusName.CANCELED.value:
        return [
            *base,
            AuditAction.CANCEL_EXAM.value,
        ]

    if status_name == StatusName.FAILED.value:
        return [
            *base,
            AuditAction.RUN_AI_ANALYSIS.value,
            AuditAction.AI_ANALYSIS_FAILED.value,
        ]

    if status_name == (
        StatusName.AWAITING_REVIEW.value
    ):
        return [
            *base,
            AuditAction.RUN_AI_ANALYSIS.value,
            AuditAction.RUN_AI_ANALYSIS.value,
        ]

    return [
        *base,
        AuditAction.RUN_AI_ANALYSIS.value,
        AuditAction.RUN_AI_ANALYSIS.value,
        AuditAction.REVIEW_EXAM.value,
    ]


def test_academic_demo_builds_deterministic_history(
    db_session: Session,
    isolated_demo_uploads,
) -> None:
    bootstrap = bootstrap_reference_data(
        db_session
    )
    db_session.commit()

    assert (
        db_session.query(
            func.count(AuditLog.id)
        ).scalar()
        == 0
    )

    demo = seed_academic_demo(
        db_session,
        bootstrap,
    )
    db_session.commit()

    logs = demo_logs(db_session)

    assert len(demo.audit_logs) == (
        EXPECTED_DEMO_AUDIT_LOG_COUNT
    )
    assert len(logs) == (
        EXPECTED_DEMO_AUDIT_LOG_COUNT
    )

    keys = [event_key(log) for log in logs]

    assert len(keys) == len(set(keys))

    action_counts = Counter(
        log.action for log in logs
    )

    assert action_counts == Counter(
        {
            AuditAction.CREATE.value: 90,
            AuditAction.UPLOAD.value: 90,
            AuditAction.RUN_AI_ANALYSIS.value: 222,
            AuditAction.REVIEW_EXAM.value: 50,
            AuditAction.AI_ANALYSIS_FAILED.value: 6,
            AuditAction.CANCEL_EXAM.value: 6,
        }
    )

    entity_counts = Counter(
        log.entity for log in logs
    )

    assert entity_counts == Counter(
        {
            AuditEntity.EXAM.value: 392,
            AuditEntity.AI_ANALYSIS.value: 72,
        }
    )

    forbidden_keys = {
        "file_path",
        "gradcam_path",
        "raw_response",
        "image_base64",
        "gradcam_base64",
    }

    for log in logs:
        assert log.user_id is not None
        assert log.clinic_id is not None
        assert log.ip_address is None
        assert log.user_agent == (
            DEMO_AUDIT_USER_AGENT
        )
        assert log.new_data[
            "academic_demo"
        ] is True
        assert not (
            forbidden_keys
            & set(log.new_data)
        )

    for exam in demo.exams.values():
        entries = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.user_agent
                == DEMO_AUDIT_USER_AGENT,
                AuditLog.entity
                == AuditEntity.EXAM.value,
                AuditLog.entity_id
                == exam.id,
            )
            .order_by(
                AuditLog.created_at.asc(),
                AuditLog.id.asc(),
            )
            .all()
        )

        assert [
            entry.action
            for entry in entries
        ] == expected_exam_actions(
            exam.status.name
        )

        timestamps = [
            entry.created_at
            for entry in entries
        ]

        assert timestamps == sorted(timestamps)
        assert isinstance(
            exam.created_at,
            datetime,
        )
        assert isinstance(
            exam.updated_at,
            datetime,
        )
        assert exam.created_at == timestamps[0]
        assert exam.updated_at == timestamps[-1]

        if exam.status.name in {
            StatusName.COMPLETED.value,
            (
                StatusName
                .COMPLETED_WITH_DIVERGENCE
                .value
            ),
        }:
            assert exam.reviewed_at == (
                timestamps[-1]
            )

    for analysis in demo.ai_analyses.values():
        entries = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.user_agent
                == DEMO_AUDIT_USER_AGENT,
                AuditLog.entity
                == AuditEntity.AI_ANALYSIS.value,
                AuditLog.entity_id
                == analysis.id,
            )
            .all()
        )

        assert len(entries) == 1
        assert entries[0].action == (
            AuditAction.RUN_AI_ANALYSIS.value
        )
        assert entries[0].created_at == (
            analysis.created_at
        )


def test_academic_demo_history_is_idempotent(
    db_session: Session,
    isolated_demo_uploads,
) -> None:
    bootstrap = bootstrap_reference_data(
        db_session
    )
    db_session.commit()

    seed_academic_demo(
        db_session,
        bootstrap,
    )
    db_session.commit()

    initial_ids = {
        event_key(log): log.id
        for log in demo_logs(db_session)
    }

    for _ in range(3):
        bootstrap = bootstrap_reference_data(
            db_session
        )
        seed_academic_demo(
            db_session,
            bootstrap,
        )
        db_session.commit()

    final_logs = demo_logs(db_session)

    assert len(final_logs) == (
        EXPECTED_DEMO_AUDIT_LOG_COUNT
    )

    assert {
        event_key(log): log.id
        for log in final_logs
    } == initial_ids
