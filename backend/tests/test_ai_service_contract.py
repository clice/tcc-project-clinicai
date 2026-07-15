"""CHK-12 — cliente backend e persistência do contrato multi-domínio."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from app.modules.ai_analysis import client as ai_client
from app.modules.ai_analysis.client import (
    AIServiceResponseError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
    request_prediction,
)
from app.modules.exams import service as exam_service


VALID_RESPONSE = {
    "exam_type": "colonoscopy",
    "exam_domain": "gastrointestinal",
    "prediction_class": 1,
    "label": "abnormal",
    "confidence": 0.9342,
    "model_name": "ensemble_stacking",
    "model_version": "models-v0.1.0",
    "gradcam_available": True,
    "gradcam_path": "/app/storage/gradcam/example.jpg",
    "device": "cpu",
}


class StubResponse:
    def __init__(self, *, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class StubAsyncClient:
    def __init__(self, *, response=None, error=None, captured=None, **_kwargs):
        self.response = response
        self.error = error
        self.captured = captured if captured is not None else {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def post(self, url, **kwargs):
        self.captured.update({"url": url, **kwargs})
        if self.error:
            raise self.error
        return self.response


def test_client_sends_exam_type_and_accepts_complete_contract(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        ai_client.httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            response=StubResponse(payload=dict(VALID_RESPONSE)),
            captured=captured,
            **kwargs,
        ),
    )

    result = asyncio.run(
        request_prediction(
            image_bytes=b"image",
            filename="exam.png",
            content_type="image/png",
            exam_type=" COLONOSCOPY ",
        )
    )

    assert captured["data"] == {"exam_type": "colonoscopy"}
    assert captured["files"]["file"] == ("exam.png", b"image", "image/png")
    assert result["exam_domain"] == "gastrointestinal"
    assert result["model_name"] == "ensemble_stacking"


def test_client_classifies_timeout(monkeypatch):
    request = httpx.Request("POST", "http://ai:8001/predict")
    monkeypatch.setattr(
        ai_client.httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            error=httpx.ReadTimeout("timeout", request=request),
            **kwargs,
        ),
    )

    with pytest.raises(AIServiceTimeoutError):
        asyncio.run(
            request_prediction(
                image_bytes=b"image",
                filename="exam.png",
                content_type="image/png",
                exam_type="endoscopy",
            )
        )


def test_client_classifies_unavailability(monkeypatch):
    request = httpx.Request("POST", "http://ai:8001/predict")
    monkeypatch.setattr(
        ai_client.httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            error=httpx.ConnectError("refused", request=request),
            **kwargs,
        ),
    )

    with pytest.raises(AIServiceUnavailableError):
        asyncio.run(
            request_prediction(
                image_bytes=b"image",
                filename="exam.png",
                content_type="image/png",
                exam_type="endoscopy",
            )
        )


def test_client_rejects_wrong_domain(monkeypatch):
    invalid = dict(VALID_RESPONSE, exam_domain="mammography")
    monkeypatch.setattr(
        ai_client.httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            response=StubResponse(payload=invalid),
            **kwargs,
        ),
    )

    with pytest.raises(AIServiceResponseError, match="não corresponde"):
        asyncio.run(
            request_prediction(
                image_bytes=b"image",
                filename="exam.png",
                content_type="image/png",
                exam_type="colonoscopy",
            )
        )


def test_client_rejects_inconsistent_gradcam(monkeypatch):
    invalid = dict(VALID_RESPONSE, gradcam_path=None)
    monkeypatch.setattr(
        ai_client.httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            response=StubResponse(payload=invalid),
            **kwargs,
        ),
    )

    with pytest.raises(AIServiceResponseError, match="gradcam_path"):
        asyncio.run(
            request_prediction(
                image_bytes=b"image",
                filename="exam.png",
                content_type="image/png",
                exam_type="colonoscopy",
            )
        )


def test_client_rejects_class_label_mismatch(monkeypatch):
    invalid = dict(VALID_RESPONSE, prediction_class=0, label="abnormal")
    monkeypatch.setattr(
        ai_client.httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            response=StubResponse(payload=invalid),
            **kwargs,
        ),
    )

    with pytest.raises(AIServiceResponseError, match="catálogo"):
        asyncio.run(
            request_prediction(
                image_bytes=b"image",
                filename="exam.png",
                content_type="image/png",
                exam_type="colonoscopy",
            )
        )


def test_client_requires_gradcam_for_gastrointestinal(monkeypatch):
    invalid = dict(VALID_RESPONSE, gradcam_available=False, gradcam_path=None)
    monkeypatch.setattr(
        ai_client.httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            response=StubResponse(payload=invalid),
            **kwargs,
        ),
    )

    with pytest.raises(AIServiceResponseError, match="gastrointestinal"):
        asyncio.run(
            request_prediction(
                image_bytes=b"image",
                filename="exam.png",
                content_type="image/png",
                exam_type="colonoscopy",
            )
        )


def test_analyze_exam_sends_type_and_persists_model_contract(tmp_path, monkeypatch):
    image_path = tmp_path / "exam.png"
    image_path.write_bytes(b"validated-image")
    exam = SimpleNamespace(
        id=17,
        ai_analysis=None,
        status=SimpleNamespace(name="processing"),
        file_path=str(image_path),
        file_name="exam.png",
        file_mime_type="image/png",
        exam_type="colonoscopy",
    )
    current_user = SimpleNamespace(id=9)
    captured = {}

    monkeypatch.setattr(exam_service, "get_exam_model_by_id", lambda **_kwargs: exam)
    monkeypatch.setattr(exam_service, "ensure_user_can_access_exam", lambda **_kwargs: None)
    monkeypatch.setattr(exam_service, "get_transition_target", lambda *_args, **_kwargs: "awaiting_review")
    monkeypatch.setattr(exam_service, "resolve_safe_exam_file_path", lambda _path: Path(image_path))
    monkeypatch.setattr(exam_service, "claim_exam_for_analysis", lambda **_kwargs: None)

    async def fake_request_prediction(**kwargs):
        captured["request"] = kwargs
        return dict(VALID_RESPONSE)

    def fake_create_ai_analysis(*, payload, **_kwargs):
        captured["payload"] = payload
        return payload.model_dump()

    monkeypatch.setattr(exam_service, "request_prediction", fake_request_prediction)
    monkeypatch.setattr(exam_service, "create_ai_analysis", fake_create_ai_analysis)

    result = asyncio.run(
        exam_service.analyze_exam(
            db=SimpleNamespace(),
            exam_id=exam.id,
            current_user=current_user,
        )
    )

    assert captured["request"]["exam_type"] == "colonoscopy"
    payload = captured["payload"]
    assert payload.prediction_class == 1
    assert payload.prediction_label == "abnormal"
    assert payload.confidence == pytest.approx(0.9342)
    assert payload.model_name == "ensemble_stacking"
    assert payload.model_version == "models-v0.1.0"
    assert payload.gradcam_path == "/app/storage/gradcam/example.jpg"
    assert result["model_name"] == "ensemble_stacking"
