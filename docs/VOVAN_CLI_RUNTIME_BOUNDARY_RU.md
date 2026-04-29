# VOVAN-CLI Runtime Boundary

## Назначение

VOVAN-CLI — локальный вычислительный исполнитель. Он запускается на машине оператора, работает рядом с локальными файлами и системными инструментами, выполняет задачи локально и возвращает безопасные результаты наружу через явно заданные интеграционные каналы.

VOVAN-CLI не является:

- сайтом;
- macOS app;
- menubar app;
- только OCR-инструментом.

OCR — первый модуль внутри VOVAN-CLI. Он не определяет всю границу проекта.

## Отношение к macOS app

Будущая macOS app или menubar app может быть только оболочкой над CLI. Она не должна становиться местом, где живёт core logic: orchestration, processing pipeline, safety checks и отчётность должны оставаться переносимыми и доступными из CLI.

## Переносимость core

Core logic должен оставаться переносимым между:

- macOS;
- Linux;
- Docker;
- потенциально другими ОС.

macOS Intel / Hackintosh — первая целевая среда эксплуатации, но архитектурная граница не должна закреплять core за одной ОС.

OS-specific поведение должно жить в adapters, а не в core. Это касается запуска внешних программ, путей, уведомлений, system services, sandbox/permissions и любых интеграций с конкретной desktop-средой.

## Что может жить в core

Core может содержать:

- OCR pipeline;
- file indexing;
- manifest generation;
- safe summaries;
- task generation;
- verification reports;
- diagnostics.

Core должен работать с абстрактными входами, конфигурацией и явными adapter-интерфейсами, а не с приватными machine-specific деталями.

## Что не должно жить в core

Core не должен содержать:

- абсолютные приватные macOS paths;
- AppleScript-only логику;
- launchd-only логику;
- Finder-only поведение;
- destructive commands без safety layer.

Любое потенциально destructive действие должно проходить через safety layer: dry-run, allowlist, проверку scope, понятный audit trail и controlled failure вместо скрытых side effects.
