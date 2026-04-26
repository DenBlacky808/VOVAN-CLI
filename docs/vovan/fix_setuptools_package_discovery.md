# fix_setuptools_package_discovery

## Ошибка

На Hackintosh первый локальный запуск после создания виртуального окружения и установки dev-зависимостей:

- `python3 -m venv .venv`
- `pip install -e ".[dev]"`

падал с ошибкой setuptools:

- `error: Multiple top-level packages discovered in a flat-layout: ['logs', 'data', 'vovan', 'reports']`

## Причина

Проект использует flat-layout, а в `pyproject.toml` не была задана явная конфигурация package discovery для setuptools.
Из-за этого setuptools пытался автоматически обнаруживать top-level пакеты и воспринимал служебные директории (`logs`, `data`, `reports`) как Python-пакеты.

## Применённый фикс

В `pyproject.toml` добавлена явная конфигурация package discovery:

```toml
[tool.setuptools.packages.find]
include = ["vovan*"]
exclude = ["data*", "logs*", "reports*", "tests*", "docs*"]
```

Эта настройка ограничивает сборку только пакетами `vovan*` и исключает служебные/документальные директории.

## Hackintosh smoke results

После фикса локально подтверждено:

- `pip install -e ".[dev]"` проходит успешно;
- `vovan doctor` работает;
- `vovan preflight ./data/sample.txt` работает;
- `vovan ocr ./data/sample.txt` работает;
- `vovan worker` работает в dry-run режиме;
- `pytest -q` — `3 passed`.

## Итог

Фикс минимальный и mergeable:

- CLI-логика не менялась;
- real OCR не подключался;
- live API не подключался;
- Docker-конфигурация не менялась.
