# NEXT CODEX TASK

## Что сделано

- создан Python CLI `vovan` с командами doctor/preflight/ocr/worker/jobs/report;
- добавлен dry-run API client и worker skeleton для pull-mode;
- добавлены Dockerfile, docker-compose, Makefile, `.env.example`;
- добавлены базовые тесты и документация (README, architecture, runbook).

## Какие проверки запускались

- `python3 -m pip install -e .[dev]`
- `pytest -q`
- `vovan doctor`
- `vovan preflight data/sample.png`
- `vovan ocr data/sample.png`
- `vovan worker`
- `vovan report`

## Ограничения

- реальный OCR engine не подключён;
- реальный VLADCHER_ru API workflow не интегрирован;
- нет GPU/ROCm поддержки;
- команды jobs/worker работают как dry-run placeholders.

## Следующий рекомендуемый PR

`connect_vovan_cli_to_real_vladcher_worker_api.md`
