from __future__ import annotations

from vovan.api_client import ApiClientError, VladcherApiClient
from vovan.config import Settings, validate_required_env
from vovan.ocr import run_placeholder_ocr
from vovan.preflight import run_preflight


def run_worker(settings: Settings, once: bool = True) -> dict:
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
        timeout_seconds=settings.request_timeout_seconds,
        download_dir=settings.download_dir,
    )

    try:
        job = client.claim_next_job()
        if job is None:
            return {
                "status": "ok",
                "result": "no_job",
                "mode": settings.mode,
                "dry_run": settings.dry_run,
                "once": once,
            }

        job_id = str(job.get("id"))
        download = client.download_job_file(job_id)
        local_path = download["local_path"]

        preflight = run_preflight(local_path, settings)
        if not preflight["suitable_for_ocr"]:
            failure = client.submit_failure(job_id, "preflight_failed", context={"preflight": preflight})
            return {
                "status": "ok",
                "result": "failed_preflight",
                "job_id": job_id,
                "preflight": preflight,
                "submit_failure": failure,
            }

        ocr = run_placeholder_ocr(local_path)
        complete = client.submit_result(job_id, {"result_text": ocr["result_text"], "ocr": ocr, "preflight": preflight})

        return {
            "status": "ok",
            "result": "completed",
            "job_id": job_id,
            "download": download,
            "preflight": preflight,
            "ocr": ocr,
            "submit_result": complete,
        }
    except ApiClientError as exc:
        return {
            "status": "error",
            "result": "api_error",
            "error": exc.to_dict(),
        }


def list_jobs(settings: Settings) -> dict:
    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "jobs": [],
        "message": "jobs endpoint placeholder",
    }
