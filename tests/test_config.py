from vovan.config import Settings, missing_required_keys


def test_missing_required_keys() -> None:
    settings = Settings(vladcher_base_url="", vovan_worker_token="")
    assert missing_required_keys(settings) == ["VLADCHER_BASE_URL", "VOVAN_WORKER_TOKEN"]
