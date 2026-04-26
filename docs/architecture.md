# VOVAN Architecture (MVP)

## Роль VOVAN

VOVAN — это **локальный runtime-worker**, а не веб-сайт и не замена VLADCHER_ru.
Он запускается локально (Hackintosh/macOS), получает задания в pull-mode и готовится к переносу на Linux.

## Связь с VLADCHER_ru

Основной канал взаимодействия — HTTP API VLADCHER_ru.
Worker в этом MVP не принимает входящие подключения и не поднимает web-сервер.

## Pull-mode

Worker периодически запрашивает следующую задачу (`claim_next_job`),
скачивает входной файл (`download_job_file`) и отправляет результат (`submit_result`).
В текущем PR это dry-run/placeholder слой с понятными сообщениями.

## Почему API — основной канал

- проще обеспечить безопасность для локальной машины;
- не нужно открывать входящие порты на Hackintosh;
- устойчиво к нестабильному локальному IP/NAT.

## Почему Docker Compose

Docker Compose нужен для повторяемого запуска локального окружения.
Одинаковая сборка и команды запуска упрощают перенос и CI-проверки.

## GPU и ROCm

В macOS Docker GPU Radeon RX6800XT в этом PR не подключается.
ROCm/GPU рассматривается как будущий Linux-only слой и не входит в текущий MVP.
