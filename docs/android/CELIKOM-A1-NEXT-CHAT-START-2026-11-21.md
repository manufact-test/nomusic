# CELIKOM Android A1 — актуальная точка передачи
Дата обновления: 21.11.2026

## Рабочая точка
- Репозиторий: `manufact-test/nomusic`
- Единственная рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- HEAD перед текущей чисткой handoff: `156fdb09ab863d747fbd8068dd4c71aeecd77f39`; чистка создаёт следующий docs-only commit. В начале каждого нового чата получать фактический HEAD ветки через GitHub, не полагаться на старый SHA из сообщения.
- Последний пакетный/code snapshot BETA12: `21e00e7805640c7d8765b9180510005b8154798d`
- Функциональная линия: native change `65bc7a613762cef00fe9cbcff7c7949ea6af67de`; regression test `75b33733a2e8106823b1dcb4d7b3ac68298c9881`.
- С момента переданного владельцем HEAD `7081e467da212fd28c7f0d1de83eec147eaad60f` ветка продвинулась на 16 коммитов. Ветка не переключалась.
- Текущий HEAD — документационная фиксация результата BETA12; APK и код соответствуют пакетному коммиту выше.

## Цель и неизменные факты
Добиться реальной подмены на Android для Рамиля «Ау», выбранной напрямую из альбома:
- Album ID: `38902809`
- Yandex Track ID: `144530503`
- Активная одобренная альтернатива: №1
- Владелец подтвердил, что Windows CELIKOM и браузерное расширение подменяют эту же песню из этого же альбома. Не просить повторно доказывать соответствие песни и не предлагать искать её через «Мою волну».

## Последняя сборка BETA12
- Workflow export: [44898991151](https://github.com/manufact-test/nomusic/actions/runs/44898991151) — SUCCESS.
- Оба job успешны: JVM issuer-proxy contract и native ARM13.
- Artifact: `CELIKOM-A1-RAMIL-AU-BETA12-HONOR50-20261121`, ID `14705751633`, срок хранения до 28.11.2026.
- [Скачать ZIP BETA12](https://github.com/manufact-test/nomusic/actions/runs/44898991151/artifacts/14705751633)
- APK: `CELIKOM-A1-RAMIL-AU-BETA12-HONOR50-20261121.apk`, 71,581,676 bytes.
- SHA-256 APK: `9c802efbe099c4eb8da4fd51d9c66f779a5936ca622172163e4acfe1500d4b11`.
- Если потребуется повторная установка: ставить поверх BETA11, не удалять приложение и не очищать данные.

## Что доказали и чего не доказали проверки
- Workflow `44893907029` завершился SUCCESS. Его точный verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. Лог явно указывает `stage_a: NO_GO`, `acoustic_product_proven: false`; artifact отсутствует. Это проверка наблюдателя/совместной установки, а не подмена.
- JVM regression workflow `44897928916`: SUCCESS, результат `RAMIL_AU_ORIGINAL_TRACK_ONLY_BETA_LINEAGE_PASS`.
- ARM13 workflow `44897905526`: SUCCESS, scoped-module build и native ARM13 publisher-first 75s gate прошли.
- Clone-alone differential `44897905524`: SUCCESS; это safety check, не подтверждение звука.
- BETA12 export workflow `44898991151`: SUCCESS, но ни один CI не заменяет проверку реального звука на телефоне.

## Диагноз BETA11 — коротко
1. Creator Track+Album был обнаружен; тот же Track вошёл в Flow позже. Одноразовый поиск ID выполнялся слишком рано и не повторялся.
2. Source-bound `OWNER_RESOLVE_REQUEST` не состоялся. Был speculative prefetch; `OWNER_RESOLVE_NOT_APPROVED` — агрегированный маркер found/approved/entitled/MIME, а не доказательство отказа сервера для правильного Track ID.
3. Exo descriptor/factory/DataSource создавались и читали данные, но доказанной связи с выбранным Track не было. Оригинальные Exo reads не означают CELIKOM-подмену.
4. MP3/M4A parity mismatch Android-клиента исправлен, но известная запись «Ау» — MP3; не объявлять mismatch единственной причиной.

## Что изменено в BETA12
- `NativeRendererStreamEvidence` сохраняет точную lineage успешного оригинального Player source setter и повторно проверяет publisher ID после позднего Flow того же creator Track.
- `NativeEarlySourceLifecycleBridge` принимает поздний кандидат только для той же setter generation, запускает source-bound resolve один раз до prepare и отклоняет конфликтующие ID/кандидаты после prepare.
- Ограниченное pre-prepare ожидание включается только при доказанной связи allowlisted Track+Album с ожидаемым Flow того же Track; grant ожидается в том же bounded window.
- `StageBAudioEvidence` переносит точный TrackWrapper через исходный Player selection и MediaPeriod prepare. Wrapper восстанавливается только если source period — тот же объект, что прошёл успешный Player setter. Это позволяет существующим descriptor/factory/DataSource hooks наследовать корректный scope.
- Добавлены regression tests для позднего Flow, границы prepare, bounded wait и точной идентичности Player source → MediaPeriod → TrackWrapper.
- Это исправления в существующей цепочке, не новая архитектура. Не считать их доказанными на телефоне до анализа диагностики.

## BETA12 на телефоне: что выявлено 21.11.2026
Файл: `CELIKOM-A1-Diagnostics-1795261506252(1).txt`. Владелец слышит оригинал.

- Улучшение относительно BETA11: `ORIGINAL_CREATOR_KEY_CONFIRMED=FEW`, `ORIGINAL_SETTER=ONE`, `OWNER_RESOLVE_REQUEST=ONE` (раньше source-bound resolve не происходил).
- `OWNER_RESOLVE_APPROVED=NONE`, `OWNER_RESOLVE_NOT_APPROVED_FLAG=FEW`, `OWNER_RESOLVE_NOT_FOUND=NONE`, `OWNER_RESOLVE_NOT_ENTITLED=NONE`, `OWNER_NETWORK_OR_RESPONSE_ERROR=NONE`, `GRANT_ADMITTED=NONE`. Это оказалось **отсутствием** ключей ответа, а не явным серверным отказом.
- `EXACT_PREPARE=FEW`, `DECISION_ALTERNATE=NONE`, `DATASOURCE_ARMED=NONE`, `AUDIO_OPEN/READ=NONE`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`. Wrapper→descriptor/factory/DataSource всё ещё не подтверждён; исправление resolve ещё не доказывает звук.
- Старый `DIAGNOSTIC_BETA_BUILD=A1_TRACKID_BETA11...` в BETA12 был неизменённым маркером; для BETA13 метка исправлена.

## Установленная причина и исправление
- Выполнен **только читающий** SSH-аудит реально развёрнутого сервера через GitHub Actions: run `44902845389` SUCCESS. Действующий `ResolveService.php` SHA-256 `eb8069111eb10b236d4ae69fd70f4bb7da818048212d14dc960b16640d5bbe18`, не совпадает с кодом ветки (`c56a49b5a3703dea69794201cf4be4dbe3cbe133871de72d3edc574897eaa040`).
- Реальный API v1 выдаёт `found=true`, но без `approved` и `entitled`. В этом сервере каталог выбирает только approved + active + not disabled, а маршрут включает account/entitlement access и signed session URL. Live-строку БД через PHP CLI получить не удалось (`LIVE_DB_READONLY_CHECK=UNAVAILABLE`), не утверждать, что SQL-строка проверена. Сам сервер **не изменён**.
- Android `NativeOwnerControlPlane.approvedAudio()` раньше превращал отсутствие этих полей в false. Точечная правка `ab40154a81fc046b51e3b8b2e2662f30f916111b`: legacy-положительный ответ допускается только если оба поля отсутствуют, `found=true`, подписанный билет имеет строгую форму `/api/v1/audio/{id}?token=...&expires=...&sid=...`; explicit false, частичные схемы, чужие адреса/отсутствие sid отклоняются. Полный `NativeGrantContract`, оригинальные source/Track/Album проверки и реальная audio Range проверка остаются.
- JVM workflow `44903018408` SUCCESS (включая regression на legacy-safe контракт и Ramil lineage). ARM13 `44903018363`, clone-alone `44903018414` требуют проверки завершения. Одноразовый read-only audit workflow удалён, чтобы не захламлять репозиторий.

## BETA13 — реальный телефонный тест, итог 21.11.2026
- Последний code/package snapshot: `8a0cb99863e9e11d805141f87124990a0129c4f5`. HEAD перед фиксацией итогов: `e5d601d4f95e38f2ac22858d82bdb8976bcba66e` (следующий commit docs-only, проверять GitHub при возобновлении).
- BETA13 export workflow [44903467475](https://github.com/manufact-test/nomusic/actions/runs/44903467475) SUCCESS: JVM + ARM13 jobs зелёные, это не аудиоприёмка. JVM `44903467410` SUCCESS, clone-alone `44903467398` SUCCESS, native `44903018363` SUCCESS. Native verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- [BETA13 artifact](https://github.com/manufact-test/nomusic/actions/runs/44903467475/artifacts/14706654912), id `14706654912`, ZIP 51,709,505 bytes, истекает 28.11.2026. APK `CELIKOM-A1-RAMIL-AU-BETA13-HONOR50-20261121.apk`, SHA-256 `9cdca506afb01402e2fe50409f1ec129676849e76de0bebfe917288c2fcdf459`. Та же подпись, устанавливалась поверх предыдущей без очистки.
- Владелец проверил BETA13 на телефоне, Рамиль «Ау» из альбома `38902809`, и слышит **оригинал**. Итог: **CELIKOM_REPLACEMENT=NOT_CONNECTED**, подмена на Android не работает. Последний TXT: `CELIKOM-A1-Diagnostics-1795265503983.txt` (приложен к чату 21.11.2026, не хранится в GitHub).
- Маркер `DIAGNOSTIC_BETA_BUILD=A1_TRACKID_BETA13_AUTHENTICATED_LEGACY_RESOLVE_20261121` подтверждает именно BETA13. Лог `LOG_TRIMMED / KEEP_LAST_32KB`, поэтому нельзя восстанавливать точный порядок всех ранних событий по snapshot: используем агрегаты.
- Прогресс сравнительно с BETA12: `ORIGINAL_CREATOR_KEY_CONFIRMED=FEW`, `ORIGINAL_SETTER=ONE`, `OWNER_ENABLED=ONE`, `OWNER_RESOLVE_REQUEST=ONE`; `OWNER_RESOLVE_APPROVED=FEW`, `OWNER_RESOLVE_MPEG=FEW`, `OWNER_RESOLVE_NOT_APPROVED(_FLAG)=NONE`, `OWNER_RESOLVE_NOT_FOUND=NONE`, `OWNER_RESOLVE_NOT_ENTITLED=NONE`, `OWNER_RESOLVE_UNSUPPORTED_MIME=NONE`. Точечная BETA13 legacy-positive схема прошла этап одобрения. ВНИМАНИЕ: счётчики одобрения агрегированы по prefetch и source-bound resolve; не утверждать без трассы, что каждый успех относится именно к target ID `144530503`.
- Критический новый результат: `OWNER_NETWORK_OR_RESPONSE_ERROR=FEW`, одновременно `OWNER_SIGNED_GRANT_VALID=NONE`, `OWNER_RESPONSE_INVALID=NONE`, `OWNER_AUDIO_RANGE_VALID/REJECTED=NONE`, `SIGNED_AUDIO_READY=NONE`, `GRANT_ADMITTED=NONE`, `OWNER_SOURCE_WINDOW_CLOSED=NONE`, `OWNER_OFFER_REJECTED=NONE`. Отсутствие даже mark(valid/invalid grant) после положительного resolve делает **исключение при разборе JSON/конструировании grant** приоритетной гипотезой, но сам маркер совмещает сеть и JSON, это ещё не доказано.
- Кодовое место: `NativeOwnerControlPlane.java`: `requestForTrackIdBeta()`/prefetch -> `approvedAudio()` -> `readGrant()` -> `validTrialGrant()` -> `verifiedRange()`. `readGrant()` требует `audio_url,track_id,duration_ms,version,expires_at,mime_type` и преобразует `expires_at` * 1000. Реальный deployed PHP v1 отличается от репозиторного, как установлено прежним read-only SSH аудитом; проверить именно его поля/типы. `catch(Exception)` объединяет все ошибки в `OWNER_NETWORK_OR_RESPONSE_ERROR`. Не выводить чувствительные URL, токены или персональные данные в логи.
- Независимый неразрешённый seam: `EXACT_PREPARE=FEW`, `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=FEW`, но `LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH=NONE`, `LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_TRACK_ALBUM_MISSING=FEW`, `NATIVE_MAIN_SOURCE_ENTER=NONE`, `WRAPPER_MAIN_SOURCE=NONE`, `WRAPPER_DESCRIPTOR_LINK=NONE`, `TRACK_DESCRIPTOR_FACTORY_LINK=NONE`, `TRACK_FACTORY_SOURCE_LINK=NONE`, `TRACK_SOURCE_OPEN_LINK=NONE`, `TRACK_SOURCE_READ_LINK=NONE`. Exo factory/open/read MANY — это *оригинальная* музыка и не доказательство замены. `DECISION_ALTERNATE=NONE`, `DATASOURCE_ARMED=NONE`, `AUDIO_OPEN/READ=NONE`. `ISSUER_VALUE_TARGET_ALLOWLISTED=NONE` и `ISSUER_TRACKID=NONE`, поэтому не пытаться переносить чужие numeric IDs без доказанной связи.
- `METRICA_EXCEPTION_SUMMARY MUSIC_APP NONE`; fallback оригинала без признаков одобренного переключения. BETA13 **не прошла** акустическую приёмку.

## Очередь работ после паузы (НЕ исполнять до возобновления)
1. **P0 — замкнуть реальный server grant.** Только read-only выяснить фактическую схему successful deployed v1 `resolve` для нужного ID (список полей/типы/без значения подписанных секретов) и откуда `OWNER_NETWORK_OR_RESPONSE_ERROR`. Разделить в клиентской диагностике безопасные классы: HTTP/connection, JSON missing/type, construction/validation (без URL, токена, тела ответа). Проверить `readGrant()` на реальном контракте; не подменять обязательные поля выдуманными значениями, не убирать проверку подписи, expiry, scope и аудио Range. Добавить JVM regression на legacy-positive -> прочитанный grant.
2. **P1 — acceptance grant до prepare.** Довести `OWNER_SIGNED_GRANT_VALID`, `OWNER_AUDIO_RANGE_VALID`, `GRANT_ADMITTED` для точной пары Track `144530503` / Album `38902809`; сохранить fail-closed, тот же owner, ту же setter generation, никаких общих/latest track хаков. Не увеличивать вслепую окно ожидания: `OWNER_SOURCE_WINDOW_CLOSED=NONE`.
3. **P2 — закрыть native lineage.** Продолжать от доказанного оригинального Player setter и *того же* source на `LivePeriod`, связать exact Track+Album с wrapper и descriptor/factory/DataSource; сейчас missing Track album on scoped wrapper period. Избегать unrelated renderer/comparator маршрутов; цель `LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH`, `WRAPPER_DESCRIPTOR_LINK`, `TRACK_SOURCE_OPEN/READ_LINK`. Не трогать закрытые LyEa/LCK1.
4. **P3 — end-to-end.** После code fix: targeted JVM regressions -> ARM13/native + clone-alone CI -> *один* APK с прежней подписью (не начинать новый клиент) -> одна проверка «Ау» 00:43–00:54. Успех только при `DECISION_ALTERNATE`, `DATASOURCE_ARMED`, `AUDIO_OPEN/READ` и подтверждённом звуке. Зелёный CI — не подтверждение подмены.

## Пауза / передача
По просьбе владельца **21.11.2026 остановить Android CELIKOM A1** для переноса других частей CELIKOM на другую платформу. Этот коммит — **только документация**: не менять Java/PHP, не менять branch/main, не запускать CI и не выпускать новый APK. При возвращении сначала прочитать этот файл, проверить текущий HEAD и приступать к P0; без новых вопросов владельцу о уже известных ID/альбоме/правильности одобрения альтернативы. Не обещать, что APK рабочая.

## Жёсткие ограничения
- Не начинать проект заново, не менять архитектуру, не повторять NAV40/NAV45.
- Не трогать закрытые маршруты LyEa/LCK1.
- Не ослаблять Track ID, Album ID, source identity, подписи или fail-closed проверки.
- Не менять сервер/оригинальный Яндекс.
- PHP-код живого сервера проверен read-only SSH, но SQL-строку действующей БД прочитать не удалось. Не заявлять, что БД проверена или подтверждён звук.
- Работать крупными последовательными блоками; без мелких промежуточных отчётов.

## Документация
Этот файл — единственная актуальная точка входа для следующего чата. Старые датированные отчёты и BETA handoff-файлы оставлены как исторические доказательства; не читать их пачкой и не удалять массово. Открывать только конкретный документ, если последняя диагностика или исходный код прямо на него ссылаются.

## Возобновление P0 — 21.11.2026
- Сверен SHA-256 прошлого live read-only SSH audit с историческим `server/src/Application/ResolveService.php` из `526b4f5b3560f65f2d04aa783a97b8e58e1fd27d`: точное совпадение `eb8069111eb10b236d4ae69fd70f4bb7da818048212d14dc960b16640d5bbe18`. Код позитивного ответа реально развёрнутой на момент аудита версии содержит `found,replacement_id,audio_url,duration_ms,mime_type,version,gain_db,gain_applied,expires_at,cache_ttl_seconds`, **нет track_id**. В BETA13 `readGrant().getString("track_id")` выбрасывает JSONException после approvedAudio до signedTrialGrant. Это объясняет провал BETA13, но не подтверждает endpoint после переезда и не доказывает звук.
- Добавлена узкая совместимость для исключительно authenticated trial resolve request: точная историческая legacy-схема без echo ID связывается с ID именно данного запроса (catalog findActive выбирает service+track), URL replacement_id сверяется, gain_applied=false для legacy без echo. Explicit mismatch/null, отсутствие SID, modern без echo, partial flags и invalid numeric fields отклоняются. Никакой синтез Album/Edition и original-source identity. Certified source path и session checks не менялись; NativeGrantContract, Range и source generation guard остаются. Добавлены безопасные диагностические категории и regression fixture `DEPLOYED_V1_RESOLVE_REQUEST_BOUND_GRANT_PASS`. CI/phone пока не подтверждены. P1/P2 не считать закрытыми.

## 24.11.2026 — infrastructure migration checkpoint, no playback change
- Existing A1 branch code `f21e1f22cbaedf1074d50b52ee21a9f11f49bf8a`, previous playback checkpoint `8475b67be3789a0cb3bd05d1bbaf7d448d87c15a`. NativeOwnerControlPlane API origin and both legacy ApiContract constants moved to https://api.celikom.com; exact grant checks/owner identity/diagnostics/audio route remain unchanged. No APK distributed. A1 CI #45433334062 queued at checkpoint; confirm outcome.
- FlokiNET music/catalog and auth secrets verified; public API currently health/config only, full auth/resolve NOT switched. Do not interpret network failures from this candidate as new playback root cause before server cutover. Legacy Android stable 0.3.92 update feed and build-input delivery not switched yet; do not disable Hostinger or alter signed update trust. Resume actual A1 audio task only after confirmed API readiness. See main docs/migration/CELIKOM-NEXT-CHAT-START-2026-11-23.md. Existing failure/owner diagnostics still authoritative.
