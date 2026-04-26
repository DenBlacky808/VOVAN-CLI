from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VladcherApiClient:
    base_url: str
    worker_token: str
    dry_run: bool = True

    def claim_next_job(self) -> dict | None:
        if self.dry_run:
            return {"status": "dry-run", "message": "claim_next_job skipped"}
        return None

    def download_job_file(self, job_id: str) -> dict:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "message": "download skipped"}
        return {"status": "not-implemented", "job_id": job_id}

    def submit_result(self, job_id: str, result: dict) -> dict:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "message": "submit skipped", "result": result}
        return {"status": "not-implemented", "job_id": job_id}
