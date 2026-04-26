from vovan.api_client import VladcherApiClient


def test_claim_next_job_uses_real_get_endpoint_in_dry_run() -> None:
    client = VladcherApiClient(base_url="https://worker.example", worker_token="t", dry_run=True)

    result = client.claim_next_job()

    assert result["method"] == "GET"
    assert result["path"] == "/api/vovan/ocr/jobs/next/"
    assert result["payload"] is None


def test_claim_next_job_parses_no_job_payload() -> None:
    payload = {"ok": True, "job": None}

    result = VladcherApiClient._parse_claim_response(payload)

    assert result is None


def test_claim_next_job_parses_job_payload() -> None:
    payload = {"ok": True, "job": {"job_id": "job-123"}}

    result = VladcherApiClient._parse_claim_response(payload)

    assert result == {"job_id": "job-123"}


def test_download_complete_fail_and_status_use_real_endpoints() -> None:
    client = VladcherApiClient(base_url="https://worker.example", worker_token="t", dry_run=True)

    download = client.download_job_file("42")
    complete = client.submit_result("42", "hello")
    fail = client.submit_failure("42", "boom")
    status = client.get_job_status("42")

    assert download["method"] == "GET"
    assert download["path"] == "/api/vovan/ocr/jobs/42/download/"

    assert complete["method"] == "POST"
    assert complete["path"] == "/api/vovan/ocr/jobs/42/complete/"
    assert complete["payload"] == {"result_text": "hello"}

    assert fail["method"] == "POST"
    assert fail["path"] == "/api/vovan/ocr/jobs/42/fail/"
    assert fail["payload"] == {"error_message": "boom"}

    assert status["method"] == "GET"
    assert status["path"] == "/api/vovan/ocr/jobs/42/status/"
