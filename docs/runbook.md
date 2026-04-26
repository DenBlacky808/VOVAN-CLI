# VOVAN Runbook

## 1) Подготовка .env

```bash
cp .env.example .env
```

Заполните минимум:
- `VLADCHER_BASE_URL`
- `VOVAN_WORKER_TOKEN`

## 2) Установка

```bash
python3 -m pip install -e .[dev]
```

## 3) Проверка окружения

```bash
vovan doctor
```

## 4) Проверка файла preflight

```bash
vovan preflight data/sample.png
```

## 5) Placeholder OCR

```bash
vovan ocr data/sample.png
```

## 6) Запуск worker через Docker Compose

```bash
docker compose build vovan-worker
docker compose run --rm vovan-worker
```

## 7) Где смотреть результаты

- Логи: `logs/`
- Отчёты: `reports/`
