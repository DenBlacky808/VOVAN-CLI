# harden_vovan_cli_mvp_pr2_before_merge

## Выполнено

- Добавлен `.gitignore` с исключениями для Python-артефактов, `.env`, `logs/*`, `reports/*` и сохранением `logs/.gitkeep`, `reports/.gitkeep`.
- Проверен smoke через module mode (`python3 -m vovan.cli ...`) без editable-install.
- В `README.md` добавлен fallback для запуска через module mode.
- Обновлён `docs/NEXT_CODEX_TASK.md`: следующий PR — `connect_vovan_cli_to_real_vladcher_worker_api.md`.

## Проверки

- `pytest -q`
- `python3 -m vovan.cli doctor || true`
- `python3 -m vovan.cli preflight ./data/sample.txt`
- `python3 -m vovan.cli ocr ./data/sample.txt`
- `python3 -m vovan.cli worker || true`
- `python3 -m vovan.cli jobs`
- `python3 -m vovan.cli report`
