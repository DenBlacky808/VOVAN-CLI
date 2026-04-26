from pathlib import Path

from vovan.preflight import run_preflight


def test_preflight_ok_for_png(tmp_path: Path) -> None:
    sample = tmp_path / "sample.png"
    sample.write_bytes(b"abc")
    payload = run_preflight(str(sample))
    assert payload["status"] == "ok"
    assert payload["checks"]["suitable_for_ocr"] is True


def test_preflight_fails_for_missing_file(tmp_path: Path) -> None:
    payload = run_preflight(str(tmp_path / "missing.png"))
    assert payload["status"] == "failed"
