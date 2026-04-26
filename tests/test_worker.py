from pathlib import Path

from vovan.config import Settings
from vovan.worker import run_worker


def _settings() -> Settings:
    return Settings(
        vladcher_base_url="https://worker.example",
        worker_token="token",
        mode="local",
        data_dir=Path("./data"),
        log_dir=Path("./logs"),
        report_dir=Path("./reports"),
        allowed_extensions={".txt"},
        max_file_size_mb=1,
        dry_run=True,
    )


def test_worker_uses_job_id_from_claim_result() -> None:
    settings = _settings()

    result = run_worker(settings)

    # dry-run client returns request contract, so no claimed job id in this path
    assert result["status"] == "ok"
    assert result["claim_result"]["path"] == "/api/vovan/ocr/jobs/next/"


def test_worker_prefers_job_id_then_id_fallback(monkeypatch) -> None:
    from vovan import worker as worker_module

    settings = _settings()

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": "primary", "id": "fallback"}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)
    assert result["job_id"] == "primary"

    class FakeClientFallback:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"id": "fallback-only"}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClientFallback)
    result_fallback = run_worker(settings)
    assert result_fallback["job_id"] == "fallback-only"
