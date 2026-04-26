from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, parse, request


@dataclass
class ApiClientError(Exception):
    message: str
    category: str
    status_code: int | None = None
    retryable: bool = False
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "category": self.category,
            "status_code": self.status_code,
            "retryable": self.retryable,
            "details": self.details or {},
        }


@dataclass
class VladcherApiClient:
    base_url: str
    worker_token: str
    dry_run: bool = True
    timeout_seconds: int = 30
    download_dir: Path = Path("./data/downloads")
    opener: Any | None = None

    def __post_init__(self) -> None:
        if self.opener is None:
            self.opener = request.build_opener()

    def _build_url(self, path: str) -> str:
        return parse.urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))

    def _headers(self, include_json: bool = True) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.worker_token}"}
        if include_json:
            headers["Content-Type"] = "application/json"
        return headers

    def _map_http_error(self, exc: error.HTTPError) -> ApiClientError:
        code = exc.code
        body = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
        category = {
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            409: "conflict",
        }.get(code, "server_error" if code >= 500 else "http_error")
        return ApiClientError(
            message=f"HTTP {code} from Vladcher API",
            category=category,
            status_code=code,
            retryable=code >= 500,
            details={"body": body[:500]},
        )

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=self._build_url(path),
            data=data,
            method=method,
            headers=self._headers(),
        )
        try:
            with self.opener.open(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise self._map_http_error(exc) from exc
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            raise ApiClientError(
                message="Network timeout or connectivity error",
                category="network_error",
                retryable=True,
                details={"reason": str(exc)},
            ) from exc

        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ApiClientError(
                message="Invalid JSON in API response",
                category="invalid_json",
                retryable=False,
                details={"response": raw[:500]},
            ) from exc

    def claim_next_job(self) -> dict | None:
        if self.dry_run:
            return None
        data = self._request_json("POST", "/api/v1/worker/jobs/claim-next")
        return data.get("job")

    def download_job_file(self, job_id: str) -> dict:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "local_path": ""}

        req = request.Request(
            url=self._build_url(f"/api/v1/worker/jobs/{job_id}/file"),
            method="GET",
            headers=self._headers(include_json=False),
        )

        try:
            with self.opener.open(req, timeout=self.timeout_seconds) as response:
                content = response.read()
                content_type = response.headers.get("Content-Type", "application/octet-stream")
        except error.HTTPError as exc:
            raise self._map_http_error(exc) from exc
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            raise ApiClientError(
                message="Download failed due to network error",
                category="network_error",
                retryable=True,
                details={"reason": str(exc)},
            ) from exc

        self.download_dir.mkdir(parents=True, exist_ok=True)
        local_path = self.download_dir / f"job_{job_id}.pdf"
        local_path.write_bytes(content)
        return {"status": "downloaded", "job_id": job_id, "local_path": str(local_path), "content_type": content_type}

    def submit_result(self, job_id: str, result: dict) -> dict:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "result": result}
        return self._request_json("POST", f"/api/v1/worker/jobs/{job_id}/complete", payload=result)

    def submit_failure(self, job_id: str, error_message: str, context: dict[str, Any] | None = None) -> dict:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "error_message": error_message, "context": context or {}}
        payload = {"error_message": error_message, "context": context or {}}
        return self._request_json("POST", f"/api/v1/worker/jobs/{job_id}/fail", payload=payload)

    def get_job_status(self, job_id: str) -> dict:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id}
        return self._request_json("GET", f"/api/v1/worker/jobs/{job_id}")
