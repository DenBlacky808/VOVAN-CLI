# NEXT CODEX TASK

## Что сделано

- Создан Python CLI skeleton `vovan` с командами doctor/preflight/ocr/worker/jobs/report.
- Добавлен Dockerfile и docker-compose service `vovan-worker`.
- Добавлен Makefile для локального запуска и smoke-команд.
- Добавлены базовые тесты config/preflight/ocr placeholder.
- Добавлены docs: architecture и runbook.

## Какие проверки запускались

- `pip3 install -e .[dev]`
- `pytest -q`
- `vovan doctor`
- `vovan preflight ./data/sample.txt`
- `vovan ocr ./data/sample.txt`

## Ограничения

- Реальный OCR не подключён (placeholder).
- Реальный VLADCHER API workflow в dry-run.
- GPU/ROCm не подключены.
- Нет Playwright/Selenium.

## Следующий рекомендуемый PR

`connect_vovan_cli_to_real_vladcher_worker_api.md`
