from __future__ import annotations

from pathlib import Path

from vovan.api_client import ApiClientError
from vovan.config import Settings
from vovan.worker import run_worker


def _settings(tmp_path: Path, dry_run: bool = False) -> Settings:
    return Settings(
        vladcher_base_url="https://api.example",
        worker_token="token",
        mode="local",
        data_dir=tmp_path,
        log_dir=tmp_path,
        report_dir=tmp_path,
        allowed_extensions={".pdf", ".txt"},
        max_file_size_mb=1,
        dry_run=dry_run,
        request_timeout_seconds=30,
        worker_sleep_seconds=5,
        download_dir=tmp_path / "downloads",
    )


def test_no_job_handled(monkeypatch, tmp_path: Path) -> None:
    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def claim_next_job(self):
            return None

    monkeypatch.setattr("vovan.worker.VladcherApiClient", FakeClient)
    result = run_worker(_settings(tmp_path), once=True)
    assert result["status"] == "ok"
    assert result["result"] == "no_job"


def test_successful_flow(monkeypatch, tmp_path: Path) -> None:
    sample_pdf = tmp_path / "downloads" / "job_1.pdf"
    sample_pdf.parent.mkdir(parents=True, exist_ok=True)
    sample_pdf.write_text("demo", encoding="utf-8")

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def claim_next_job(self):
            return {"id": 1}

        def download_job_file(self, job_id: str):
            return {"status": "downloaded", "job_id": job_id, "local_path": str(sample_pdf)}

        def submit_result(self, _job_id: str, _result: dict):
            return {"status": "done"}

        def submit_failure(self, _job_id: str, _error: str, context=None):
            return {"status": "failed", "context": context}

    monkeypatch.setattr("vovan.worker.VladcherApiClient", FakeClient)
    result = run_worker(_settings(tmp_path), once=True)
    assert result["status"] == "ok"
    assert result["result"] == "completed"
    assert result["submit_result"]["status"] == "done"


def test_preflight_fail_submits_failure(monkeypatch, tmp_path: Path) -> None:
    sample_bad = tmp_path / "downloads" / "job_2.exe"
    sample_bad.parent.mkdir(parents=True, exist_ok=True)
    sample_bad.write_text("x", encoding="utf-8")

    called = {"failure": False}

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def claim_next_job(self):
            return {"id": 2}

        def download_job_file(self, job_id: str):
            return {"status": "downloaded", "job_id": job_id, "local_path": str(sample_bad)}

        def submit_result(self, _job_id: str, _result: dict):
            return {"status": "done"}

        def submit_failure(self, _job_id: str, _error: str, context=None):
            called["failure"] = True
            return {"status": "failed", "context": context}

    monkeypatch.setattr("vovan.worker.VladcherApiClient", FakeClient)
    result = run_worker(_settings(tmp_path), once=True)
    assert result["result"] == "failed_preflight"
    assert called["failure"] is True


def test_structured_api_errors(monkeypatch, tmp_path: Path) -> None:
    for code, category in [(401, "unauthorized"), (409, "conflict"), (503, "server_error")]:
        class FakeClient:
            def __init__(self, **_kwargs):
                pass

            def claim_next_job(self):
                raise ApiClientError("boom", category=category, status_code=code, retryable=code >= 500)

        monkeypatch.setattr("vovan.worker.VladcherApiClient", FakeClient)
        result = run_worker(_settings(tmp_path), once=True)
        assert result["status"] == "error"
        assert result["error"]["category"] == category
        assert result["error"]["status_code"] == code
