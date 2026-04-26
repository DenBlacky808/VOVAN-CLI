from __future__ import annotations

from vovan.api_client import ApiError, VladcherApiClient
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
        timeout_seconds=settings.request_timeout_seconds,
    )

    try:
        claim = client.claim_next_job()
        if claim is None or claim.get("job") is None:
            return {
                "status": "ok",
                "mode": settings.mode,
                "dry_run": settings.dry_run,
                "result": "no_job",
                "claim_result": claim,
            }

        job = claim.get("job", claim)
        job_id = str(job.get("id", ""))
        if not job_id:
            return {
                "status": "error",
                "message": "Invalid claim response: missing job id",
                "claim_result": claim,
            }

        download = client.download_job_file(job_id, settings.download_dir)
        file_path = download["file_path"]

        preflight = run_preflight(file_path, settings)
        if not preflight["suitable_for_ocr"]:
            failure = client.submit_failure(job_id, reason="preflight_failed", details={"preflight": preflight})
            return {
                "status": "ok",
                "mode": settings.mode,
                "dry_run": settings.dry_run,
                "result": "failed_preflight",
                "job_id": job_id,
                "preflight": preflight,
                "failure_submit": failure,
            }

        ocr_result = run_placeholder_ocr(file_path)
        complete = client.submit_result(job_id, ocr_result)
        return {
            "status": "ok",
            "mode": settings.mode,
            "dry_run": settings.dry_run,
            "result": "completed",
            "job_id": job_id,
            "download": download,
            "preflight": preflight,
            "ocr": ocr_result,
            "complete_submit": complete,
        }
    except ApiError as exc:
        return {
            "status": "error",
            "mode": settings.mode,
            "dry_run": settings.dry_run,
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
