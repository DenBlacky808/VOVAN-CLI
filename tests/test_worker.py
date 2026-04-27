import json
from pathlib import Path

from vovan.config import Settings
from vovan.worker import (
    PDF_MVP_PLACEHOLDER,
    _build_download_filename,
    _download_to_local_file,
    inspect_pdf,
    process_pdf_job,
    run_worker,
    run_worker_loop,
    sanitize_worker_error,
)


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


class _FakePdfPage:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        return self.text


def _pdf_header(path: Path) -> None:
    path.write_bytes(b"%PDF-1.4\n% test fixture\n")


def test_worker_uses_job_id_from_claim_result() -> None:
    settings = _settings()

    result = run_worker(settings)

    # dry-run client returns request contract, so no claimed job id in this path
    assert result["status"] == "ok"
    assert result["claim_result"]["path"] == "/api/vovan/ocr/jobs/next/"


def test_worker_prefers_job_id_then_id_fallback(monkeypatch) -> None:
    from vovan import worker as worker_module

    settings = _settings()
    settings.allowed_extensions = {".png"}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": "primary", "id": "fallback", "original_filename": "scan.png"}

        def download_job_file(self, job_id: str):
            return b"ok"

        def submit_result(self, job_id: str, result_payload: dict):
            return {"ok": True}

        def submit_failure(self, job_id: str, error_payload: dict):
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
            return {"id": "fallback-only", "original_filename": "scan.png"}

        def download_job_file(self, job_id: str):
            return b"ok"

        def submit_result(self, job_id: str, result_payload: dict):
            return {"ok": True}

        def submit_failure(self, job_id: str, error_payload: dict):
            return {"ok": True}

        def get_job_status(self, job_id: str):
            return {"ok": True}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClientFallback)
    result_fallback = run_worker(settings)
    assert result_fallback["job_id"] == "fallback-only"


def test_worker_full_mocked_image_flow_complete(monkeypatch, tmp_path: Path) -> None:
    from vovan import worker as worker_module

    settings = _settings()
    settings.data_dir = tmp_path
    settings.allowed_extensions = {".png"}
    settings.max_file_size_mb = 1
    settings.dry_run = False

    call_order = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            call_order.append("claim")
            return {"job_id": "42", "original_filename": "scan.png"}

        def download_job_file(self, job_id: str):
            call_order.append("download")
            assert job_id == "42"
            return b"hello from api"

        def submit_result(self, job_id: str, result_payload: dict):
            call_order.append("complete")
            assert job_id == "42"
            assert result_payload["status"] == "completed"
            assert result_payload["extracted_text"] == "placeholder OCR result"
            assert result_payload["result_text"] == "placeholder OCR result"
            return {"ok": True}

        def submit_failure(self, job_id: str, error_payload: dict):
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
    assert result["result_payload"]["extracted_text"] == "placeholder OCR result"
    assert result["result_payload"]["ocr_engine"] == "placeholder"
    assert result["ocr_engine"] == "placeholder"
    assert result["complete_result"] == {"ok": True}
    assert call_order == ["claim", "download", "complete", "status"]


def test_worker_unsupported_engine_falls_back_safely(monkeypatch, tmp_path: Path) -> None:
    from vovan import worker as worker_module

    settings = _settings()
    settings.data_dir = tmp_path
    settings.allowed_extensions = {".png"}
    settings.max_file_size_mb = 1
    settings.dry_run = False
    settings.ocr_engine = "unknown-engine"

    captured_payload = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": "88", "original_filename": "scan.png"}

        def download_job_file(self, job_id: str):
            return b"hello from api"

        def submit_result(self, job_id: str, result_payload: dict):
            captured_payload.update(result_payload)
            return {"ok": True}

        def submit_failure(self, job_id: str, error_payload: dict):
            return {"ok": True}

        def get_job_status(self, job_id: str):
            return {"ok": True, "status": "completed"}

    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)
    result = run_worker(settings)
    assert result["status"] == "ok"
    assert result["ocr_engine"] == "placeholder"
    assert captured_payload["extracted_text"] == "placeholder OCR result"
    assert captured_payload["processing_warnings"]


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

        def submit_result(self, job_id: str, result_payload: dict):
            call_order.append("complete")
            return {"ok": True}

        def submit_failure(self, job_id: str, error_payload: dict):
            call_order.append("fail")
            assert "Preflight failed" in error_payload["error_message"]
            assert error_payload["safe_error"] == error_payload["error_message"]
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


def test_inspect_pdf_rejects_fake_pdf(tmp_path: Path) -> None:
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_text("not actually a pdf", encoding="utf-8")

    result = inspect_pdf(fake_pdf)

    assert result["is_pdf"] is False
    assert result["is_valid_pdf"] is False
    assert "PDF header" in result["processing_warnings"][0]


def test_minimal_pdf_failure_is_controlled(monkeypatch, tmp_path: Path) -> None:
    from vovan import worker as worker_module

    minimal_pdf = tmp_path / "minimal.pdf"
    _pdf_header(minimal_pdf)

    class BrokenPdfReader:
        def __init__(self, *args, **kwargs):
            raise ValueError(f"cannot read /Users/local/private/{minimal_pdf.name} token=secret")

    monkeypatch.setattr(worker_module, "PdfReader", BrokenPdfReader)

    result = process_pdf_job({"job_id": "pdf-1", "file_path": minimal_pdf})

    assert result["status"] == "failed"
    assert result["job_id"] == "pdf-1"
    serialized = json.dumps(result)
    assert "/Users/local/private" not in serialized
    assert "secret" not in serialized


def test_pdf_without_text_layer_returns_placeholder(monkeypatch, tmp_path: Path) -> None:
    from vovan import worker as worker_module

    pdf_path = tmp_path / "scan.pdf"
    _pdf_header(pdf_path)

    class BlankPdfReader:
        def __init__(self, *args, **kwargs):
            self.pages = [_FakePdfPage("")]

    monkeypatch.setattr(worker_module, "PdfReader", BlankPdfReader)

    result = process_pdf_job({"job_id": "pdf-2", "file_path": pdf_path})

    assert result["status"] == "completed"
    assert result["extracted_text"] == PDF_MVP_PLACEHOLDER
    assert result["page_count"] == 1
    assert result["has_text_layer"] is False
    assert "scanned-page OCR is not enabled" in " ".join(result["processing_warnings"])


def test_pdf_with_text_layer_extracts_text(monkeypatch, tmp_path: Path) -> None:
    from vovan import worker as worker_module

    pdf_path = tmp_path / "text.pdf"
    _pdf_header(pdf_path)

    class TextPdfReader:
        def __init__(self, *args, **kwargs):
            self.pages = [_FakePdfPage("hello text layer")]

    monkeypatch.setattr(worker_module, "PdfReader", TextPdfReader)

    result = process_pdf_job({"job_id": "pdf-3", "file_path": pdf_path})

    assert result["status"] == "completed"
    assert result["extracted_text"] == "hello text layer"
    assert result["page_count"] == 1
    assert result["has_text_layer"] is True


def test_sanitize_worker_error_removes_paths_and_auth_details() -> None:
    message = sanitize_worker_error(
        "failed at /Users/4ep/private/file.pdf with Authorization: Bearer abc123 and token=secret"
    )

    assert "/Users/4ep" not in message
    assert "abc123" not in message
    assert "secret" not in message
    assert "[redacted]" in message


def test_worker_loop_survives_api_error(monkeypatch) -> None:
    from vovan import worker as worker_module

    settings = _settings()
    settings.worker_poll_seconds = 1
    settings.worker_error_backoff_seconds = 9
    calls = []

    def fake_run_worker(settings: Settings):
        calls.append("run")
        if len(calls) == 1:
            return {"status": "error", "message": "temporary network error"}
        return {"status": "ok", "message": "No job available", "claim_result": None}

    sleeps = []
    logs = []
    monkeypatch.setattr(worker_module, "run_worker", fake_run_worker)

    result = run_worker_loop(
        settings,
        sleep_func=sleeps.append,
        log_func=logs.append,
        max_iterations=2,
    )

    assert result["status"] == "ok"
    assert len(calls) == 2
    assert sleeps == [9]
    assert any('"worker_state": "idle"' in line for line in logs)


def test_result_payload_does_not_publish_private_paths(monkeypatch, tmp_path: Path) -> None:
    from vovan import worker as worker_module

    settings = _settings()
    settings.data_dir = tmp_path
    settings.allowed_extensions = {".pdf"}
    settings.max_file_size_mb = 1
    settings.dry_run = False
    captured_payload = {}

    class BlankPdfReader:
        def __init__(self, *args, **kwargs):
            self.pages = [_FakePdfPage("")]

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def claim_next_job(self):
            return {"job_id": "123", "original_filename": "scan.pdf"}

        def download_job_file(self, job_id: str):
            return b"%PDF-1.4\n% fixture\n"

        def submit_result(self, job_id: str, result_payload: dict):
            captured_payload.update(result_payload)
            return {"ok": True}

        def submit_failure(self, job_id: str, error_payload: dict):
            return {"ok": False}

        def get_job_status(self, job_id: str):
            return {"ok": True, "status": "completed"}

    monkeypatch.setattr(worker_module, "PdfReader", BlankPdfReader)
    monkeypatch.setattr(worker_module, "VladcherApiClient", FakeClient)

    result = run_worker(settings)

    assert result["status"] == "ok"
    assert captured_payload["status"] == "completed"
    assert str(tmp_path) not in json.dumps(captured_payload)


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
