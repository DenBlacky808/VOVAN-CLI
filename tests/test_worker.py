from __future__ import annotations

from pathlib import Path

from vovan.config import Settings
from vovan.worker import run_worker


class FakeClientNoJob:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    def claim_next_job(self):
        return {"status": "ok", "job": None}


class FakeClientSuccess:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.failed = False

    def claim_next_job(self):
        return {"status": "ok", "job": {"id": 1, "filename": "doc.pdf"}}

    def download_job_file(self, job_id, download_dir, filename):
        download_dir.mkdir(parents=True, exist_ok=True)
        p = download_dir / "doc.pdf"
        p.write_text("hello", encoding="utf-8")
        return {"status": "ok", "local_path": str(p)}

    def submit_result(self, job_id, result):
        return {"status": "ok", "data": {"saved": True}}

    def submit_failure(self, job_id, reason, preflight=None):
        self.failed = True
        return {"status": "ok"}


class FakeClientPreflightFail(FakeClientSuccess):
    def download_job_file(self, job_id, download_dir, filename):
        download_dir.mkdir(parents=True, exist_ok=True)
        p = download_dir / "doc.exe"
        p.write_text("bad", encoding="utf-8")
        return {"status": "ok", "local_path": str(p)}


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        vladcher_base_url="https://api.example/",
        worker_token="token",
        mode="local",
        data_dir=tmp_path,
        log_dir=tmp_path / "logs",
        report_dir=tmp_path / "reports",
        download_dir=tmp_path / "downloads",
        allowed_extensions={".pdf", ".txt"},
        max_file_size_mb=1,
        request_timeout_seconds=30,
        worker_sleep_seconds=1,
        dry_run=False,
    )


def test_worker_no_job(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("vovan.worker.VladcherApiClient", FakeClientNoJob)
    result = run_worker(_settings(tmp_path), once=True)
    assert result["status"] == "ok"
    assert result["runs"][0]["result"] == "no_job"


def test_worker_success_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("vovan.worker.VladcherApiClient", FakeClientSuccess)
    result = run_worker(_settings(tmp_path), once=True)
    assert result["status"] == "ok"
    assert result["runs"][0]["result"] == "processed"


def test_worker_preflight_fail_submits_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("vovan.worker.VladcherApiClient", FakeClientPreflightFail)
    result = run_worker(_settings(tmp_path), once=True)
    assert result["status"] == "ok"
    assert result["runs"][0]["result"] == "failed_preflight"
    assert result["runs"][0]["submit_failure"]["status"] == "ok"
