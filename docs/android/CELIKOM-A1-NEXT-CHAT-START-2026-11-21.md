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

## Следующий шаг
После зелёного native CI экспортировать BETA13 одним owner-phone APK. Один тест той же «Ау» непосредственно из альбома: 00:43–00:54. Никаких ADB, очистки данных или повторного логина.

Если ещё оригинал, проверить в TXT сначала `OWNER_RESOLVE_APPROVED`, `GRANT_ADMITTED`, `DECISION_ALTERNATE`, `DATASOURCE_ARMED`, `AUDIO_OPEN/READ`, затем source lineage. Не начинать NAV40/NAV45 и не выпускать диагностические APK без правки. Только реальное звучание подтверждает успех.

## BETA13 — собрана, ждёт реального звукового теста
- Последний пакетный/code HEAD: `8a0cb99863e9e11d805141f87124990a0129c4f5`. Это commit сборки именно BETA13, ветка прежняя.
- BETA13 export workflow `44903467475` SUCCESS: оба job `jvm-issuer-proxy-contract` и `actual-2025-own-lspatch2-disposable-native-arm13` SUCCESS. Важный verdict native остаётся `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`: это safety gate, НЕ акустическая приёмка.
- JVM `44903467410` SUCCESS, clone-alone `44903467398` SUCCESS. Предшествующий полный native `44903018363` SUCCESS.
- [BETA13 GitHub artifact](https://github.com/manufact-test/nomusic/actions/runs/44903467475/artifacts/14706654912), artifact ID `14706654912`, ZIP 51,709,505 bytes, живой до 28.11.2026. Имя APK внутри: `CELIKOM-A1-RAMIL-AU-BETA13-HONOR50-20261121.apk`. Его SHA-256 по GitHub native export log: `9cdca506afb01402e2fe50409f1ec129676849e76de0bebfe917288c2fcdf459`.
- Owner signer совпал с сохранённым установленным сертификатом; свежая установка не разрешалась, процесс сборки был настроен на обновление имеющегося приложения без сброса данных.
- Инструкция владельцу дана: установить BETA13 поверх BETA12 без удаления и очистки данных, включить «Ау» из альбома `38902809`, проверить `00:43–00:54`. Если звучит оригинал — прислать TXT. **Результат на телефоне пока не получен; не объявлять подмену работающей.**
- В BETA13 устранён именно обнаруженный сбой совместимости с legacy-сервером. Второй блокер `wrapper → descriptor/factory → unopened DataSource` оставался недоказанным в BETA12 и может проявиться следующим; продолжать по новому TXT, не заниматься повторно NAV40/NAV45 и не возвращаться к уже проверенному серверному формату без оснований.

## Жёсткие ограничения
- Не начинать проект заново, не менять архитектуру, не повторять NAV40/NAV45.
- Не трогать закрытые маршруты LyEa/LCK1.
- Не ослаблять Track ID, Album ID, source identity, подписи или fail-closed проверки.
- Не менять сервер/оригинальный Яндекс.
- PHP-код живого сервера проверен read-only SSH, но SQL-строку действующей БД прочитать не удалось. Не заявлять, что БД проверена или подтверждён звук.
- Работать крупными последовательными блоками; без мелких промежуточных отчётов.

## Документация
Этот файл — единственная актуальная точка входа для следующего чата. Старые датированные отчёты и BETA handoff-файлы оставлены как исторические доказательства; не читать их пачкой и не удалять массово. Открывать только конкретный документ, если последняя диагностика или исходный код прямо на него ссылаются.
