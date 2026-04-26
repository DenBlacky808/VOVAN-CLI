# create_vovan_ocr_cli_mvp_skeleton

MVP skeleton создан как mergeable PR:

- Python CLI пакет `vovan` с командами `doctor`, `preflight`, `ocr`, `worker`, `jobs`, `report`.
- Конфигурация через `.env`.
- Dry-run заготовка pull-worker для VLADCHER_ru API-контракта.
- Placeholder OCR (без тяжёлого движка).
- Dockerfile и Docker Compose service `vovan-worker`.
- Makefile для локальных и docker-команд.
- Базовые тесты и документация runbook/architecture/NEXT_CODEX_TASK.

Ограничения соблюдены:

- Без GPU/ROCm.
- Без Playwright/Selenium.
- Без web-сервера и входящих подключений.
