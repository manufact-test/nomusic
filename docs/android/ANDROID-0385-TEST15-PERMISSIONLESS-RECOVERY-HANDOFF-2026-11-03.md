# CELIKOM Android — Test.15 recovery / permission-free seek investigation / handoff
Дата: 2026-11-03. **Статус: Test.16 ОТКЛОНЕНА владельцем; Test.15 — подтверждённый лучший полевой эталон.**

## 1. Единственная корректная основа следующей работы

- Репозиторий: https://github.com/manufact-test/nomusic
- **Новая рабочая ветка для следующего чата:** `feature/android-0385-test15-permissionless-recovery-20261103`, создана **не из Test.16**, а из backup Test.15. Начальные функциональные файлы в ней совпадают с Test.15; последующие коммиты этого handoff — только документация.
- Неприкосновенная резервная Test.15: `backup/android-0385-test15-best-owner-20261103`, SHA `6fde1e48179ecb812f1def16067f18bf0d9c3003`. Функциональный SHA Test.15 `4838ccee4aa4628dce68437ebbf00d4dfc30ce27`. Отдельное приложение `pro.celikom.nativeprobe.test`, version `0.3.85-test.15`, code `86100`; успешный full CI https://github.com/manufact-test/nomusic/actions/runs/41674369584 ; подписанный ZIP/APK https://github.com/manufact-test/nomusic/actions/runs/41674369584/artifacts/13248949184 (учесть срок хранения GitHub Artifacts).
- **Оригинальная стабильная CELIKOM 0.3.85/code86, её package/signing/OTA Hostinger `stable.json`, stable publisher, резервы и PR #37 не затрагиваются**. Не обновлять стабильную версию, не сливать PR #37, не брать случайно Test.16 HEAD.
- Test.16 `0.3.85-test.16/code86101` functional SHA `66dfa4eb5b4ca05b0c26abb8e629131de1ac64e4`, поздний doc SHA `aa79a33808904fbadd161e5542c5103c6d707026` в старой рабочей ветке `feature/android-0385-intro-join-investigation-20261102`: **REJECTED, НЕ базировать новые изменения на ней и НЕ считать релизом**. Историю сохранить как диагностический пример, не выполнять разрушительное удаление чужих refs.

## 2. Итог акустического Test.15 и тяжёлый откат Test.16

Полевое мнение владельца: Test.15 — лучшая версия за серию испытаний: примерно 70% переходов практически незаметны, присоединение в ту же секунду вместо прежней полусекунды. На песнях с резкой атакой остаточный стык ещё слышен. После Test.16 владелец подтвердил резкую деградацию: много склеек через 2–3 секунды.

В общих run-сегментах приватного combined 2026-11-03:
- Test.15: 16/16 join, >1с 2/16, >2с 1/16.
- Test.16: 23/24 join, >1с 7/23, >2с 6/23.
- Сопоставимые треки (от первого наблюдения Yandex isPlaying=true до `replacement_transition_complete`):
  - «Крылья» SLIMUS/Ай-Q: Test.15 214мс, Test.16 2056мс.
  - «Дым» Лёша Свик: 215мс против 2210мс.
  - «Бошки Дымятся» Элджей: 467мс против 3387мс.
  - «Крылья (Другая версия)»: 266мс против 3239мс.
Разные порядок воспроизведения, кэш и сеть: эти цифры **доказывают регрессию пользовательского опыта, но не доказывают единственную причинность изменений Test.16**.

Test.16 меняла только bounded fast-join sampling `INITIAL_MS 35→15`, `STEP_MS 60→30` в прежних 1200мс и добавляла `AudioManager.AudioPlaybackCallback` только для анонимной read-only диагностики. Этот callback показал часто меняющиеся числа активных конфигураций 0–3; он **не знает**, какая из них Яндекс, что делает UI, и не предоставляет позицию. Этим способом не чинить паузу/seek. Test.16 не переносить в новую ветку.

Прямые причины некоторых поздних joins Test.16 по trace: скачивание файла ещё не завершилось при выборе трека. «Дым»: cold full_download ~1800мс, join после ~2210мс; «Бошки Дымятся»: cold download ~2486мс, join ~3387мс. «Крылья», «Нас не понимают вообще» и «Крылья (Другая версия)» ожидали уже запущенный speculative/in-flight full-file prefetch, который был не готов к началу песни. Нельзя лечить это очередным уменьшением polling timers. В Test.15 одно общее `NativeApi.audioWork` serial executor, speculative enqueue delayed 1100мс для foreground-current priority и 340мс grace для cached current prime; учитывать предыдущие неудачные параллельные audio queues.

Проверить архитектурно:
- Почему готовые/подготовленные замены снова скачиваются и теряются при быстрых сменах/перезапуске.
- `ProbeService.onStartCommand`: старые файлы `replacement-*.audio` и `buffered-*.audio` удаляются при старте. Аудировать назначение cleanup и возможность ограниченного долговременного validated LRU, а не просто убрать удаление: account scope, версии, приватность, максимальный объём, expiry, live file leases и безопасная очистка.
- Проверить очередь foreground-vs-lookahead, single-flight/promoted in-flight, отмену неактуальной prefetch, приоритет current download и длительный warm-cache reuse. Осторожно: при неизвестной внезапно выбранной песне невозможно гарантировать начало замены с нулевой задержкой, если полный файл требуется скачать; не обещать чудес.
- Защитить первый аккорд/звуковой стык с verified PCM/edition/alignment, но не вслепую менять fade/gain/clock и не ломать принятую перемотку.

## 3. Два трека с проблемной перемоткой / паузой

Трек A: **«Дым» — Лёша Свик**, Yandex trackId `39949113`, в Test.16 media alias `447`, albumId `5281614`, source duration 219660мс.

Видео: UI Yandex перематывается примерно 0:01→2:15→3:11→1:19→2:30; `MediaController.getCurrentPosition()` в CELIKOM всё это время продолжал отсчитывать лишь ~2–6с. Нет `SAME_ITEM_SEEK` и нет `replacement_sync(state=seek)`, пока не выбрана следующая песня. В предыдущем Test.15 видео также наблюдались UI 0→1:46→3:21→3:38→1:57 без исходного seek. Со слов владельца, пауза тоже не останавливает замену, но именно новое видео лучше доказывает seek, а не отдельное нажатие Pause. **Не объявлять seek/pause исправленными**.

Трек B: **«Нас не понимают вообще» — Космонавты, RASKOL**, Yandex trackId `42884423`, alias `430`, albumId `5685525`, duration 232330мс.
Видео: UI прыгает около 0:05→1:23→2:46, далее обратно около 1:42. В Media3 **нет `onPositionDiscontinuity(SAME_ITEM_SEEK)`**, но после задержки источник `getCurrentPosition()` всё-таки скачет: Test.16 t56411мс `sourcePositionMs=169454`, и t61029мс `sourcePositionMs=105337`. CELIKOM отправляет собственный `replacement_seek_request` и получает ACK в десятки миллисекунд после появления новых данных, т.е. accepted internal seek/ACK работает. UI явно меняется раньше доступной session state. Эти два сбоя похожи для пользователя, но **не идентичны по телеметрии**: A не сообщает скачка вообще, B сообщает запоздало. Не переписывать frozen `ReplacementEngine.seek()/completeSeek()` без доказанной собственной ошибки.

`ProbeService.tick` уже вызывает `sample(false)` каждые 250мс, а `onEvents` — дополнительный sample; чаще опрашивать не поможет, если upstream Media3 session отдаёт старую позицию. Legacy read-only `MediaBrowser` как альтернативный путь уже проверялся ранее и оказался `legacy_position_source_unavailable`. Не подавать его как новую идею.

## 4. НОВОЕ решение владельца: продукт без чувствительных разрешений

**Для массового CELIKOM НЕ добавлять** `AccessibilityService`, `NotificationListenerService`, `MEDIA_CONTENT_CONTROL`, `MediaProjection` и прочие специальные разрешения/опасные подсказки в production. Пользователь прямо указал на сложности установки, Google Play/Play Protect, недоверие клиентов и потерю масштабируемости. Разрешения в исключительном случае допустимы только как отдельно согласованный разовый исследовательский эксперимент на личном телефоне владельца; **никакая реализация релиза не должна зависеть от их выдачи**. Сохранять чистую установку APK.

Приоритетные **permission-free, read-only гипотезы**, пока НЕ подтверждены:
1. Сегодня мы создаём `androidx.media3.session.MediaController` из сервисного `SessionToken` Yandex `com.yandex.music.shared.media.session.session.Media3LibraryService`. Официальная документация Media3 объясняет, что `controller.getConnectedToken()` возвращает уже конкретный `TYPE_SESSION`; проверить **второй независимый контроллер с этим прямым токеном** и сравнить снимки состояния/seek/pause на проблемных треках с основным. Сама возможность подключения не гарантирует свежие данные, вторым контроллером **НЕ посылать transport commands**; строго отслеживать lifecycle и release.
2. Через стандартные `PackageManager.GET_SERVICES`/публично экспортированные `MediaSessionService`/`MediaLibraryService` того же Yandex package проверить, нет ли другого доступного публичного session endpoint с более свежими позициями. Для Android 11+ корректно учитывать manifest package visibility `<queries>`, но не добавлять чувствительных системных разрешений. Нельзя пытаться неэкспортированные компоненты, private API, root, hooks, обход защиты.
3. Проверить **свежий snapshot при разрешённом реконнекте** к той же официальной session и сравнить с давно живущим controller, чтобы отличить устаревший controller cache от устаревшего state на стороне Yandex. Не организовывать постоянный reconnect без доказательства и тестов; не оставлять параллельные бесполезные подключения в релизе.
4. Если все доступные публичные API честно отдают старое состояние, признать аппаратно/платформенное ограничение; сохранить безопасное поведение и не выдумывать позицию по анонимным audio counts, времени пальца или случайной активности.

Официальные Android references:
- https://developer.android.com/reference/androidx/media3/session/MediaController — `getConnectedToken()`, состояние remote controller.
- https://developer.android.com/reference/androidx/media3/session/MediaController.Builder — direct TYPE_SESSION vs service TYPE_LIBRARY_SERVICE.
- https://developer.android.com/reference/androidx/media3/session/MediaLibraryService и https://developer.android.com/reference/androidx/media3/session/MediaSessionService — публичные service interfaces.
- https://developer.android.com/reference/androidx/media3/common/Player.Listener — `onPositionDiscontinuity` только для опубликованных событий.
- https://support.google.com/android/answer/12623953 и https://support.google.com/googleplay/android-developer/answer/10964491 — причины не вводить чувствительные разрешения для массового APK.

## 5. Полевая диагностика и приёмка

Приватные файлы владельца (НЕ коммитить и НЕ добавлять в CI/artifacts):
- Test.15: `CELIKOM-combined-20261103-194654.txt`, `SVID_20261103_194429_1.mp4`.
- Test.16: `CELIKOM-combined-20261103-201203.txt`, `SVID_20261103_200939_1 (1).mp4` (~135.5с). Тестовый run Test.16 начинается в combined у строки ~3490, `run_start` at `2026-11-03T20:09:28+03:00`; предыдущие сегменты в том же файле — Test.14/Test.15. Если другому чату файлы не видны, владелец может приложить заново. Не публиковать слушательскую историю.
- Для оценки каждого нового изменения логировать отдельно `source first isPlaying`, cache hit/download/queue wait, lookahead inflight, decoder prepared, first audible replacement guard, seek originating from Media3 vs sampled discontinuity, source pause/resume, route changes и status native player. Сравнивать с Test.15 как акустически, так и по задержкам, отличать совпадения от доказанных причин.

## 6. Правила следующего разработчика

1. Вначале читать `docs/android/NEXT-CHAT.md`, этот handoff, Test.15 serial-audio doc, accepted frozen-seek docs, исходный код/host tests. Не начинать с Test.16 и не откатывать эталон.
2. Изучить логи и проверяемые источники Android без навязывания разрешений; прежде чем вносить изменения, обосновать, **какой именно наблюдаемый сигнал** должен исправиться; не объявлять гипотезу доказанной.
3. Тестирование: host regressions для stale Media3 controller, miss/delayed seek, pause/resume, cross-track identity, route change, invalid cache/eviction, serial queues и simultaneous lookahead; frozen accepted seek/ACK не ломать. Публичные инструменты не заменяют телефонную акустическую приёмку.
4. **Не гонять владельца по микросборкам.** Внести максимальный безопасный совместимый набор исправлений и только после CI выдать **ОДНУ** отдельную signed CELIKOM Test APK (новый versionCode, тот же пакет и signer) через реально работающий GitHub Actions artifact ZIP; учесть, что Library доставку ранее ломало. Дать точную ссылку и понятное, что проверять за один полный проход. Не выкладывать в stable OTA.
5. Критерии: Test.15 не деградирует по интро, «Дым» и «Нас не понимают вообще» явно проверены по pause + seek и сравнимым source/decoder часовым шкалам, обычные seek и переходы не ломаются, Play Protect/установка без новых специальных разрешений, потребность в fallback честно документирована.
6. При любом значимом ухудшении — откат **только экспериментальной ветки** к неизменной Test.15 backup; Test.16 не использовать для нового baseline. Обновить NEXT-CHAT после нового полевого теста и зафиксировать CI SHA/artifact/вердикт владельца.

**Никаких функциональных изменений или APK в этой передаче: только новая ветка на Test.15 и документы.**
