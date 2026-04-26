from pathlib import Path
from unittest.mock import Mock

import vovan.ocr as ocr_module
from vovan.ocr import run_ocr, run_placeholder_ocr


def test_ocr_placeholder_contract() -> None:
    result = run_placeholder_ocr("/tmp/demo.pdf")
    assert result["status"] == "completed"
    assert result["result_text"] == "placeholder OCR result"
    assert result["source_file"] == "/tmp/demo.pdf"
    assert result["engine"] == "placeholder"
    assert "created_at" in result


def test_run_ocr_unsupported_engine_falls_back_safely() -> None:
    result = run_ocr("/tmp/demo.pdf", "unsupported")
    assert result["status"] == "completed"
    assert result["engine"] == "placeholder"
    assert result["engine_requested"] == "unsupported"
    assert "engine_warning" in result


def test_run_ocr_tesseract_unavailable_falls_back_safely(monkeypatch) -> None:
    monkeypatch.setattr(ocr_module.shutil, "which", lambda _: None)
    result = run_ocr("/tmp/demo.png", "tesseract")
    assert result["status"] == "completed"
    assert result["engine_requested"] == "tesseract"
    assert result["engine"] == "placeholder"
    assert "not installed" in result["engine_warning"]


def test_run_ocr_tesseract_available_for_image(monkeypatch, tmp_path: Path) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"fake")

    monkeypatch.setattr(ocr_module.shutil, "which", lambda _: "/usr/bin/tesseract")
    list_completed = Mock(returncode=0, stdout="List of available languages in \"/tmp\":\neng\nrus\n", stderr="")
    ocr_completed = Mock(returncode=0, stdout="recognized text\n", stderr="")
    run_mock = Mock(side_effect=[list_completed, ocr_completed])
    monkeypatch.setattr(ocr_module.subprocess, "run", run_mock)

    result = run_ocr(str(image), "tesseract", tesseract_lang="rus+eng")
    assert result["status"] == "completed"
    assert result["result_text"] == "recognized text"
    assert result["engine_requested"] == "tesseract"
    assert result["engine"] == "tesseract"
    assert run_mock.call_count == 2
    assert run_mock.call_args_list[1].args[0] == ["tesseract", str(image), "stdout", "-l", "rus+eng"]


def test_run_ocr_tesseract_available_but_pdf_falls_back(monkeypatch) -> None:
    monkeypatch.setattr(
        ocr_module.shutil,
        "which",
        lambda name: "/usr/bin/tesseract" if name == "tesseract" else None,
    )
    run_mock = Mock()
    monkeypatch.setattr(ocr_module.subprocess, "run", run_mock)

    result = run_ocr("/tmp/demo.pdf", "tesseract")
    assert result["status"] == "completed"
    assert result["engine_requested"] == "tesseract"
    assert result["engine"] == "placeholder"
    assert "pdftoppm is not installed" in result["engine_warning"]
    run_mock.assert_called_once_with(
        ["tesseract", "--list-langs"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_run_ocr_tesseract_missing_requested_language_falls_back_safely(monkeypatch, tmp_path: Path) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"fake")

    monkeypatch.setattr(ocr_module.shutil, "which", lambda _: "/usr/bin/tesseract")
    list_completed = Mock(returncode=0, stdout="List of available languages in \"/tmp\":\neng\n", stderr="")
    run_mock = Mock(return_value=list_completed)
    monkeypatch.setattr(ocr_module.subprocess, "run", run_mock)

    result = run_ocr(str(image), "tesseract", tesseract_lang="rus+eng")
    assert result["status"] == "completed"
    assert result["engine"] == "placeholder"
    assert result["engine_requested"] == "tesseract"
    assert "not installed" in result["engine_warning"]


def test_pdf_conversion_command_and_tesseract_per_page(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        ocr_module.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"tesseract", "pdftoppm"} else None,
    )

    calls = []

    def _fake_run(command, capture_output, text, check):
        calls.append(command)
        if command[:2] == ["tesseract", "--list-langs"]:
            return Mock(returncode=0, stdout="List of available languages:\neng\n", stderr="")
        if command and command[0] == "pdftoppm":
            output_prefix = Path(command[-1])
            (output_prefix.parent / "page-1.png").write_bytes(b"p1")
            (output_prefix.parent / "page-2.png").write_bytes(b"p2")
            return Mock(returncode=0, stdout="", stderr="")
        if command and command[0] == "tesseract":
            page = Path(command[1]).name
            return Mock(returncode=0, stdout=f"text from {page}\n", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(ocr_module.subprocess, "run", _fake_run)

    result = run_ocr(str(pdf), "tesseract", tesseract_lang="eng", pdf_max_pages=2, pdf_dpi=150)
    assert result["engine"] == "tesseract"
    assert "--- page 1 ---" in result["result_text"]
    assert "--- page 2 ---" in result["result_text"]
    assert "text from page-1.png" in result["result_text"]
    assert "text from page-2.png" in result["result_text"]

    pdftoppm_call = next(cmd for cmd in calls if cmd and cmd[0] == "pdftoppm")
    assert pdftoppm_call == [
        "pdftoppm",
        "-png",
        "-r",
        "150",
        "-f",
        "1",
        "-l",
        "2",
        str(pdf),
        pdftoppm_call[-1],
    ]
    tesseract_page_calls = [cmd for cmd in calls if cmd and cmd[0] == "tesseract" and len(cmd) > 1 and cmd[1] != "--list-langs"]
    assert len(tesseract_page_calls) == 2
    assert tesseract_page_calls[0][3:] == ["-l", "eng"]


def test_pdf_max_pages_limit_is_used(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(
        ocr_module.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"tesseract", "pdftoppm"} else None,
    )

    commands = []

    def _fake_run(command, capture_output, text, check):
        commands.append(command)
        if command[:2] == ["tesseract", "--list-langs"]:
            return Mock(returncode=0, stdout="List of available languages:\neng\n", stderr="")
        if command[0] == "pdftoppm":
            output_prefix = Path(command[-1])
            (output_prefix.parent / "page-1.png").write_bytes(b"p1")
            return Mock(returncode=0, stdout="", stderr="")
        return Mock(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(ocr_module.subprocess, "run", _fake_run)
    run_ocr(str(pdf), "tesseract", pdf_max_pages=1, pdf_dpi=200)

    pdftoppm_call = next(cmd for cmd in commands if cmd[0] == "pdftoppm")
    assert "-l" in pdftoppm_call
    assert pdftoppm_call[pdftoppm_call.index("-l") + 1] == "1"
