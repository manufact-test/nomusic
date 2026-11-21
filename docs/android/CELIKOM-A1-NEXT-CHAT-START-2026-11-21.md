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

## Следующий шаг
Ожидаемый следующий вход — TXT-диагностика владельца после проверки BETA12. Сначала прочитать её целиком и сопоставить фактические события:
- publisher Track ID и точный source-bound resolve;
- ответ/причина grant gate;
- original Player setter и его generation;
- descriptor → factory → тот же unopened DataSource;
- `DECISION_ALTERNATE`, `DATASOURCE_ARMED`, `AUDIO_OPEN/READ`.

Не просить повторно устанавливать APK, делать скриншоты, использовать ADB/кабель/PowerShell/IDE, если диагностика не покажет реальную необходимость. Не выпускать APK ради новых счётчиков. Следующий шаг должен исправлять конкретный разрыв, обнаруженный в последней диагностике.

## Жёсткие ограничения
- Не начинать проект заново, не менять архитектуру, не повторять NAV40/NAV45.
- Не трогать закрытые маршруты LyEa/LCK1.
- Не ослаблять Track ID, Album ID, source identity, подписи или fail-closed проверки.
- Не менять сервер/оригинальный Яндекс.
- Не утверждать, что live Hostinger/admin DB проверена: в предыдущей сессии авторизованного доступа к ней не было. Проверять самостоятельно только если доступный авторизованный браузер реально есть.
- Работать крупными последовательными блоками; без мелких промежуточных отчётов.

## Документация
Этот файл — единственная актуальная точка входа для следующего чата. Старые датированные отчёты и BETA handoff-файлы оставлены как исторические доказательства; не читать их пачкой и не удалять массово. Открывать только конкретный документ, если последняя диагностика или исходный код прямо на него ссылаются.
