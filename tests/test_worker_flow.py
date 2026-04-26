from __future__ import annotations

from pathlib import Path

from vovan.config import Settings
from vovan.worker import run_worker


def _settings(tmp_path: Path, dry_run: bool = False) -> Settings:
    return Settings(
        vladcher_base_url="https://example.test",
        worker_token="token",
        mode="worker",
        data_dir=tmp_path,
        log_dir=tmp_path,
        report_dir=tmp_path,
        download_dir=tmp_path / "downloads",
        allowed_extensions={".pdf"},
        max_file_size_mb=5,
        dry_run=dry_run,
        request_timeout_seconds=30,
        worker_sleep_seconds=5,
    )


def test_no_job_is_handled(monkeypatch, tmp_path: Path) -> None:
    class FakeClient:
        def claim_next_job(self):
            return {"status": "ok", "job": None}

    monkeypatch.setattr("vovan.worker.VladcherApiClient", lambda **kwargs: FakeClient())

    result = run_worker(_settings(tmp_path))

    assert result["status"] == "ok"
    assert result["worker_status"] == "no_job"


def test_successful_mocked_flow(monkeypatch, tmp_path: Path) -> None:
    class FakeClient:
        def claim_next_job(self):
            return {"status": "ok", "job": {"id": 1}}

        def download_job_file(self, job_id: str, destination_dir: Path):
            destination_dir.mkdir(parents=True, exist_ok=True)
            path = destination_dir / f"job_{job_id}.pdf"
            path.write_bytes(b"%PDF-1.4")
            return {"status": "ok", "local_path": str(path)}

        def submit_result(self, job_id: str, result: dict):
            return {"status": "ok", "job_id": job_id, "echo": result}

    monkeypatch.setattr("vovan.worker.VladcherApiClient", lambda **kwargs: FakeClient())

    result = run_worker(_settings(tmp_path))

    assert result["status"] == "ok"
    assert result["worker_status"] == "completed"
    assert result["job_id"] == "1"
    assert result["completion"]["status"] == "ok"


def test_preflight_fail_calls_submit_failure(monkeypatch, tmp_path: Path) -> None:
    calls = {"failure_called": False}

    class FakeClient:
        def claim_next_job(self):
            return {"status": "ok", "job": {"id": 5}}

        def download_job_file(self, job_id: str, destination_dir: Path):
            destination_dir.mkdir(parents=True, exist_ok=True)
            path = destination_dir / "job_5.exe"
            path.write_bytes(b"not a pdf")
            return {"status": "ok", "local_path": str(path)}

        def submit_failure(self, job_id: str, reason: str, details: dict):
            calls["failure_called"] = True
            return {"status": "ok", "job_id": job_id, "reason": reason, "details": details}

    monkeypatch.setattr("vovan.worker.VladcherApiClient", lambda **kwargs: FakeClient())

    result = run_worker(_settings(tmp_path))

    assert result["status"] == "ok"
    assert result["worker_status"] == "failed"
    assert calls["failure_called"] is True
