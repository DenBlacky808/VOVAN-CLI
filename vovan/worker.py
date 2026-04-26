from __future__ import annotations

import re
from pathlib import Path

from vovan.api_client import VladcherApiClient
from vovan.config import Settings, validate_required_env
from vovan.ocr import run_placeholder_ocr
from vovan.preflight import run_preflight


def _sanitize_download_basename(value: str) -> str:
    candidate = Path(value).name.strip()
    if not candidate:
        return ""
    normalized = re.sub(r"[^A-Za-z0-9._-]", "_", candidate)
    normalized = normalized.lstrip(".")
    return normalized


def _choose_download_filename(job_id: str, claim_payload: dict | None) -> str:
    if claim_payload:
        raw_original_filename = claim_payload.get("original_filename")
        if isinstance(raw_original_filename, str):
            sanitized = _sanitize_download_basename(raw_original_filename)
            if sanitized:
                return sanitized

    return f"job_{job_id}.pdf"


def _download_to_local_file(
    client: VladcherApiClient,
    settings: Settings,
    job_id: str,
    claim_payload: dict | None = None,
) -> Path:
    download = client.download_job_file(job_id)
    target_name = _choose_download_filename(job_id=job_id, claim_payload=claim_payload)
    target_path = settings.data_dir / target_name
    target_path.parent.mkdir(parents=True, exist_ok=True)

    content = download.get("content", b"")
    if isinstance(content, str):
        payload = content.encode("utf-8")
    elif isinstance(content, bytes):
        payload = content
    else:
        payload = b""
    target_path.write_bytes(payload)
    return target_path


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
    if job_id is None:
        return {
            "status": "error",
            "message": "Claimed job payload does not contain job_id/id",
            "claim_result": claim,
        }

    job_id_str = str(job_id)

    local_file = _download_to_local_file(
        client=client,
        settings=settings,
        job_id=job_id_str,
        claim_payload=claim,
    )
    preflight = run_preflight(str(local_file), settings)
    if not preflight["suitable_for_ocr"]:
        fail_result = client.submit_failure(job_id_str, "Preflight failed for downloaded job file")
        return {
            "status": "error",
            "mode": settings.mode,
            "dry_run": settings.dry_run,
            "job_id": job_id_str,
            "claim_result": claim,
            "downloaded_file": str(local_file),
            "preflight": preflight,
            "fail_result": fail_result,
        }

    ocr_result = run_placeholder_ocr(str(local_file))
    complete_result = client.submit_result(job_id_str, ocr_result["result_text"])

    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "claim_result": claim,
        "job_id": job_id_str,
        "downloaded_file": str(local_file),
        "preflight": preflight,
        "ocr_result": ocr_result,
        "complete_result": complete_result,
    }


def list_jobs(settings: Settings) -> dict:
    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "jobs": [],
        "message": "jobs endpoint placeholder",
    }
