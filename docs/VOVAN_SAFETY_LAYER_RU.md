# VOVAN Safety Layer Directive

Эта директива фиксирует границы безопасности для VOVAN-CLI как локального исполнителя.
VOVAN не должен выполнять destructive actions без safety layer, даже если команда технически доступна локально.

## 1. Emergency stop / kill switch

VOVAN должен иметь операционный режим немедленной остановки.

При активном emergency stop VOVAN:

- прекращает запуск новых задач;
- не выполняет файловые изменения;
- не удаляет, не перезаписывает и не перемещает данные;
- завершает текущий шаг controlled failure, если продолжение может изменить состояние;
- пишет только безопасный status/audit event без секретов и приватных путей.

Emergency stop имеет приоритет над обычными настройками, очередью задач и пользовательскими shortcut-командами.

## 2. Allowed folders

Запись разрешена только в явно определённые рабочие области VOVAN.

Разрешённые зоны должны быть заданы как repo-relative или config-relative allowlist, например:

- рабочая директория проекта;
- временная директория, созданная VOVAN для текущей задачи;
- директория логов VOVAN;
- директория отчётов VOVAN;
- явно переданная output-директория, прошедшая preflight.

Даже внутри allowed folders destructive actions требуют dry-run и подтверждения, если действие удаляет, перезаписывает или делает необратимое изменение.

## 3. Forbidden folders

VOVAN не должен выполнять запись, удаление, перезапись или рекурсивные операции в forbidden folders.

К forbidden folders относятся:

- системные директории ОС;
- домашние директории пользователя целиком;
- директории ключей, SSH, password manager, browser profiles и cloud credentials;
- директории с `.env`, secrets, tokens, credentials;
- production settings и production deploy/config directories;
- реальные документы пользователя, raw OCR, scans, PDFs и архивы с ними;
- `.git` и служебные директории системы контроля версий;
- внешние mount points, cloud sync folders и removable media, если они не добавлены в явный allowlist.

Если путь совпадает сразу с allowed и forbidden правилом, применяется forbidden правило.

## 4. Read-only mode для неизвестных директорий

Любая директория вне явного allowlist считается unknown scope.

Для unknown scope действует read-only mode по умолчанию:

- разрешены только чтение метаданных и безопасный preflight;
- запрещены delete, overwrite, move, chmod, chown, truncate, clean, prune и bulk rename;
- запрещены рекурсивные операции с изменением состояния;
- результатом попытки записи должен быть controlled failure.

Unknown scope нельзя автоматически повышать до writable на основании того, что команда успешно стартует.

## 5. Dry-run перед destructive actions

Перед любым destructive action VOVAN обязан выполнить dry-run.

Dry-run должен показать:

- тип действия;
- количество затронутых файлов или объектов;
- repo-relative, masked или normalized scope;
- причину действия;
- expected result;
- список блокирующих safety warnings.

Dry-run не должен читать или печатать содержимое приватных документов, OCR raw text, secrets, tokens или credentials.

## 6. Запрет удаления без явного подтверждения

Удаление запрещено без явного подтверждения.

Подтверждение должно быть:

- отдельным от исходной команды;
- привязанным к конкретному dry-run result;
- ограниченным конкретным scope;
- одноразовым для текущей операции;
- недействительным после изменения scope, количества объектов или типа действия.

Фразы вроде "почисти всё", "удали старое", "сделай как надо" не являются достаточным подтверждением для удаления.

## 7. Destructive command blocker

Safety layer должен блокировать команды и операции, которые могут необратимо изменить данные.

К destructive operations относятся:

- delete/remove;
- overwrite existing file;
- truncate file;
- move с потерей исходного расположения;
- recursive chmod/chown;
- clean/prune/purge;
- reset/revert локальных изменений без явного запроса;
- mass rename;
- запись за пределами allowed folders;
- отправка приватных данных во внешний сервис.

Если операция попадает в destructive class, она должна пройти allowlist check, forbidden check, dry-run и explicit confirmation.

## 8. Audit log без секретов и приватных путей

Каждое safety decision должно оставлять audit event.

Audit event может содержать:

- timestamp;
- command category;
- decision: allowed, blocked, dry-run-only или controlled-failure;
- normalized или repo-relative scope;
- count of affected objects;
- reason code;
- short human-readable reason.

Audit event не должен содержать:

- значения env vars;
- tokens, passwords, API keys, cookies или auth headers;
- абсолютные приватные пути;
- содержимое документов, raw OCR, scans, PDFs;
- stack traces с machine-specific diagnostics.

Если безопасно записать audit event невозможно, VOVAN должен остановить действие и вернуть controlled failure.

## 9. Controlled failure вместо опасного действия

При нарушении safety rule VOVAN должен завершить операцию controlled failure.

Controlled failure должен:

- не менять состояние файловой системы;
- не продолжать частичное destructive action;
- объяснять, какое правило сработало;
- предлагать безопасный следующий шаг, например dry-run или уточнение scope;
- не раскрывать секреты, приватные пути или содержимое документов.

Опасное действие нельзя выполнять "частично", чтобы потом восстановить состояние.

## 10. Если scope непонятен - остановиться

Если VOVAN не может однозначно определить scope операции, он обязан остановиться.

Остановка обязательна, если:

- путь отсутствует, неоднозначен или раскрывается в несколько директорий;
- glob или recursive pattern затрагивает unknown или forbidden scope;
- команда зависит от текущей директории, но она не подтверждена;
- dry-run result не совпадает с исходным намерением;
- есть риск затронуть реальные документы, raw OCR, scans, PDFs, secrets или production settings.

Правило по умолчанию: unclear scope means stop.
