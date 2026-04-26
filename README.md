# VOVAN OCR CLI MVP

Локальный backend-worker CLI для VOVAN OCR в режиме **pull-mode** c интеграцией с HTTP API VLADCHER_ru.

## Что это

- Локальный worker (macOS/Hackintosh first, Linux later).
- Не веб-сайт, не замена VLADCHER_ru.
- Без входящих соединений.
- OCR пока placeholder (без тяжёлой модели).

## Быстрый старт

```bash
cp .env.example .env
make install
make doctor
make preflight SAMPLE=./data/sample.txt
make ocr SAMPLE=./data/sample.txt
```

## CLI команды

- `vovan doctor`
- `vovan preflight <path>`
- `vovan ocr <path>`
- `vovan worker --dry-run --once`
- `vovan worker --live --once`
- `vovan jobs`
- `vovan report`

## Worker режимы

- `--dry-run`: принудительно без HTTP вызовов (удобно для smoke локально).
- `--live`: принудительно реальный HTTP pull в VLADCHER_ru API.
- `--once`: выполнить ровно один цикл worker (claim → download → preflight → placeholder OCR → complete/fail).

Если флаги не заданы, используется `VOVAN_DRY_RUN` из `.env`.

## Fallback без install -e

Если entrypoint `vovan` ещё не установлен (например, без `make install`), используйте module mode:

```bash
python3 -m vovan.cli doctor
python3 -m vovan.cli worker --dry-run --once
```

## Docker Compose

```bash
docker compose up --build vovan-worker
```

См. `docs/runbook.md` и `docs/architecture.md`.
