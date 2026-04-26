from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ApiError(Exception):
    code: str
    message: str
    http_status: int | None = None
    retryable: bool = False
    details: dict | None = None

    def to_dict(self) -> dict:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "http_status": self.http_status,
            "retryable": self.retryable,
            "details": self.details or {},
        }


@dataclass
class VladcherApiClient:
    base_url: str
    worker_token: str
    dry_run: bool = True
    timeout_seconds: int = 30

    def _build_url(self, path: str) -> str:
        return urllib.parse.urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.worker_token}",
            "Accept": "application/json",
        }

    def _request_json(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = None
        headers = self._headers()
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url=self._build_url(path),
            method=method,
            data=body,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read()
                text = raw.decode("utf-8") if raw else "{}"
                try:
                    data = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ApiError(
                        code="invalid_json",
                        message="Response is not valid JSON",
                        http_status=resp.status,
                        details={"body": text[:200]},
                    ) from exc
                return data
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            self._raise_http_error(exc.code, body_text)
        except urllib.error.URLError as exc:
            raise ApiError(
                code="network_timeout" if "timed out" in str(exc.reason).lower() else "network_error",
                message=f"Network request failed: {exc.reason}",
                retryable=True,
            ) from exc

    def _raise_http_error(self, status_code: int, body_text: str) -> None:
        error_map = {
            401: ("unauthorized", False),
            403: ("forbidden", False),
            404: ("not_found", False),
            409: ("conflict", False),
        }
        code, retryable = error_map.get(status_code, ("server_error", status_code >= 500))
        raise ApiError(
            code=code,
            message=f"HTTP {status_code} from VLADCHER API",
            http_status=status_code,
            retryable=retryable,
            details={"body": body_text[:300]},
        )

    def claim_next_job(self) -> dict | None:
        if self.dry_run:
            return {"status": "dry-run", "message": "claim_next_job skipped"}
        return self._request_json("POST", "/api/v1/worker/ocr-jobs/claim-next")

    def download_job_file(self, job_id: str, download_dir: Path) -> dict:
        if self.dry_run:
            target = download_dir / f"job_{job_id}.pdf"
            return {
                "status": "dry-run",
                "job_id": job_id,
                "message": "download skipped",
                "file_path": str(target),
            }

        req = urllib.request.Request(
            url=self._build_url(f"/api/v1/worker/ocr-jobs/{job_id}/download"),
            method="GET",
            headers=self._headers(),
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                download_dir.mkdir(parents=True, exist_ok=True)
                extension = ".pdf"
                content_type = resp.headers.get("Content-Type", "")
                if "image/png" in content_type:
                    extension = ".png"
                target = download_dir / f"job_{job_id}{extension}"
                target.write_bytes(resp.read())
                return {
                    "status": "ok",
                    "job_id": job_id,
                    "file_path": str(target),
                    "content_type": content_type,
                }
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            self._raise_http_error(exc.code, body_text)
        except urllib.error.URLError as exc:
            raise ApiError(
                code="network_timeout" if "timed out" in str(exc.reason).lower() else "network_error",
                message=f"Network request failed: {exc.reason}",
                retryable=True,
            ) from exc

    def submit_result(self, job_id: str, result: dict) -> dict:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "message": "submit skipped", "result": result}
        payload = {"result_text": result.get("result_text", ""), "meta": result}
        return self._request_json("POST", f"/api/v1/worker/ocr-jobs/{job_id}/complete", payload=payload)

    def submit_failure(self, job_id: str, reason: str, details: dict | None = None) -> dict:
        if self.dry_run:
            return {
                "status": "dry-run",
                "job_id": job_id,
                "message": "submit_failure skipped",
                "reason": reason,
            }
        payload = {"reason": reason, "details": details or {}}
        return self._request_json("POST", f"/api/v1/worker/ocr-jobs/{job_id}/fail", payload=payload)

    def get_job_status(self, job_id: str) -> dict:
        if self.dry_run:
            return {"status": "dry-run", "job_id": job_id, "message": "get_job_status skipped"}
        return self._request_json("GET", f"/api/v1/worker/ocr-jobs/{job_id}")
