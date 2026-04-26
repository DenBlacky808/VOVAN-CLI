# VOVAN Runbook (MVP)

## 1) Подготовка

```bash
cp .env.example .env
```

Заполните:
- `VLADCHER_BASE_URL`
- `VOVAN_WORKER_TOKEN`

Проверьте ключевые параметры worker:
- `VOVAN_DRY_RUN=true|false`
- `VOVAN_REQUEST_TIMEOUT_SECONDS=30`
- `VOVAN_WORKER_SLEEP_SECONDS=5`
- `VOVAN_DOWNLOAD_DIR=./data/downloads`

## 2) Установка

```bash
make install
```

## 3) Проверка окружения

```bash
make doctor
```

## 4) Preflight файла

```bash
make preflight SAMPLE=./data/sample.txt
```

## 5) Placeholder OCR

```bash
make ocr SAMPLE=./data/sample.txt
```

## 6) One-shot worker dry-run

```bash
vovan worker --dry-run --once
```

## 7) One-shot worker live

```bash
vovan worker --live --once
```

В live режиме worker делает pull-flow:
1. claim следующей задачи;
2. если задач нет — `ok/no_job`;
3. download файла в `VOVAN_DOWNLOAD_DIR`;
4. local preflight;
5. placeholder OCR;
6. complete, либо `submit_failure` при preflight fail.

## 8) Docker Compose worker

```bash
make docker-worker
```

## 9) Где смотреть артефакты

- Загрузки: `./data/downloads`
- Логи: `./logs`
- Отчёты: `./reports`
