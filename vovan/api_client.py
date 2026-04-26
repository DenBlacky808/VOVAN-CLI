from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass
class VladcherApiClient:
    base_url: str
    worker_token: str
    dry_run: bool = True
    request_timeout_seconds: int = 30

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.worker_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _build_url(self, path: str) -> str:
        return urljoin(f"{self.base_url.rstrip('/')}/", path.lstrip("/"))

    def _http_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._build_url(path)
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = Request(url=url, method=method, headers=self._headers(), data=body)

        try:
            with urlopen(req, timeout=self.request_timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    parsed = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    return {
                        "ok": False,
                        "error": {
                            "kind": "invalid_json",
                            "http_status": resp.status,
                            "message": "Response is not valid JSON",
                            "url": url,
                        },
                    }
                return {"ok": True, "http_status": resp.status, "data": parsed}
        except HTTPError as exc:
            return {
                "ok": False,
                "error": {
                    "kind": self._http_error_kind(exc.code),
                    "http_status": exc.code,
                    "message": str(exc),
                    "url": url,
                },
            }
        except URLError as exc:
            reason = exc.reason
            if isinstance(reason, socket.timeout):
                kind = "timeout"
            else:
                kind = "network"
            return {
                "ok": False,
                "error": {
                    "kind": kind,
                    "message": str(exc),
                    "url": url,
                },
            }
        except TimeoutError as exc:
            return {
                "ok": False,
                "error": {"kind": "timeout", "message": str(exc), "url": url},
            }

    @staticmethod
    def _http_error_kind(status_code: int) -> str:
        if status_code == 401:
            return "unauthorized"
        if status_code == 403:
            return "forbidden"
        if status_code == 404:
            return "not_found"
        if status_code == 409:
            return "conflict"
        if 500 <= status_code <= 599:
            return "server_error"
        return "http_error"

    def claim_next_job(self) -> dict[str, Any]:
        if self.dry_run:
            return {"status": "dry-run", "message": "claim_next_job skipped", "job": None}

        response = self._http_json("POST", "/api/v1/worker/ocr/jobs/claim", {"source": "vovan-cli"})
        if not response["ok"]:
            return {"status": "error", "step": "claim", "error": response["error"]}

        data = response["data"]
        job = data.get("job")
        return {"status": "ok", "job": job, "raw": data}

    def download_job_file(self, job_id: str, destination_dir: Path) -> dict[str, Any]:
        if self.dry_run:
            return {
                "status": "dry-run",
                "job_id": job_id,
                "message": "download skipped",
                "local_path": str(destination_dir / f"dryrun_{job_id}.pdf"),
            }

        destination_dir.mkdir(parents=True, exist_ok=True)
        url = self._build_url(f"/api/v1/worker/ocr/jobs/{job_id}/file")
        request = Request(url=url, method="GET", headers=self._headers())
        local_path = destination_dir / f"job_{job_id}.pdf"

        try:
            with urlopen(request, timeout=self.request_timeout_seconds) as resp:
                local_path.write_bytes(resp.read())
                return {
                    "status": "ok",
                    "job_id": job_id,
                    "local_path": str(local_path),
                    "http_status": resp.status,
                }
        except HTTPError as exc:
            return {
                "status": "error",
                "step": "download",
                "job_id": job_id,
                "error": {
                    "kind": self._http_error_kind(exc.code),
                    "http_status": exc.code,
                    "message": str(exc),
                    "url": url,
                },
            }
        except URLError as exc:
            return {
                "status": "error",
                "step": "download",
                "job_id": job_id,
                "error": {
                    "kind": "timeout" if isinstance(exc.reason, socket.timeout) else "network",
                    "message": str(exc),
                    "url": url,
                },
            }

    def submit_result(self, job_id: str, result: dict[str, Any]) -> dict[str, Any]:
        if self.dry_run:
            return {
                "status": "dry-run",
                "job_id": job_id,
                "message": "submit_result skipped",
                "result": result,
            }

        response = self._http_json("POST", f"/api/v1/worker/ocr/jobs/{job_id}/complete", result)
        if not response["ok"]:
            return {"status": "error", "step": "submit_result", "job_id": job_id, "error": response["error"]}
        return {"status": "ok", "job_id": job_id, "data": response["data"]}

    def submit_failure(self, job_id: str, reason: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"reason": reason, "details": details or {}}
        if self.dry_run:
            return {
                "status": "dry-run",
                "job_id": job_id,
                "message": "submit_failure skipped",
                "payload": payload,
            }

        response = self._http_json("POST", f"/api/v1/worker/ocr/jobs/{job_id}/fail", payload)
        if not response["ok"]:
            return {"status": "error", "step": "submit_failure", "job_id": job_id, "error": response["error"]}
        return {"status": "ok", "job_id": job_id, "data": response["data"]}

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        if self.dry_run:
            return {
                "status": "dry-run",
                "job_id": job_id,
                "job_status": "unknown",
                "message": "get_job_status skipped",
            }

        response = self._http_json("GET", f"/api/v1/worker/ocr/jobs/{job_id}")
        if not response["ok"]:
            return {"status": "error", "step": "get_job_status", "job_id": job_id, "error": response["error"]}

        data = response["data"]
        return {"status": "ok", "job_id": job_id, "job_status": data.get("status"), "data": data}
