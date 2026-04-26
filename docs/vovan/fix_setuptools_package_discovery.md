# fix_setuptools_package_discovery

## Проблема

На первом локальном запуске на Hackintosh команда:

- `python3 -m venv .venv`
- `pip install -e ".[dev]"`

падала с ошибкой setuptools:

`error: Multiple top-level packages discovered in a flat-layout: ['logs', 'data', 'vovan', 'reports']`.

## Причина

Репозиторий использует flat-layout, и без явной конфигурации package discovery `setuptools` пытается автоматически интерпретировать несколько верхнеуровневых директорий как пакеты. В результате вместе с целевым пакетом `vovan` подхватывались служебные директории (`logs`, `data`, `reports`).

## Применённый фикс

В `pyproject.toml` добавлена явная настройка discovery:

```toml
[tool.setuptools.packages.find]
include = ["vovan*"]
exclude = ["data*", "logs*", "reports*", "tests*", "docs*"]
```

Это ограничивает сборку только пакетами `vovan*` и исключает нерелевантные директории.

## Результаты Hackintosh smoke

После фикса подтверждено:

- `pip install -e ".[dev]"` проходит успешно;
- `vovan doctor` работает;
- `vovan preflight ./data/sample.txt` работает;
- `vovan ocr ./data/sample.txt` работает;
- `vovan worker` работает в dry-run;
- `pytest -q` проходит (`3 passed`).

## Итог

Фикс является минимальным, не меняет CLI-логику и устраняет проблему editable-install для локальной разработки.
