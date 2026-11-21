# CELIKOM Android A1 — BETA9 / следующая диагностика владельца (21.11.2026)

## Фиксированная точка

- Repo: `manufact-test/nomusic`.
- **Только** branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Последний функциональный код: [`7fac727c70085a51ce35e8f35c9fa3b2387ffdf5`](https://github.com/manufact-test/nomusic/commit/7fac727c70085a51ce35e8f35c9fa3b2387ffdf5) (BETA9). Не путать с HEAD документации — читать ветку при старте следующего чата.
- **Дальнейшая работа начинается с нового реального owner TXT BETA9**, который пользователь отправит в следующий чат. Не начинать проект заново и не выпускать BETA10 до анализа этой диагностики.
- Цель: подмена разрешённой альтернативы в **том же** оригинальном Яндекс/Exo player, без второго проигрывателя и второго входа. HONOR 50 / Android 13. Тест: Ramil' «Ау», original track ID `144530503`, **00:43–00:54**, результат устанавливается на слух владельца.
- Test.50, NAV40, NAV45, Windows, backend, оригинальный подписанный Яндекс APK не менять. Отдельную BETA кнопку и второй логин не возвращать; кнопка статуса/экспорта TXT — сверху справа `CELIKOM: ВКЛ · TXT`; saved CELIKOM session автоматически запускает owner flow.

## Доказательство провала BETA8

HONOR 50 owner TXT `CELIKOM-A1-Diagnostics-1795247871997.txt`: `OWNER_ENABLED=ONE`, `ISSUER_PROXY_CREATED=ONE`, `ISSUER_METHOD_SELECTED=ONE`, `ISSUER_HANDLER_INVOKE=FEW`, `ISSUER_VALUE_TARGET_ALLOWLISTED=ONE`, `ISSUER_VALUE_SCOPE_PRESENT=NONE`, `ISSUER_VALUE_SCOPE_ABSENT=FEW`, `ISSUER_TRACK_SCOPE_MISSING=ONE`, `ISSUER_TRACKID=NONE`, `ORIGINAL_SETTER=NONE`, `PREFETCH_STARTED=NONE`, `GRANT_ADMITTED=NONE`, `DATASOURCE_ARMED=NONE`, `AUDIO_READ=NONE`. Настоящий `@Query("trackId")` проходит original Retrofit handler **без Track ThreadLocal scope**; origin Exo продолжает играть оригинал. Из TXT нельзя утверждать точную нить/порядок событий.

## Что реализовано в BETA9

Код `StageBAudioEvidence.java`: в отсутствие Track ThreadLocal оригинальный **allowlisted** issuer ID записывается только в RAM максимум на 30 секунд и передаётся существующему owner prefetch. Связь разрешается только при полном совпадении **исходного numeric ключа подписанного original `tCa(String)`**, identity того же original Track+Album+Wrapper или проверенного Track+wrapper без Album, и original source setter. Механизм fail-closed; без глобального «последнего трека», угадывания ID, подмены Retrofit запросов или произвольного audio grant.

Маркеры BETA9: `DIAGNOSTIC_BETA_BUILD=A1_TRACKID_BETA9_EXACT_ASYNC_ISSUER_CREATOR_20261121`, `ISSUER_ASYNC_ID_OBSERVED`, `ISSUER_ASYNC_CREATOR_BOUND`, `ISSUER_ASYNC_CREATOR_STALE`. JVM fixture проверяет совпадение original identities, отсутствие ticket, истечение срока, чужой original ключ, Album конфликт и late Flow без Album.

CI **SUCCESS** (это НЕ проверка звука): [paired original-first + JVM #44883122288](https://github.com/manufact-test/nomusic/actions/runs/44883122288), [clone-only Android13 #44883122281](https://github.com/manufact-test/nomusic/actions/runs/44883122281), native verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. Signed installer `UPDATE_EXISTING`; signer SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`. Подтверждённого звучания альтернативы на HONOR 50 **пока нет**.

## Где владельцу брать BETA9

- **В Библиотеку ChatGPT уже загружен и повторно проверен** файл `/CELIKOM-A1-RAMIL-AU-BETA9-HONOR50-20261121.apk`; Files `files.manage_library` ответил `status=succeeded`, `library_file_id=libfile_ed79781b3ecc81918ce9de2bf6da5e1b`, 71,577,580 bytes. Пользователь сообщил, что прошлый `sandbox:` линк на APK не скачивается, **не повторять его как надёжный**. Прямой публичный URL для library record не предоставлен.
- GitHub fallback: [artifact #14698319574](https://github.com/manufact-test/nomusic/actions/runs/44883122288/artifacts/14698319574), требует GitHub login; это ZIP с APK.
- SHA256 APK `d17ef52602cb4d8bd4978e71cffbbd6085789162ff5ecab234678842d3ac37f6`. Установка **поверх BETA8**, без удаления приложения и данных. Сам факт загрузки файла в библиотеку не подтверждает, что владелец установил BETA9.

## Следующий проход — без отвлечений

1. Прочитать **фактически приложенный новый owner TXT**, удостовериться в `DIAGNOSTIC_BETA_BUILD` и `OWNER_ENABLED` (может оказаться BETA8, если скачать/установить BETA9 не удалось). Не предполагать, что это BETA9.
2. Разобрать по очереди: `ISSUER_PROXY_CREATED`, `ISSUER_HANDLER_INVOKE`, `ISSUER_VALUE_TARGET_ALLOWLISTED`, `ISSUER_VALUE_SCOPE_ABSENT`, `ISSUER_ASYNC_ID_OBSERVED`, `ISSUER_ASYNC_CREATOR_BOUND`, `ISSUER_ASYNC_CREATOR_STALE`, `ISSUER_TRACKID`, `EXACT_BETA_CREATOR`, `ORIGINAL_SETTER`, `PREFETCH_STARTED`, `SIGNED_MPEG_READY`, `OWNER_RESOLVE_REQUEST`, `GRANT_ADMITTED`, `EXACT_PREPARE`, `DECISION_ALTERNATE`, `DATASOURCE_ARMED`, `AUDIO_OPEN`, `AUDIO_READ`.
3. Если async issuer виден, но creator не bound — проверить actual original `tCa(String)` key / оригинальные identity и окно 30s; не вносить глобальную привязку к треку. Если bound, но original setter absent — проверить exact original setter/source generation. Если issuer+setter есть, но grant/prepare/audio отсутствуют — локализовать **первый отсутствующий** signed owner/source/DataSource этап, исправить только его.
4. Один маленький обоснованный code fix, регрессионные JVM тесты, GitHub native ARM13 paired + clone CI, **один** signed APK, подписанный тем же сертификатом, через Библиотеку; телефонный тест звука. Отдельный диагностический билд ради статусов без движения к звуку не делать.
5. Из TXT не публиковать user tokens, account, signed URI и raw IDs. Не объявлять product PASS по CI. После подтверждённого звука уже проверять Pause/Seek/Next/MyWave.

## Куда смотреть в коде

- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/StageBAudioEvidence.java`
- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/ExitCallsiteWitness.java`
- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/NativeTrackIdBetaPolicy.java`
- `android/native-yandex-hooklab/ci/test_a1_stage_b_audio_evidence.py`
- Оригинальный signed owner source/route: `NativeOwnerControlPlane`, `NativeEarlySourceLifecycleBridge`, `NativeExoAlternateByteRoute`.
