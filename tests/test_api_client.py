from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from urllib import error

from vovan.api_client import ApiClientError, VladcherApiClient


class DummyResponse:
    def __init__(self, payload: bytes, headers: dict[str, str] | None = None) -> None:
        self._payload = payload
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyOpener:
    def __init__(self, fn):
        self.fn = fn

    def open(self, req, timeout=0):
        return self.fn(req, timeout)


def test_dry_run_does_not_call_http() -> None:
    def _fail(_req, _timeout):
        raise AssertionError("HTTP should not be called in dry-run")

    client = VladcherApiClient(
        base_url="https://api.example",
        worker_token="token",
        dry_run=True,
        opener=DummyOpener(_fail),
    )

    assert client.claim_next_job() is None


def test_authorization_header_is_set(tmp_path: Path) -> None:
    captured = {}

    def _ok(req, _timeout):
        captured["auth"] = req.get_header("Authorization")
        return DummyResponse(json.dumps({"job": None}).encode("utf-8"))

    client = VladcherApiClient(
        base_url="https://api.example",
        worker_token="secret-token",
        dry_run=False,
        download_dir=tmp_path,
        opener=DummyOpener(_ok),
    )
    client.claim_next_job()
    assert captured["auth"] == "Bearer secret-token"


def test_http_error_structured() -> None:
    def _conflict(req, _timeout):
        raise error.HTTPError(req.full_url, 409, "Conflict", hdrs=None, fp=BytesIO(b'{"detail":"busy"}'))

    client = VladcherApiClient(
        base_url="https://api.example",
        worker_token="token",
        dry_run=False,
        opener=DummyOpener(_conflict),
    )

    try:
        client.claim_next_job()
        assert False, "expected error"
    except ApiClientError as exc:
        data = exc.to_dict()
        assert data["category"] == "conflict"
        assert data["status_code"] == 409


def test_invalid_json_structured() -> None:
    def _bad_json(_req, _timeout):
        return DummyResponse(b"not-json")

    client = VladcherApiClient(
        base_url="https://api.example",
        worker_token="token",
        dry_run=False,
        opener=DummyOpener(_bad_json),
    )

    try:
        client.claim_next_job()
        assert False, "expected error"
    except ApiClientError as exc:
        assert exc.category == "invalid_json"
