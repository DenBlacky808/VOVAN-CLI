# Tesseract image OCR smoke (local checkpoint)

This document captures a successful local smoke run for image OCR with Tesseract.

## Environment checkpoint (Hackintosh)

- `tesseract` path: `/usr/local/bin/tesseract`
- `tesseract` version: `5.5.1`

Availability checks:

```bash
which tesseract
tesseract --version
```

## Supported image extensions

Current image OCR path supports these input extensions:

- `.png`
- `.jpg`
- `.jpeg`
- `.tif`
- `.tiff`
- `.bmp`
- `.webp`

## Successful smoke command

```bash
VOVAN_OCR_ENGINE=tesseract python -m vovan.cli ocr "<png screenshot>"
```

Expected output fields for a successful run:

- `engine_requested=tesseract`
- `engine=tesseract`
- `ocr_engine=tesseract`
- `result_text` is non-empty

## Known limitation

OCR quality depends on:

- installed language packs
- image quality
- font
- resolution

## NEXT (safe incremental plan)

- add `VOVAN_TESSERACT_LANG`
- default value: `eng`
- allow combined languages later (for example `rus+eng`)
- add `doctor` output for available Tesseract language packs

## Non-goals for this checkpoint

- no PDF preprocessing
- no worker API changes
- no placeholder default changes
- no heavy dependencies
