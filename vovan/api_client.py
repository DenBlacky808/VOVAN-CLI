from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, parse, request


@dataclass
class VladcherApiClient:
    base_url: str
    worker_token: str
    request_timeout_seconds: int = 30
    dry_run: bool = True

    def _join_url(self, path: str) -> str:
        return parse.urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.worker_token}",
            "Accept": "application/json",
        }

    def _error(self, kind: str, message: str, status_code: int | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "status": "error",
            "error": {
                "type": kind,
                "message": message,
                "status_code": status_code,
                "details": details or {},
            },
        }

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None
        headers = self._headers()
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(self._join_url(path), data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.request_timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    data = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    return self._error("invalid_json", "Server returned invalid JSON", resp.status)
                return {"status": "ok", "http_status": resp.status, "data": data}
        except error.HTTPError as exc:
            kind = {
                401: "unauthorized",
                403: "forbidden",
                404: "not_found",
                409: "conflict",
            }.get(exc.code, "server_error" if exc.code >= 500 else "http_error")
            return self._error(kind, f"HTTP {exc.code}", exc.code)
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            return self._error("network_timeout", str(exc))

    def claim_next_job(self) -> dict[str, Any] | None:
        if self.dry_run:
            return {"status": "dry-run", "message": "claim_next_job skipped", "job": None}
        response = self._request_json("POST", "/api/v1/worker/ocr/jobs/claim-next/")
        if response.get("status") != "ok":
            return response
        return {"status": "ok", "job": response.get("data", {}).get("job")}

    def download_job_file(self, job_id: str, download_dir: Path, filename: str = "input.pdf") -> dict[str, Any]:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "message": "download skipped", "local_path": str(download_dir / filename)}

        req = request.Request(
            self._join_url(f"/api/v1/worker/ocr/jobs/{job_id}/file/"),
            headers=self._headers(),
            method="GET",
        )
        try:
            with request.urlopen(req, timeout=self.request_timeout_seconds) as resp:
                download_dir.mkdir(parents=True, exist_ok=True)
                local_path = download_dir / f"job_{job_id}_{Path(filename).name}"
                local_path.write_bytes(resp.read())
                return {"status": "ok", "job_id": job_id, "local_path": str(local_path)}
        except error.HTTPError as exc:
            kind = {
                401: "unauthorized",
                403: "forbidden",
                404: "not_found",
                409: "conflict",
            }.get(exc.code, "server_error" if exc.code >= 500 else "http_error")
            return self._error(kind, f"HTTP {exc.code}", exc.code)
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            return self._error("network_timeout", str(exc))

    def submit_result(self, job_id: str, result: dict[str, Any]) -> dict[str, Any]:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "message": "submit skipped", "result": result}
        return self._request_json("POST", f"/api/v1/worker/ocr/jobs/{job_id}/complete/", payload=result)

    def submit_failure(self, job_id: str, reason: str, preflight: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.dry_run:
            return {
                "status": "dry-run",
                "job_id": job_id,
                "message": "submit_failure skipped",
                "reason": reason,
            }
        payload = {"reason": reason, "preflight": preflight or {}}
        return self._request_json("POST", f"/api/v1/worker/ocr/jobs/{job_id}/fail/", payload=payload)

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "job": None}
        return self._request_json("GET", f"/api/v1/worker/ocr/jobs/{job_id}/")
