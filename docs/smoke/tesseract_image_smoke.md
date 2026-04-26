# Tesseract Image OCR Smoke (Hackintosh checkpoint)

Этот документ фиксирует успешный локальный smoke-тест OCR через Tesseract для изображений и задаёт безопасный следующий шаг: конфигурация языка OCR.

## Environment checkpoint

- Platform: Hackintosh (local run).
- Tesseract binary path: `/usr/local/bin/tesseract`.
- Tesseract version: `5.5.1`.

## Tesseract availability check

Перед запуском smoke-теста убедитесь, что Tesseract доступен в системе:

```bash
which tesseract
tesseract --version
```

Ожидаемо:
- `which tesseract` возвращает валидный путь (например, `/usr/local/bin/tesseract`).
- `tesseract --version` показывает установленную версию (в checkpoint: `5.5.1`).

## Supported image extensions

Текущий image smoke покрывает расширения:

- `.png`
- `.jpg`
- `.jpeg`
- `.tif`
- `.tiff`
- `.bmp`
- `.webp`

## Successful smoke command example

```bash
VOVAN_OCR_ENGINE=tesseract python -m vovan.cli ocr "<png screenshot>"
```

## Expected output fields

В успешном результате должны подтверждаться следующие поля:

- `engine_requested=tesseract`
- `engine=tesseract`
- `ocr_engine=tesseract`
- `result_text` non-empty (не пустой текст)

## Known limitation

Качество OCR зависит от:

- установленных language packs,
- качества входного изображения,
- используемого шрифта,
- разрешения изображения.

## NEXT (language configuration planning)

Короткий план следующего безопасного улучшения:

1. Добавить переменную конфигурации `VOVAN_TESSERACT_LANG`.
2. Значение по умолчанию: `eng`.
3. Позже разрешить комбинации вроде `rus+eng`.
4. Добавить в `doctor` вывод доступных language packs.

## Explicit non-goals for this checkpoint

- Не реализуем PDF preprocessing.
- Не меняем worker API.
- Не меняем placeholder default engine.
- Не добавляем heavy dependencies.
