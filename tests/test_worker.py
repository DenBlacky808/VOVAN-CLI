from pathlib import Path

from vovan.config import Settings
from vovan.worker import _build_download_filename, _download_to_local_file, run_worker


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
        ocr_engine="placeholder",
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

        def download_job_file(self, job_id: str):
            return b"ok"

        def submit_result(self, job_id: str, result_text: str):
            return {"ok": True}

        def submit_failure(self, job_id: str, error_message: str):
            return {"ok": True}

        def get_job_status(self, job_id: str):
            return {"ok": True}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)
    assert result["job_id"] == "primary"

    class FakeClientFallback:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"id": "fallback-only"}

        def download_job_file(self, job_id: str):
            return b"ok"

        def submit_result(self, job_id: str, result_text: str):
            return {"ok": True}

        def submit_failure(self, job_id: str, error_message: str):
            return {"ok": True}

        def get_job_status(self, job_id: str):
            return {"ok": True}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClientFallback)
    result_fallback = run_worker(settings)
    assert result_fallback["job_id"] == "fallback-only"


def test_worker_full_mocked_flow_complete(monkeypatch, tmp_path: Path) -> None:
    from vovan import worker as worker_module

    settings = _settings()
    settings.data_dir = tmp_path
    settings.allowed_extensions = {".pdf"}
    settings.max_file_size_mb = 1
    settings.dry_run = False

    call_order = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            call_order.append("claim")
            return {"job_id": "42", "original_filename": "scan.pdf"}

        def download_job_file(self, job_id: str):
            call_order.append("download")
            assert job_id == "42"
            return b"hello from api"

        def submit_result(self, job_id: str, result_text: str):
            call_order.append("complete")
            assert job_id == "42"
            assert result_text == "placeholder OCR result"
            return {"ok": True}

        def submit_failure(self, job_id: str, error_message: str):
            call_order.append("fail")
            return {"ok": True, "unexpected": True}

        def get_job_status(self, job_id: str):
            call_order.append("status")
            return {"ok": True, "status": "completed"}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)

    assert result["status"] == "ok"
    assert result["job_id"] == "42"
    assert result["preflight"]["suitable_for_ocr"] is True
    assert result["ocr_engine"] == "placeholder"
    assert result["ocr"]["result_text"] == "placeholder OCR result"
    assert result["complete_result"] == {"ok": True}
    assert call_order == ["claim", "download", "complete", "status"]


def test_worker_unsupported_engine_falls_back_safely(monkeypatch, tmp_path: Path) -> None:
    from vovan import worker as worker_module

    settings = _settings()
    settings.data_dir = tmp_path
    settings.allowed_extensions = {".pdf"}
    settings.max_file_size_mb = 1
    settings.dry_run = False
    settings.ocr_engine = "unknown-engine"

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": "42", "original_filename": "scan.pdf"}

        def download_job_file(self, job_id: str):
            return b"hello from api"

        def submit_result(self, job_id: str, result_text: str):
            assert result_text == "placeholder OCR result"
            return {"ok": True}

        def submit_failure(self, job_id: str, error_message: str):
            return {"ok": True}

        def get_job_status(self, job_id: str):
            return {"ok": True, "status": "completed"}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)
    assert result["status"] == "ok"
    assert result["ocr_engine"] == "placeholder"
    assert "unsupported OCR engine" in result["ocr"]["warning"]


def test_worker_preflight_failure_reports_fail(monkeypatch, tmp_path: Path) -> None:
    from vovan import worker as worker_module

    settings = _settings()
    settings.data_dir = tmp_path
    settings.allowed_extensions = {".pdf"}
    settings.max_file_size_mb = 1
    settings.dry_run = False

    call_order = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            call_order.append("claim")
            return {"job_id": "99", "original_filename": "scan.txt"}

        def download_job_file(self, job_id: str):
            call_order.append("download")
            return b"plain text"

        def submit_result(self, job_id: str, result_text: str):
            call_order.append("complete")
            return {"ok": True}

        def submit_failure(self, job_id: str, error_message: str):
            call_order.append("fail")
            assert "Preflight failed" in error_message
            return {"ok": True}

        def get_job_status(self, job_id: str):
            call_order.append("status")
            return {"ok": True, "status": "failed"}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)

    assert result["status"] == "ok"
    assert result["preflight"]["suitable_for_ocr"] is False
    assert result["fail_result"] == {"ok": True}
    assert "complete_result" not in result
    assert call_order == ["claim", "download", "fail", "status"]


def test_download_filename_prefers_claim_original_filename() -> None:
    assert _build_download_filename("42", {"original_filename": "scan.pdf"}) == "scan.pdf"


def test_download_filename_sanitizes_unsafe_original_filename() -> None:
    filename = _build_download_filename("42", {"original_filename": "../../bad dir/evil?.pdf"})
    assert filename == "evil_.pdf"
    assert "/" not in filename
    assert "\\" not in filename


def test_download_filename_falls_back_to_job_pdf() -> None:
    assert _build_download_filename("42", {}) == "job_42.pdf"
    assert _build_download_filename("42", {"original_filename": ""}) == "job_42.pdf"


def test_download_to_local_file_keeps_pdf_extension_for_preflight(tmp_path: Path) -> None:
    settings = _settings()
    settings.data_dir = tmp_path
    settings.allowed_extensions = {".pdf"}
    settings.dry_run = False

    class FakeClient:
        def download_job_file(self, job_id: str):
            return b"%PDF-1.4"

    local_file = _download_to_local_file(
        FakeClient(),
        settings,
        "77",
        {"original_filename": "scan.pdf"},
    )
    assert local_file.suffix == ".pdf"


def test_download_to_local_file_supports_live_bytes_payload(tmp_path: Path) -> None:
    settings = _settings()
    settings.data_dir = tmp_path
    settings.dry_run = False

    class FakeClient:
        def download_job_file(self, job_id: str):
            return b"live-bytes"

    local_file = _download_to_local_file(FakeClient(), settings, "11", {"original_filename": "scan.pdf"})
    assert local_file.read_bytes() == b"live-bytes"
