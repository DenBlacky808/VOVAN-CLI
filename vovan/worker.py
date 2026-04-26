from __future__ import annotations

import time
from typing import Any

from vovan.api_client import VladcherApiClient
from vovan.config import Settings, validate_required_env
from vovan.ocr import run_placeholder_ocr
from vovan.preflight import run_preflight


def _run_one_cycle(settings: Settings, client: VladcherApiClient) -> dict[str, Any]:
    claim = client.claim_next_job()
    if claim is None:
        return {"status": "error", "step": "claim", "message": "Empty claim response"}
    if claim.get("status") == "error":
        return {"status": "error", "step": "claim", "claim": claim}

    job = claim.get("job")
    if not job:
        return {"status": "ok", "result": "no_job", "claim": claim}

    job_id = str(job.get("id"))
    filename = str(job.get("filename") or "input.pdf")

    download = client.download_job_file(job_id=job_id, download_dir=settings.download_dir, filename=filename)
    if download.get("status") == "error":
        return {"status": "error", "step": "download", "job_id": job_id, "download": download}

    local_path = download.get("local_path")
    preflight = run_preflight(str(local_path), settings)
    if not preflight.get("suitable_for_ocr"):
        failure = client.submit_failure(job_id=job_id, reason="preflight_failed", preflight=preflight)
        return {
            "status": "ok",
            "result": "failed_preflight",
            "job_id": job_id,
            "preflight": preflight,
            "submit_failure": failure,
        }

    ocr = run_placeholder_ocr(str(local_path))
    complete = client.submit_result(job_id=job_id, result=ocr)
    if complete.get("status") == "error":
        return {
            "status": "error",
            "step": "complete",
            "job_id": job_id,
            "preflight": preflight,
            "ocr": ocr,
            "complete": complete,
        }

    return {
        "status": "ok",
        "result": "processed",
        "job_id": job_id,
        "preflight": preflight,
        "ocr": ocr,
        "complete": complete,
    }


def run_worker(settings: Settings, once: bool = True) -> dict[str, Any]:
    missing = validate_required_env(settings)
    if missing:
        return {
            "status": "error",
            "message": f"Missing required env vars: {', '.join(missing)}",
        }

    client = VladcherApiClient(
        base_url=settings.vladcher_base_url,
        worker_token=settings.worker_token,
        request_timeout_seconds=settings.request_timeout_seconds,
        dry_run=settings.dry_run,
    )

    runs: list[dict[str, Any]] = []
    while True:
        result = _run_one_cycle(settings, client)
        runs.append(result)
        if once:
            break
        if result.get("status") == "error":
            break
        time.sleep(settings.worker_sleep_seconds)

    return {
        "status": "ok" if all(item.get("status") == "ok" for item in runs) else "error",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "once": once,
        "runs": runs,
    }


def list_jobs(settings: Settings) -> dict:
    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "jobs": [],
        "message": "jobs endpoint placeholder",
    }
