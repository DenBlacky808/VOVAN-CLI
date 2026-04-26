from pathlib import Path

from vovan.config import Settings
from vovan.worker import run_worker


class StubClientNoJob:
    def claim_next_job(self):
        return {"job": None}


class StubClientSuccess:
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path

    def claim_next_job(self):
        return {"job": {"id": 7}}

    def download_job_file(self, job_id: str, download_dir: Path):
        sample = self.tmp_path / "job_7.pdf"
        sample.write_text("pdf", encoding="utf-8")
        return {"status": "ok", "file_path": str(sample)}

    def submit_result(self, job_id: str, result: dict):
        return {"status": "ok", "job_id": job_id, "accepted": True, "result_text": result.get("result_text")}


class StubClientPreflightFail:
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.failure_called = False

    def claim_next_job(self):
        return {"job": {"id": 8}}

    def download_job_file(self, job_id: str, download_dir: Path):
        bad = self.tmp_path / "job_8.exe"
        bad.write_text("bad", encoding="utf-8")
        return {"status": "ok", "file_path": str(bad)}

    def submit_failure(self, job_id: str, reason: str, details: dict | None = None):
        self.failure_called = True
        return {"status": "ok", "job_id": job_id, "reason": reason}


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        vladcher_base_url="https://example.test",
        worker_token="token",
        mode="local",
        data_dir=tmp_path,
        log_dir=tmp_path,
        report_dir=tmp_path,
        allowed_extensions={".pdf", ".txt"},
        max_file_size_mb=10,
        dry_run=False,
        request_timeout_seconds=30,
        worker_sleep_seconds=5,
        download_dir=tmp_path / "downloads",
    )


def test_worker_handles_no_job(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("vovan.worker.VladcherApiClient", lambda *args, **kwargs: StubClientNoJob())
    result = run_worker(_settings(tmp_path))
    assert result["status"] == "ok"
    assert result["result"] == "no_job"


def test_worker_success_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("vovan.worker.VladcherApiClient", lambda *args, **kwargs: StubClientSuccess(tmp_path))
    result = run_worker(_settings(tmp_path))
    assert result["status"] == "ok"
    assert result["result"] == "completed"
    assert result["job_id"] == "7"
    assert result["complete_submit"]["accepted"] is True


def test_worker_preflight_fail_submits_failure(monkeypatch, tmp_path: Path) -> None:
    stub = StubClientPreflightFail(tmp_path)
    monkeypatch.setattr("vovan.worker.VladcherApiClient", lambda *args, **kwargs: stub)
    result = run_worker(_settings(tmp_path))
    assert result["status"] == "ok"
    assert result["result"] == "failed_preflight"
    assert stub.failure_called is True
