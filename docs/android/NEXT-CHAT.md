# CELIKOM Android A1 — NEXT CHAT

Репозиторий: `manufact-test/nomusic`
Ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Текущая версия
- На телефоне проверена BETA36 NAV56 — слышимой подмены нет.
- Готовится BETA37 NAV57. Не устанавливать старую BETA36 повторно; дождаться owner-only APK из CI run `46163744419`.

## Что установлено
- BETA36 диагностика: `CELIKOM-A1-Diagnostics-1795880627662.txt`.
- First-open: кандидат принят; deferred arm принят; `DATASOURCE_ARMED=ONE`.
- Альтернативный DataSource реально открывался и отдавал байты: `AUDIO_OPEN=ONE`, `AUDIO_READ=MANY`.
- Но связь этих байтов с текущим MediaPeriod не была зафиксирована: `LIVE_PERIOD_SOURCE_LOOKUP_CALL=NONE`.
- Renderer read наблюдался при state != 2; `ENGINE_HOLDER_TYPE1_STATE2=NONE`. Старый код прекращал source lookup до чтения текущего PeriodID/MediaPeriod.
- NAV55 уже подтвердил прямой `Lo96` MediaPeriod в select/attach/read. Не повторять holder-аудит.
- NAV56 сохраняет exact first-open DataSource после очистки creator history. Не переделывать этот путь.
- BETA35 диагностика имела устаревший маркер BETA34; не путать её с BETA34.

## NAV57 — изменение
- Source lookup теперь запускается и на renderer read при state != STATE_STARTED.
- Проверяется точный текущий PeriodID (UID + оба индекса) вместе с текущим SLOT_B и source identity.
- Это read-only source correlation. Не считать её доказательством audible PCM.
- STATE_STARTED/decoder evidence остаётся отдельным строгим условием.
- MP3/AAC override и audio route не менялись. Не повторять BETA32 codec override без нового доказательства.

## Проверки
- JVM regression tests: PASS.
- Полный BETA36 ARM13 publisher-first side-by-side 75s gate: PASS, verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- BETA37 JVM contract: PASS.
- BETA37 ARM13 publisher-first side-by-side gate: CI run `46163744419`, сейчас выполняется. Clone-only differential `CLONE_ONLY_MASTER_KEY_INIT_OR_MAIN_NO_GO` — отдельный диагностический NO_GO, не product acceptance; publisher intentionally absent.

## Следующий шаг
1. Дождаться успешного BETA37 ARM13 gate и owner-only draft APK.
2. Установить BETA37 поверх BETA36, не удалять приложение и не очищать данные.
3. Проверить Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, 00:43–00:54.
4. Сохранить диагностику CELIKOM.

В новой диагностике проверить:
- `LIVE_QUEUE_SLOT_B_TYPE1_NOT2_READ_MATCH`
- `LIVE_QUEUE_SLOT_B_TYPE1_NOT2_PERIOD_ID_SAME`
- `LIVE_PERIOD_SOURCE_LOOKUP_CALL` / `LIVE_PERIOD_SOURCE_LOOKUP_RESOLVED`
- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS` или `..._EOS_UNKNOWN`

Если альтернативный read связан с текущим MediaPeriod — следующий этап decoder/format, без повторного DataSource-аудита. Если нет — исправлять только конкретное несовпадение source identity.
