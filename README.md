# VOVAN OCR CLI MVP

Минимальный MVP-скелет локального backend-worker `vovan` для pull-mode интеграции с VLADCHER_ru API.

## Что умеет

- читает конфиг из `.env`;
- `vovan doctor` проверяет готовность окружения;
- `vovan preflight <path>` валидирует локальный файл для OCR pipeline;
- `vovan ocr <path>` возвращает placeholder OCR результат;
- `vovan worker` запускает dry-run заготовку pull-worker;
- `vovan jobs` резервирует CLI-контракт для списка задач;
- `vovan report` пишет markdown-отчёт в `reports/`.

## Быстрый старт

```bash
cp .env.example .env
python3 -m pip install -e .[dev]
vovan doctor
```

## Docker Compose

```bash
docker compose build vovan-worker
docker compose run --rm vovan-worker
```

## Ограничения MVP

- тяжёлый OCR не подключён;
- GPU/ROCm не используются;
- Playwright/Selenium не добавляются;
- входящие подключения не требуются.
