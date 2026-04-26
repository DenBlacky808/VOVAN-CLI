from __future__ import annotations

import io
from urllib.error import HTTPError

from vovan.api_client import VladcherApiClient


class DummyResponse:
    def __init__(self, payload: bytes, status: int = 200):
        self._payload = payload
        self.status = status

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_dry_run_claim_does_not_call_http(monkeypatch) -> None:
    called = {"value": False}

    def fake_urlopen(*args, **kwargs):  # pragma: no cover
        called["value"] = True
        raise AssertionError("urlopen should not be called in dry-run")

    monkeypatch.setattr("vovan.api_client.urlopen", fake_urlopen)
    client = VladcherApiClient(base_url="https://example.test", worker_token="token", dry_run=True)

    result = client.claim_next_job()

    assert result["status"] == "dry-run"
    assert called["value"] is False


def test_authorization_header_is_attached(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["auth"] = request.headers.get("Authorization")
        return DummyResponse(b'{"job": null}', 200)

    monkeypatch.setattr("vovan.api_client.urlopen", fake_urlopen)
    client = VladcherApiClient(base_url="https://example.test", worker_token="secret-token", dry_run=False)

    result = client.claim_next_job()

    assert result["status"] == "ok"
    assert captured["auth"] == "Bearer secret-token"


def test_http_errors_are_structured(monkeypatch) -> None:
    def fake_urlopen_401(request, timeout):
        raise HTTPError(request.full_url, 401, "Unauthorized", hdrs=None, fp=io.BytesIO(b""))

    monkeypatch.setattr("vovan.api_client.urlopen", fake_urlopen_401)
    client = VladcherApiClient(base_url="https://example.test", worker_token="token", dry_run=False)
    unauthorized = client.claim_next_job()
    assert unauthorized["status"] == "error"
    assert unauthorized["error"]["kind"] == "unauthorized"

    def fake_urlopen_409(request, timeout):
        raise HTTPError(request.full_url, 409, "Conflict", hdrs=None, fp=io.BytesIO(b""))

    monkeypatch.setattr("vovan.api_client.urlopen", fake_urlopen_409)
    conflict = client.claim_next_job()
    assert conflict["status"] == "error"
    assert conflict["error"]["kind"] == "conflict"

    def fake_urlopen_500(request, timeout):
        raise HTTPError(request.full_url, 500, "ServerError", hdrs=None, fp=io.BytesIO(b""))

    monkeypatch.setattr("vovan.api_client.urlopen", fake_urlopen_500)
    server_error = client.claim_next_job()
    assert server_error["status"] == "error"
    assert server_error["error"]["kind"] == "server_error"
