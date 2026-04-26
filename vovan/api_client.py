from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class VladcherApiClient:
    base_url: str
    worker_token: str
    dry_run: bool = True

    def claim_next_job(self) -> dict[str, Any]:
        if self.dry_run:
            return {"status": "dry-run", "job": None, "message": "claim_next_job placeholder"}
        raise NotImplementedError("Real API integration is not implemented in this MVP.")

    def download_job_file(self, job_id: str) -> dict[str, Any]:
        if self.dry_run:
            return {
                "status": "dry-run",
                "job_id": job_id,
                "message": "download_job_file placeholder",
            }
        raise NotImplementedError("Real API integration is not implemented in this MVP.")

    def submit_result(self, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.dry_run:
            return {
                "status": "dry-run",
                "job_id": job_id,
                "payload": payload,
                "message": "submit_result placeholder",
            }
        raise NotImplementedError("Real API integration is not implemented in this MVP.")
