from pathlib import Path

from vovan.cli import build_parser, cmd_worker
from vovan.config import Settings


def _settings() -> Settings:
    return Settings(
        vladcher_base_url="https://worker.example",
        worker_token="token",
        mode="local",
        data_dir=Path("./data"),
        log_dir=Path("./logs"),
        report_dir=Path("./reports"),
        allowed_extensions={".txt"},
        max_file_size_mb=1,
        dry_run=True,
    )


def test_worker_parser_accepts_once_and_mode_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["worker", "--dry-run", "--once"])
    assert args.command == "worker"
    assert args.dry_run is True
    assert args.live is False
    assert args.once is True


def test_cmd_worker_sets_live_mode(monkeypatch) -> None:
    from vovan import cli as cli_module

    captured = {}

    def fake_load_settings():
        return _settings()

    def fake_run_worker(settings: Settings):
        captured["dry_run"] = settings.dry_run
        return {"status": "ok"}

    monkeypatch.setattr(cli_module, "load_settings", fake_load_settings)
    monkeypatch.setattr(cli_module, "run_worker", fake_run_worker)
    monkeypatch.setattr(cli_module, "write_report", lambda *args, **kwargs: None)

    exit_code = cmd_worker(worker_mode="live", once=True)

    assert exit_code == 0
    assert captured["dry_run"] is False


def test_cmd_worker_without_once_runs_loop(monkeypatch) -> None:
    from vovan import cli as cli_module

    captured = {}

    def fake_load_settings():
        return _settings()

    def fake_run_worker_loop(settings: Settings):
        captured["dry_run"] = settings.dry_run
        return {"status": "ok", "message": "loop stopped"}

    monkeypatch.setattr(cli_module, "load_settings", fake_load_settings)
    monkeypatch.setattr(cli_module, "run_worker_loop", fake_run_worker_loop)
    monkeypatch.setattr(cli_module, "write_report", lambda *args, **kwargs: None)

    exit_code = cmd_worker(worker_mode="live", once=False)

    assert exit_code == 0
    assert captured["dry_run"] is False
