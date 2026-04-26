from pathlib import Path

from vovan.config import Settings
from vovan.worker import run_worker


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        vladcher_base_url="https://worker.example",
        worker_token="token",
        mode="local",
        data_dir=tmp_path,
        log_dir=Path("./logs"),
        report_dir=Path("./reports"),
        allowed_extensions={".pdf", ".png", ".jpg", ".jpeg"},
        max_file_size_mb=1,
        dry_run=False,
    )


def test_worker_uses_job_id_from_claim_result(tmp_path, monkeypatch) -> None:
    from vovan import worker as worker_module

    settings = _settings(tmp_path)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": "42", "original_filename": "scan.pdf"}

        def download_job_file(self, job_id):
            assert job_id == "42"
            return {"content": b"%PDF-1.7 mock"}

        def submit_result(self, job_id, result_text):
            return {"ok": True, "job_id": job_id, "result_text": result_text}

        def submit_failure(self, job_id, error_message):
            raise AssertionError("submit_failure should not be called")

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)

    assert result["status"] == "ok"
    assert result["job_id"] == "42"
    downloaded = Path(result["downloaded_file"])
    assert downloaded.suffix == ".pdf"
    assert downloaded.name == "scan.pdf"
    assert result["preflight"]["extension"] == ".pdf"
    assert result["preflight"]["suitable_for_ocr"] is True


def test_worker_prefers_job_id_then_id_fallback(monkeypatch, tmp_path) -> None:
    from vovan import worker as worker_module

    settings = _settings(tmp_path)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": "primary", "id": "fallback", "original_filename": "scan.pdf"}

        def download_job_file(self, job_id):
            return {"content": b"fake-pdf"}

        def submit_result(self, job_id, result_text):
            return {"ok": True}

        def submit_failure(self, job_id, error_message):
            return {"ok": False}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)
    assert result["job_id"] == "primary"

    class FakeClientFallback:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"id": "fallback-only", "original_filename": "image.png"}

        def download_job_file(self, job_id):
            return {"content": b"fake-png"}

        def submit_result(self, job_id, result_text):
            return {"ok": True}

        def submit_failure(self, job_id, error_message):
            return {"ok": False}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClientFallback)
    result_fallback = run_worker(settings)
    assert result_fallback["job_id"] == "fallback-only"


def test_worker_sanitizes_unsafe_original_filename(monkeypatch, tmp_path) -> None:
    from vovan import worker as worker_module

    settings = _settings(tmp_path)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": "777", "original_filename": "../../bad dir/../evil?.pdf"}

        def download_job_file(self, job_id):
            return {"content": b"fake-pdf"}

        def submit_result(self, job_id, result_text):
            return {"ok": True}

        def submit_failure(self, job_id, error_message):
            raise AssertionError("submit_failure should not be called")

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)
    assert Path(result["downloaded_file"]).name == "evil_.pdf"


def test_worker_fallback_filename_without_original_filename_is_pdf(monkeypatch, tmp_path) -> None:
    from vovan import worker as worker_module

    settings = _settings(tmp_path)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": 9}

        def download_job_file(self, job_id):
            return {"content": b"fallback-content"}

        def submit_result(self, job_id, result_text):
            return {"ok": True}

        def submit_failure(self, job_id, error_message):
            raise AssertionError("submit_failure should not be called")

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)
    assert Path(result["downloaded_file"]).name == "job_9.pdf"
    assert result["preflight"]["extension"] == ".pdf"


def test_worker_preflight_failure_submits_fail(monkeypatch, tmp_path) -> None:
    from vovan import worker as worker_module

    settings = _settings(tmp_path)
    settings.allowed_extensions = {".pdf"}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": "bad", "original_filename": "scan.png"}

        def download_job_file(self, job_id):
            return {"content": b"png"}

        def submit_result(self, job_id, result_text):
            raise AssertionError("submit_result should not be called")

        def submit_failure(self, job_id, error_message):
            return {"ok": True, "job_id": job_id, "error": error_message}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)
    assert result["status"] == "error"
    assert result["preflight"]["extension"] == ".png"
    assert result["fail_result"]["ok"] is True
