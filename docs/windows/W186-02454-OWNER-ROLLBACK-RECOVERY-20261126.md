# W186 — восстановление точного owner-accepted CELIKOM Windows 0.24.54 (26.11.2026)

> **SUPERSEDED после фактического owner-теста 26.11.2026. НЕ ПОВТОРЯТЬ прежнюю процедуру очистки DPAPI.**
>
> Владелец установил 0.24.54, приложение запустилось, но вход завершился общей ошибкой. Предыдущий шаг с удалением `session.dpapi` заставляет W173 0.24.54 использовать старый Hostinger origin по умолчанию, а не Floki. Проверка Hostinger health/config не подтверждала вход владельца. Подробный разбор и правильный план — [W187](./W187-02454-HOSTINGER-LOGIN-FAILURE-FLOKI-API-RECOVERY-20261126.md).
>
> **Не удалять повторно CELIKOM/session.dpapi, не переустанавливать и не просить владельца снова входить в старую сборку.** Требуется owner-only кандидат от точного W174 audio baseline с минимальным Floki origin migration backport. Login и audible replacement пока не подтверждены.


## Цель

Владелец запросил вернуть последнюю реально принятую рабочую Windows-версию, не создавать очередной speculative audio-hook candidate.

## Найден точный W173 owner package

Использован GitHub Actions run [44894407351](https://github.com/manufact-test/nomusic/actions/runs/44894407351), artifact ID `14703029534`, name `CELIKOM-Windows-internal-stage-0fe5729f3e6f51e2679bf1cbec2dc6cedb81c27d`.

Artifact был загружен, распакован, SHA-256 пересчитан локально:

- EXE: `CELIKOM-W173-START-UX-02454-UNSIGNED.exe`
- EXE size: 85,134,903 bytes
- EXE SHA-256: `da5877bb01dca6048ce85cb07881f663c3a16cb81ec1f3b16074837bf9b60f33`
- ZIP: `CELIKOM-Windows-0.24.54.zip`
- ZIP SHA-256: `d719af9688d74230440887707b9a6cd1c8e2b08af6026cd406c909fd4d3fb4b3`

Оба хеша совпадают с исходной W173 документацией. Это точный owner-stage package, принятый владельцем до миграции. Не путать с более поздним W20 internal artifact 14705515606: у него другой EXE hash и он не является исходным W173 package.

Установщик — internal owner-stage, без Authenticode подписи. Это не новый signed/customer release.

## Проверка прежнего API

Hostinger monitor run [45759107905](https://github.com/manufact-test/nomusic/actions/runs/45759107905), 26.11.2026 11:38 UTC, проверял именно старый origin `https://darkred-camel-588676.hostingersite.com`:

- `/api/v1/health`: HTTP 200
- `/api/v1/config`: HTTP 200
- anonymous resolve: HTTP 401 (ожидаемый ответ без авторизации)

Это подтверждает доступность health/config routes, но не подтверждает вход владельца, состояние его старой сессии или успешный resolve с его аккаунтом.

## Почему простая установка EXE не делает полный rollback

W173 0.24.54 загружает сохранённую DPAPI-сессию и использует сохранённый `Origin`, если он задан. После миграции 0.24.55 этот origin в `%LOCALAPPDATA%\CELIKOM\Windows\session.dpapi` был переведён на `https://api.celikom.com`.

Поэтому установка старого EXE поверх 0.24.60 без очистки сохранённого входа оставит Floki origin. Это не вернёт прежнюю связку.

## Проверенная процедура возврата

Исходный W173 Inno Setup script проверен:

- При удалении предлагает checkbox «Также удалить сохранённые данные входа», по умолчанию выключен.
- До удаления требует успешный `--restore-native`; при ошибке удаление отменяется.
- При явной отметке удаляет только точный файл `%LOCALAPPDATA%\CELIKOM\Windows\session.dpapi`.
- Не удаляет рекурсивно AppData, Yandex-файлы, trial или subscription на сервере.
- В W173 installer файлы устанавливаются с `ignoreversion`; отдельной проверки, запрещающей in-place downgrade, в Inno Setup script нет.

Шаги владельца:
1. Закрыть Yandex Music и CELIKOM.
2. Удалить CELIKOM штатным деинсталлятором Windows.
3. В диалоге удаления отметить «Также удалить сохранённые данные входа».
4. Установить точный W173 0.24.54 EXE.
5. Войти заново — новая пустая сессия использует старый Hostinger origin.
6. Проверить реальный звук на известной замене track `144530503` («Ау»), затем Next и Play/Pause.

Если owner login к Hostinger не работает, не делать повторные переустановки и не менять Yandex hook. Это отдельная проблема auth/API. До личного прослушивания возврат считается подготовленным, но не подтверждённым.

## Repository safety

Перед записью документации создан backup branch:

- `backup/windows-main-pre-02454-restore-20261126`
- preserved HEAD: `bd942f423c922b8d51cbf2931c285e035c4d65c7`

No runtime files, API deployment, customer manifest, Android, extension, or Floki services were changed as part of this artifact recovery.