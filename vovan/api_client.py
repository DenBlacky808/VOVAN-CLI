from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request


@dataclass
class VladcherApiClient:
    base_url: str
    worker_token: str
    dry_run: bool = True

    def _build_url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def _request_json(self, method: str, path: str, payload: dict | None = None) -> dict:
        if self.dry_run:
            return {
                "status": "dry-run",
                "method": method,
                "path": path,
                "payload": payload,
            }

        data = None
        headers = {
            "Authorization": f"Bearer {self.worker_token}",
            "Accept": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(
            self._build_url(path),
            data=data,
            method=method,
            headers=headers,
        )
        with request.urlopen(req) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))

    def _request_bytes(self, method: str, path: str) -> bytes:
        req = request.Request(
            self._build_url(path),
            method=method,
            headers={
                "Authorization": f"Bearer {self.worker_token}",
                "Accept": "*/*",
            },
        )
        with request.urlopen(req) as resp:  # noqa: S310
            return resp.read()

    @staticmethod
    def _parse_claim_response(response: dict) -> dict | None:
        if response.get("ok") is not True:
            return None

        job = response.get("job")
        if job is None:
            return None

        if isinstance(job, dict):
            return job
        return None

    def claim_next_job(self) -> dict | None:
        path = "/api/vovan/ocr/jobs/next/"
        response = self._request_json("GET", path)
        if self.dry_run:
            return response
        return self._parse_claim_response(response)

    def download_job_file(self, job_id: str) -> dict | bytes:
        path = f"/api/vovan/ocr/jobs/{job_id}/download/"
        if self.dry_run:
            return self._request_json("GET", path)
        return self._request_bytes("GET", path)

    def submit_result(self, job_id: str, result_text: str) -> dict:
        path = f"/api/vovan/ocr/jobs/{job_id}/complete/"
        payload = {"result_text": result_text}
        return self._request_json("POST", path, payload)

    def submit_failure(self, job_id: str, error_message: str) -> dict:
        path = f"/api/vovan/ocr/jobs/{job_id}/fail/"
        payload = {"error_message": error_message}
        return self._request_json("POST", path, payload)

    def get_job_status(self, job_id: str) -> dict:
        path = f"/api/vovan/ocr/jobs/{job_id}/status/"
        return self._request_json("GET", path)
