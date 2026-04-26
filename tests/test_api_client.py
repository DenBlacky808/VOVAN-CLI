from pathlib import Path

import pytest

from vovan.api_client import ApiError, VladcherApiClient


def test_dry_run_does_not_make_http_calls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = VladcherApiClient(base_url="https://example.test", worker_token="token", dry_run=True)

    def boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("HTTP should not be called in dry-run")

    monkeypatch.setattr(client, "_request_json", boom)

    claim = client.claim_next_job()
    download = client.download_job_file("1", tmp_path)
    submit = client.submit_result("1", {"result_text": "ok"})

    assert claim and claim["status"] == "dry-run"
    assert download["status"] == "dry-run"
    assert submit["status"] == "dry-run"


def test_authorization_header_is_bearer_token() -> None:
    client = VladcherApiClient(base_url="https://example.test", worker_token="abc123", dry_run=False)
    headers = client._headers()
    assert headers["Authorization"] == "Bearer abc123"


@pytest.mark.parametrize(
    ("status_code", "code", "retryable"),
    [
        (401, "unauthorized", False),
        (409, "conflict", False),
        (500, "server_error", True),
    ],
)
def test_structured_http_errors(status_code: int, code: str, retryable: bool) -> None:
    client = VladcherApiClient(base_url="https://example.test", worker_token="abc", dry_run=False)

    with pytest.raises(ApiError) as exc_info:
        client._raise_http_error(status_code, "{}")

    err = exc_info.value
    assert err.code == code
    assert err.http_status == status_code
    assert err.retryable is retryable
