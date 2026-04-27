from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Callable

from vovan.api_client import VladcherApiClient
from vovan.config import Settings, validate_required_env
from vovan.ocr import run_ocr
from vovan.preflight import run_preflight

try:  # pypdf is intentionally optional at runtime.
    from pypdf import PdfReader
except Exception:  # pragma: no cover - import behavior depends on environment
    PdfReader = None  # type: ignore[assignment]


PDF_MVP_PLACEHOLDER = "PDF accepted; scanned-page OCR is not enabled in MVP"
PDF_SUFFIX = ".pdf"


def run_worker(settings: Settings) -> dict:
    missing = validate_required_env(settings)
    if missing:
        return {
            "status": "error",
            "message": f"Missing required env vars: {', '.join(missing)}",
        }

    client = VladcherApiClient(
        base_url=settings.vladcher_base_url,
        worker_token=settings.worker_token,
        dry_run=settings.dry_run,
    )

    try:
        claim = client.claim_next_job()
    except Exception as exc:
        return _worker_api_error(settings, "Claim job request failed", exc)

    if claim is None:
        return {
            "status": "ok",
            "mode": settings.mode,
            "dry_run": settings.dry_run,
            "message": "No job available",
            "claim_result": None,
        }

    job_id = claim.get("job_id") or claim.get("id")
    if not job_id:
        if settings.dry_run:
            return {
                "status": "ok",
                "mode": settings.mode,
                "dry_run": settings.dry_run,
                "message": "Dry-run claim preview (no job_id in mocked response)",
                "claim_result": claim,
            }
        return {
            "status": "error",
            "mode": settings.mode,
            "dry_run": settings.dry_run,
            "message": "Claimed job payload missing job_id",
            "claim_result": claim,
        }

    job_id = str(job_id)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    try:
        local_file = _download_to_local_file(client, settings, job_id, claim)
    except Exception as exc:
        return _worker_api_error(settings, "Download job file request failed", exc, job_id=job_id)

    preflight = run_preflight(str(local_file), settings)

    if not preflight["suitable_for_ocr"]:
        result_payload = _build_failed_payload(
            job_id,
            "Preflight failed: file is not suitable for OCR",
            ["Downloaded file did not pass local OCR preflight checks."],
        )
    else:
        job = {
            "job_id": job_id,
            "file_path": local_file,
            "claim": claim,
            "settings": settings,
        }
        if _is_pdf_job_file(local_file):
            result_payload = process_pdf_job(job)
        else:
            result_payload = process_image_job(job, settings)

    if result_payload["status"] == "failed":
        try:
            fail_result = client.submit_failure(job_id, result_payload)
        except Exception as exc:
            return _worker_api_error(settings, "Submit failure request failed", exc, job_id=job_id)
        status_result = _safe_job_status(client, job_id)
        return {
            "status": "ok",
            "mode": settings.mode,
            "dry_run": settings.dry_run,
            "claim_result": claim,
            "job_id": job_id,
            "preflight": preflight,
            "result_payload": result_payload,
            "fail_result": fail_result,
            "job_status": status_result,
            "message": result_payload["safe_error"],
        }

    try:
        complete_result = client.submit_result(job_id, result_payload)
    except Exception as exc:
        return _worker_api_error(settings, "Submit completed result request failed", exc, job_id=job_id)
    status_result = _safe_job_status(client, job_id)

    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "claim_result": claim,
        "job_id": job_id,
        "preflight": preflight,
        "result_payload": result_payload,
        "ocr_engine": result_payload.get("ocr_engine", settings.ocr_engine),
        "complete_result": complete_result,
        "job_status": status_result,
    }


def run_worker_loop(
    settings: Settings,
    sleep_func: Callable[[float], None] = time.sleep,
    log_func: Callable[[str], None] = print,
    max_iterations: int | None = None,
) -> dict:
    iterations = 0
    try:
        while True:
            try:
                result = run_worker(settings)
            except Exception as exc:  # Defensive guard for daemon mode.
                result = {
                    "status": "error",
                    "mode": settings.mode,
                    "dry_run": settings.dry_run,
                    "message": sanitize_worker_error(exc),
                }

            iterations += 1
            _log_worker_iteration(result, log_func)

            if max_iterations is not None and iterations >= max_iterations:
                return {
                    "status": "ok",
                    "message": "Worker loop stopped after max_iterations",
                    "iterations": iterations,
                    "last_result": result,
                }

            delay = (
                settings.worker_error_backoff_seconds
                if result.get("status") != "ok"
                else settings.worker_poll_seconds
            )
            sleep_func(max(0.0, delay))
    except KeyboardInterrupt:
        stopped = {
            "status": "ok",
            "message": "Worker stopped by Ctrl+C",
            "iterations": iterations,
        }
        _log_worker_iteration(stopped, log_func)
        return stopped


def inspect_pdf(file_path: str | Path) -> dict:
    path = Path(file_path)
    warnings: list[str] = []
    result = {
        "is_pdf": False,
        "is_valid_pdf": False,
        "page_count": None,
        "has_text_layer": None,
        "processing_warnings": warnings,
    }

    if not path.exists() or not path.is_file():
        warnings.append("PDF file is missing or is not a regular file.")
        return result

    if not _has_pdf_header(path):
        warnings.append("File header is not a PDF header.")
        return result

    result["is_pdf"] = True
    metadata = _read_pdf_text_metadata(path)
    result.update(
        {
            "is_valid_pdf": metadata["is_valid_pdf"],
            "page_count": metadata["page_count"],
            "has_text_layer": metadata["has_text_layer"],
        }
    )
    warnings.extend(metadata["processing_warnings"])
    return result


def extract_pdf_text_if_available(file_path: str | Path) -> dict:
    path = Path(file_path)
    metadata = _read_pdf_text_metadata(path)
    return {
        "extracted_text": metadata["extracted_text"],
        "page_count": metadata["page_count"],
        "has_text_layer": metadata["has_text_layer"],
        "processing_warnings": metadata["processing_warnings"],
    }


def fallback_pdf_ocr_placeholder(
    file_path: str | Path,
    job_id: str = "",
    page_count: int | None = None,
    has_text_layer: bool | None = False,
    processing_warnings: list[str] | None = None,
) -> dict:
    warnings = list(processing_warnings or [])
    if not any("scanned-page OCR" in warning for warning in warnings):
        warnings.append("No PDF text layer detected; scanned-page OCR is not enabled in MVP.")
    return _build_completed_payload(
        job_id=job_id,
        extracted_text=PDF_MVP_PLACEHOLDER,
        page_count=page_count,
        has_text_layer=has_text_layer,
        processing_warnings=warnings,
        worker_result_summary="PDF accepted as scanned/no-text; OCR placeholder returned.",
    )


def sanitize_worker_error(error: object) -> str:
    message = str(error) or error.__class__.__name__
    message = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [redacted]", message)
    message = re.sub(
        r"(?i)\b(token|secret|password|authorization)\b\s*[:=]\s*[^,\s]+",
        lambda match: f"{match.group(1)}=[redacted]",
        message,
    )
    message = re.sub(r"(?<!\w)/(?:Users|home|private|var|tmp)/[^\s'\"<>]+", "[local-path]", message)
    message = re.sub(r"[A-Za-z]:\\[^\s'\"<>]+", "[local-path]", message)
    message = " ".join(message.split())
    if not message:
        return "Worker failed safely"
    return message[:500]


def process_pdf_job(job: dict) -> dict:
    job_id = str(job.get("job_id") or "")
    file_path = Path(job.get("file_path") or job.get("local_file") or "")

    try:
        inspection = inspect_pdf(file_path)
        warnings = list(inspection["processing_warnings"])

        if not inspection["is_pdf"] or not inspection["is_valid_pdf"]:
            return _build_failed_payload(
                job_id,
                "PDF preflight failed: file is not a readable PDF",
                warnings,
            )

        if inspection["has_text_layer"]:
            text_result = extract_pdf_text_if_available(file_path)
            warnings.extend(text_result["processing_warnings"])
            return _build_completed_payload(
                job_id=job_id,
                extracted_text=text_result["extracted_text"],
                page_count=text_result["page_count"],
                has_text_layer=True,
                processing_warnings=_unique_warnings(warnings),
                worker_result_summary="PDF text layer extracted.",
            )

        return fallback_pdf_ocr_placeholder(
            file_path,
            job_id=job_id,
            page_count=inspection["page_count"],
            has_text_layer=inspection["has_text_layer"],
            processing_warnings=warnings,
        )
    except Exception as exc:
        return _build_failed_payload(job_id, exc, ["PDF job failed in controlled worker processing."])


def process_image_job(job: dict, settings: Settings | None = None) -> dict:
    job_id = str(job.get("job_id") or "")
    file_path = Path(job.get("file_path") or job.get("local_file") or "")
    active_settings = settings or job.get("settings")
    if active_settings is None:
        return _build_failed_payload(job_id, "Worker settings missing for image job", [])

    try:
        ocr = run_ocr(
            str(file_path),
            active_settings.ocr_engine,
            tesseract_lang=active_settings.tesseract_lang,
            pdf_max_pages=active_settings.pdf_max_pages,
            pdf_dpi=active_settings.pdf_dpi,
        )
    except Exception as exc:
        return _build_failed_payload(job_id, exc, ["Image job failed in controlled worker processing."])

    warnings = []
    if ocr.get("engine_warning"):
        warnings.append(sanitize_worker_error(ocr["engine_warning"]))

    return _build_completed_payload(
        job_id=job_id,
        extracted_text=ocr.get("result_text", ""),
        page_count=None,
        has_text_layer=None,
        processing_warnings=warnings,
        worker_result_summary=f"Image OCR completed with {ocr.get('engine', 'unknown')} engine.",
        extra={"ocr_engine": ocr.get("engine")},
    )


def _sanitize_original_filename(original_filename: str) -> str:
    basename = original_filename.replace("\\", "/").split("/")[-1].strip()
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", basename).strip(" .")
    if not sanitized or sanitized in {".", ".."} or set(sanitized) == {"."}:
        return ""
    if sanitized.startswith("."):
        sanitized = sanitized.lstrip(".")
    return sanitized


def _build_download_filename(job_id: str, claim_payload: dict | None) -> str:
    fallback = f"job_{job_id}.pdf"
    if not isinstance(claim_payload, dict):
        return fallback

    original_filename = claim_payload.get("original_filename")
    if not isinstance(original_filename, str) or not original_filename.strip():
        return fallback

    sanitized = _sanitize_original_filename(original_filename)
    return sanitized or fallback


def _download_to_local_file(
    client: VladcherApiClient,
    settings: Settings,
    job_id: str,
    claim_payload: dict | None = None,
) -> Path:
    destination = settings.data_dir / _build_download_filename(job_id, claim_payload)
    payload = client.download_job_file(job_id)

    if isinstance(payload, bytes):
        destination.write_bytes(payload)
    else:
        destination.write_text("dry-run placeholder input", encoding="utf-8")

    return destination


def _has_pdf_header(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except OSError:
        return False


def _is_pdf_job_file(path: Path) -> bool:
    return path.suffix.lower() == PDF_SUFFIX or _has_pdf_header(path)


def _read_pdf_text_metadata(path: Path) -> dict:
    warnings: list[str] = []
    result = {
        "is_valid_pdf": False,
        "page_count": None,
        "has_text_layer": None,
        "extracted_text": "",
        "processing_warnings": warnings,
    }

    if PdfReader is None:
        warnings.append("pypdf is not installed; PDF text-layer inspection is unavailable.")
        result["is_valid_pdf"] = _has_pdf_header(path)
        return result

    try:
        reader = _create_pdf_reader(path)
        pages = list(reader.pages)
    except Exception as exc:
        warnings.append(f"PDF structure could not be read: {sanitize_worker_error(exc)}")
        return result

    page_texts = []
    for page_number, page in enumerate(pages, start=1):
        try:
            page_text = (page.extract_text() or "").strip()
        except Exception as exc:
            warnings.append(f"PDF page {page_number} text layer could not be read: {sanitize_worker_error(exc)}")
            page_text = ""
        if page_text:
            page_texts.append((page_number, page_text))

    result["is_valid_pdf"] = True
    result["page_count"] = len(pages)
    result["has_text_layer"] = bool(page_texts)
    result["extracted_text"] = _join_pdf_page_texts(page_texts)
    return result


def _create_pdf_reader(path: Path):
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed")
    try:
        return PdfReader(str(path), strict=False)
    except TypeError:
        return PdfReader(str(path))


def _join_pdf_page_texts(page_texts: list[tuple[int, str]]) -> str:
    if not page_texts:
        return ""
    if len(page_texts) == 1:
        return page_texts[0][1]
    return "\n\n".join(f"--- page {page_number} ---\n{text}" for page_number, text in page_texts)


def _build_completed_payload(
    job_id: str,
    extracted_text: str,
    page_count: int | None,
    has_text_layer: bool | None,
    processing_warnings: list[str] | None,
    worker_result_summary: str,
    extra: dict | None = None,
) -> dict:
    payload = {
        "job_id": str(job_id),
        "status": "completed",
        "extracted_text": extracted_text,
        "result_text": extracted_text,
        "page_count": page_count,
        "has_text_layer": has_text_layer,
        "processing_warnings": _unique_warnings(processing_warnings or []),
        "worker_result_summary": worker_result_summary,
    }
    if extra:
        payload.update(extra)
    return payload


def _build_failed_payload(job_id: str, error: object, processing_warnings: list[str] | None = None) -> dict:
    safe_error = sanitize_worker_error(error)
    return {
        "job_id": str(job_id),
        "status": "failed",
        "safe_error": safe_error,
        "error_message": safe_error,
        "processing_warnings": _unique_warnings(processing_warnings or []),
    }


def _unique_warnings(warnings: list[str]) -> list[str]:
    unique = []
    for warning in warnings:
        if warning and warning not in unique:
            unique.append(warning)
    return unique


def _safe_job_status(client: VladcherApiClient, job_id: str) -> dict:
    try:
        return client.get_job_status(job_id)
    except Exception as exc:
        return {"ok": False, "safe_error": sanitize_worker_error(exc)}


def _worker_api_error(settings: Settings, message: str, error: object, job_id: str | None = None) -> dict:
    result = {
        "status": "error",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "message": message,
        "safe_error": sanitize_worker_error(error),
    }
    if job_id:
        result["job_id"] = job_id
    return result


def _log_worker_iteration(result: dict, log_func: Callable[[str], None]) -> None:
    event = {
        "status": result.get("status"),
        "message": result.get("message"),
    }
    if result.get("job_id"):
        event["job_id"] = result["job_id"]
    result_payload = result.get("result_payload")
    if isinstance(result_payload, dict):
        event["job_result_status"] = result_payload.get("status")
        event["worker_result_summary"] = result_payload.get("worker_result_summary")
    if result.get("claim_result") is None and result.get("message") == "No job available":
        event["worker_state"] = "idle"
    log_func(json.dumps(event, ensure_ascii=False, sort_keys=True))


def list_jobs(settings: Settings) -> dict:
    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "jobs": [],
        "message": "jobs endpoint placeholder",
    }
