from __future__ import annotations

import re
from pathlib import Path

from vovan.api_client import VladcherApiClient
from vovan.config import Settings, validate_required_env
from vovan.ocr import run_placeholder_ocr
from vovan.preflight import run_preflight


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

    claim = client.claim_next_job()
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

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    local_file = _download_to_local_file(client, settings, str(job_id), claim)
    preflight = run_preflight(str(local_file), settings)

    if not preflight["suitable_for_ocr"]:
        error_message = "Preflight failed: file is not suitable for OCR"
        fail_result = client.submit_failure(str(job_id), error_message)
        status_result = client.get_job_status(str(job_id))
        return {
            "status": "ok",
            "mode": settings.mode,
            "dry_run": settings.dry_run,
            "claim_result": claim,
            "job_id": job_id,
            "source_file": str(local_file),
            "preflight": preflight,
            "fail_result": fail_result,
            "job_status": status_result,
            "message": error_message,
        }

    ocr = run_placeholder_ocr(str(local_file))
    complete_result = client.submit_result(str(job_id), ocr["result_text"])
    status_result = client.get_job_status(str(job_id))

    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "claim_result": claim,
        "job_id": job_id,
        "source_file": str(local_file),
        "preflight": preflight,
        "ocr": ocr,
        "complete_result": complete_result,
        "job_status": status_result,
    }


def _download_to_local_file(
    client: VladcherApiClient,
    settings: Settings,
    job_id: str,
    claim_payload: dict | None = None,
) -> Path:
    destination = settings.data_dir / f"job_{job_id}{_resolve_download_extension(job_id, claim_payload)}"
    payload = client.download_job_file(job_id)

    if isinstance(payload, bytes):
        destination.write_bytes(payload)
    else:
        destination.write_text("dry-run placeholder input", encoding="utf-8")

    return destination


def _resolve_download_extension(job_id: str, claim_payload: dict | None = None) -> str:
    fallback_name = f"job_{job_id}.pdf"
    if not isinstance(claim_payload, dict):
        return Path(fallback_name).suffix

    original_filename = claim_payload.get("original_filename")
    if not isinstance(original_filename, str):
        return Path(fallback_name).suffix

    candidate = _sanitize_filename(original_filename)
    if not candidate:
        return Path(fallback_name).suffix

    extension = Path(candidate).suffix.lower()
    if not extension or extension == ".":
        return Path(fallback_name).suffix

    return extension


def _sanitize_filename(value: str) -> str:
    basename = value.replace("\\", "/").split("/")[-1].strip()
    if not basename:
        return ""

    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", basename)
    sanitized = sanitized.lstrip(".")

    if not sanitized or set(sanitized) == {"."}:
        return ""

    return sanitized


def list_jobs(settings: Settings) -> dict:
    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "jobs": [],
        "message": "jobs endpoint placeholder",
    }
