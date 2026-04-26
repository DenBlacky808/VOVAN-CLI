from __future__ import annotations

from pathlib import Path
from typing import Any

from vovan.api_client import VladcherApiClient
from vovan.config import Settings, validate_required_env
from vovan.ocr import run_placeholder_ocr
from vovan.preflight import run_preflight


def _extract_job_id(job: dict[str, Any]) -> str:
    return str(job.get("id") or job.get("job_id") or "")


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
        dry_run=settings.dry_run,
        request_timeout_seconds=settings.request_timeout_seconds,
    )

    claim = client.claim_next_job()
    if claim.get("status") == "error":
        return {"status": "error", "step": "claim", "error": claim.get("error")}

    job = claim.get("job")
    if not job:
        return {
            "status": "ok",
            "worker_status": "no_job",
            "mode": settings.mode,
            "dry_run": settings.dry_run,
            "once": once,
            "claim": claim,
        }

    job_id = _extract_job_id(job)
    if not job_id:
        return {
            "status": "error",
            "step": "claim",
            "message": "Claimed job has no id/job_id",
            "claim": claim,
        }

    download = client.download_job_file(job_id, settings.download_dir)
    if download.get("status") == "error":
        return {
            "status": "error",
            "step": "download",
            "job_id": job_id,
            "error": download.get("error"),
        }

    source_file = download.get("local_path")
    if not source_file:
        return {
            "status": "error",
            "step": "download",
            "job_id": job_id,
            "message": "download_job_file did not return local_path",
            "download": download,
        }

    preflight = run_preflight(str(source_file), settings)
    if not preflight["suitable_for_ocr"]:
        failure = client.submit_failure(
            job_id=job_id,
            reason="preflight_failed",
            details={"preflight": preflight},
        )
        return {
            "status": "ok",
            "worker_status": "failed",
            "job_id": job_id,
            "failure_reason": "preflight_failed",
            "preflight": preflight,
            "failure_submit": failure,
        }

    ocr = run_placeholder_ocr(str(source_file))
    completion_payload = {
        "result_text": ocr["result_text"],
        "meta": {
            "source_file": ocr["source_file"],
            "created_at": ocr["created_at"],
            "engine": "placeholder",
        },
    }
    completion = client.submit_result(job_id, completion_payload)

    if completion.get("status") == "error":
        return {
            "status": "error",
            "step": "submit_result",
            "job_id": job_id,
            "error": completion.get("error"),
            "preflight": preflight,
            "ocr": ocr,
        }

    return {
        "status": "ok",
        "worker_status": "completed",
        "job_id": job_id,
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "once": once,
        "preflight": preflight,
        "ocr": ocr,
        "completion": completion,
    }


def list_jobs(settings: Settings) -> dict:
    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "jobs": [],
        "message": "jobs endpoint placeholder",
    }
