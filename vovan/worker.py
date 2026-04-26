from __future__ import annotations

from dataclasses import asdict, dataclass

from .api_client import VladcherApiClient
from .config import Settings, missing_required_keys


@dataclass(slots=True)
class WorkerResult:
    status: str
    message: str
    details: dict


def run_worker(settings: Settings) -> WorkerResult:
    missing = missing_required_keys(settings)
    if missing:
        return WorkerResult(
            status="failed",
            message="Missing required environment variables.",
            details={"missing": missing},
        )

    client = VladcherApiClient(
        base_url=settings.vladcher_base_url,
        worker_token=settings.vovan_worker_token,
        dry_run=settings.dry_run,
    )

    try:
        claim = client.claim_next_job()
        return WorkerResult(
            status="ok",
            message="Worker loop placeholder executed.",
            details={"dry_run": settings.dry_run, "claim": claim},
        )
    except Exception as exc:  # pragma: no cover
        return WorkerResult(
            status="failed",
            message="Worker execution failed with a handled error.",
            details={"error": str(exc)},
        )


def worker_result_to_dict(result: WorkerResult) -> dict:
    return asdict(result)
