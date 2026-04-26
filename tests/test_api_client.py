from __future__ import annotations

import io
import json
from pathlib import Path
from urllib import error

from vovan.api_client import VladcherApiClient


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.status = status
        self._bytes = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._bytes

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeBinaryResponse:
    def __init__(self, content: bytes, status: int = 200) -> None:
        self.status = status
        self._content = content

    def read(self) -> bytes:
        return self._content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_dry_run_claim_does_not_call_http(monkeypatch) -> None:
    client = VladcherApiClient(base_url="https://x/", worker_token="tok", dry_run=True)

    def _raise(*args, **kwargs):
        raise AssertionError("urlopen should not be called in dry-run")

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    result = client.claim_next_job()
    assert result["status"] == "dry-run"


def test_authorization_header_sent(monkeypatch) -> None:
    captured = {}

    def _fake_urlopen(req, timeout=0):
        captured["authorization"] = req.get_header("Authorization")
        return FakeResponse({"job": None})

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    client = VladcherApiClient(base_url="https://api.example/", worker_token="secret", dry_run=False)
    client.claim_next_job()
    assert captured["authorization"] == "Bearer secret"


def test_structured_http_errors(monkeypatch) -> None:
    def _http_401(req, timeout=0):
        raise error.HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b""))

    def _http_409(req, timeout=0):
        raise error.HTTPError(req.full_url, 409, "Conflict", {}, io.BytesIO(b""))

    def _http_500(req, timeout=0):
        raise error.HTTPError(req.full_url, 500, "Server Error", {}, io.BytesIO(b""))

    client = VladcherApiClient(base_url="https://api.example/", worker_token="secret", dry_run=False)

    monkeypatch.setattr("urllib.request.urlopen", _http_401)
    assert client.claim_next_job()["error"]["type"] == "unauthorized"

    monkeypatch.setattr("urllib.request.urlopen", _http_409)
    assert client.claim_next_job()["error"]["type"] == "conflict"

    monkeypatch.setattr("urllib.request.urlopen", _http_500)
    assert client.claim_next_job()["error"]["type"] == "server_error"


def test_download_job_file_success(monkeypatch, tmp_path: Path) -> None:
    def _fake_urlopen(req, timeout=0):
        return FakeBinaryResponse(b"PDF")

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    client = VladcherApiClient(base_url="https://api.example/", worker_token="secret", dry_run=False)
    result = client.download_job_file("1", tmp_path, "a.pdf")
    assert result["status"] == "ok"
    assert Path(result["local_path"]).read_bytes() == b"PDF"
