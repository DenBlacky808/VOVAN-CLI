from __future__ import annotations

from vovan.api_client import VladcherApiClient
from vovan.config import Settings, validate_required_env


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
    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "claim_result": claim,
    }


def list_jobs(settings: Settings) -> dict:
    return {
        "status": "ok",
        "mode": settings.mode,
        "dry_run": settings.dry_run,
        "jobs": [],
        "message": "jobs endpoint placeholder",
    }
