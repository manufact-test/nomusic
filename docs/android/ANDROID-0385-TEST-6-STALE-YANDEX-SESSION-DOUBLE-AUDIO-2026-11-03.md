# CELIKOM Test.6 — новая аудиосессия Яндекс Музыки, двойной звук (HONOR / Android 13), 2026-11-03

## Вывод

**Новый реальный функциональный баг, не новая APK.** Владелец после длительного перерыва наблюдал, что ряд замен не подключается, а при подключении одновременно слышны оригинал Яндекс Музыки и замена CELIKOM. Нажатия «Отмена» → «Старт» владельцем восстановили нормальное поведение. **Автоматическое продолжение/подмена между треками необходимо сохранить** — это принятая функциональность, возврат к ручному входу в эквалайзер на каждую песню недопустим.

Тестируемая версия неизменна: `0.3.85-test.6`, code86091, package `pro.celikom.nativeprobe.test`, functional SHA `3c22a03f364a019ac545efb4e132ad3f5fc12c21`. Никакой Test.7 пока нет.

## Диагностика

Новый combined `CELIKOM-combined-20261103-110350.txt`, 3592 строк. Содержит три накопленных запуска: Test.2 (737 JSON events), Test.4 (1039), **Test.6 (1813, start 2026-11-03 00:08:51+03)**. Test.6 `elapsed_ms` до 39,298,560 (~10ч55м), с большими естественными пропусками журнала между ночным и новым прослушиванием. Не путать с отдельными запусками. Сырые файлы и названия музыки не коммитить.

### Подтверждённый механизм двойного звука

| Test.6 elapsed | Факт |
| --- | --- |
| 18–111 с и 3992.81 с | `audio_session_broadcast` Яндекс `OPEN_AUDIO_EFFECT_CONTROL_SESSION`, sessionId **74313** |
| 39220.747 с | Яндекс прислал новый `OPEN_AUDIO_EFFECT_CONTROL_SESSION`, sessionId **75561**; повтор при 39243.207, 39254.039, 39263.105 с |
| 39220–39296 с | `service_heartbeat` CELIKOM по-прежнему держит **trustedSessionId 74313** |
| 39288.189 с | `replacement_original_muted` с **sessionId 74313**, несмотря на новую объявленную Яндексом **75561** |
| 39288.516 с | `audio_owner_state` = `REPLACEMENT`, `sourceMutedCommand=true`, replacementVolume=1; CMD не измеряет реальную акустику |
| 39296.267 с | CELIKOM считает `REPLACEMENT`, эффект `hasControl=true/enabled=true` на **старой** сессии, новый исходный звук может оставаться слышимым |

**Важная ловушка:** `effectSessionId` в `ProbeService.runtimeSnapshot()` получен через `e.effect.getId()` — это **ID эффекта**, а не audioSessionId; сравнивать его с 74313/75561 нельзя. Настоящий ID эффекта привязан к 74313 в `new DynamicsProcessing(0,trustedSession,null)` внутри `ReplacementEngine.mute()`.

Причина, почему защита отсутствует на устройстве: `ProbeService.audio` распознаёт пакет Яндекс Музыки, но вызывает `replacement.stop("yandex_audio_session_changed")` **только если** `verifiedSessionSender(this)` возвращает true. `verifiedSessionSender()` сразу возвращает false для **Android API<34** из-за недоступности `BroadcastReceiver.getSentFromUid()`. У владельца HONOR Android **API33**; все журнальные `trustedForAttach:false`. В итоге mismatch сессий наблюдался, но не приводил даже к защитной остановке. Проверка effect.hasControl() не помогает: старый эффект жив и имеет контроль, только обрабатывает не ту сессию.

### Отдельный симптом: замена долго не подключалась

Для source alias8 наблюдение Yandex metadata в **39263.086 с**, каталог своей копии был `STALE_OR_INCOMPLETE_SNAPSHOT`, `method NONE`. Новый `album_request` по albumId был лишь **39286.367 с** (разница ~23.3с), `album_response` HTTP200 / unique match в 39286.433 с, current resolve в 39286.524 с, prepared 39288.174, join 39288.519. Это подтверждает отдельное ожидание identity/album network, но причина именно 23-секундной задержки запросов требует проверки budget/pending/foreground. Не списывать её полностью на audioSession. Не подменять без уникального кандидата.

Повторяющиеся `replacement_lookahead_prefetch_promoted_inflight` с phase `cached` после готовности файла — отдельное состояние prefetch, **нет свидетельства второго декодера**, не считать причиной двойного звука без доказательств.

## Требования к исправлению

1. **Остаться автоматически включённым между песнями**, как сейчас. Нельзя возвращать обязательный ручной вход в эквалайзер при каждом track boundary.
2. На Android13 обнаруживать и **fail-closed** обрабатывать вероятную смену Yandex source-session: при наблюдении нового session ID того же заявленного Yandex package останавливать/глушить replacement, возвращать оригинал и показывать явное объяснение. **Не привязывать** эффект к новому ID автоматически по непроверенному broadcast — package/session extras на Android13 не удостоверяют UID, иначе другое приложение сможет заставить CELIKOM вмешаться в чужую сессию. Возможный DoS от поддельного broadcast при fail-closed требует явного risk review; по возможности подтверждать дополнительным независимым сигналом перед stop, но никогда не продолжать играть replacement на заведомо stale session.
3. На Android>=34 использовать доступный verified UID для trusted transition detection. Следующий механизм бесшовного re-attach должен получить свежий **проверенный** session ID через подписанный Yandex effect panel/достоверный источник, не угадывать его из untrusted broadcast.
4. Добавить host regressions на API33 mismatch OPEN и CLOSE, совпадающие ID, чужой пакет, неактивную подмену и запрет auto-trust; проверить автономную сессию после длительного background/reopen и после Next.
5. Совместно устранить отдельный identity/album delay только с доказанной причиной. Главный приоритет — звук вступлений, но двойной звук является критическим safety/regression bug.
6. Любой реальный фикс — только experimental branch, new Test APK code>86091, original signing cert, OTA OFF, полный host suite, неизменённый accepted seek guard, API36/D8, GitHub Actions, SHA/verification/receipt/Library. Stable0.3.85/code86, backup branches, `stable.json`, Hostinger, PR#37 не трогать.
7. **В текущем чате исправление пока НЕ внедрено и НЕ собрано.** Сохранили диагностику и причину; Test.6 остаётся последней проверенной APK, но теперь известно её ограничение после Yandex audio-session restart. Владелец подтвердил, что Cancel→Start временно восстанавливает звук.

## Контрольные точки

- Branch `feature/android-0385-intro-join-investigation-20261102`.
- Latest owner-retreat docs `docs/android/ANDROID-0385-TEST-6-OWNER-RETEST-RESULT-2026-11-03.md`; Test.6 functional SHA `3c22a03f364a019ac545efb4e132ad3f5fc12c21`.
- Stable original `0.3.85`/code86 `pro.celikom.nativeprobe` SHA `053b7d59beb53db5f30b942feba35e51a1ab256a`; accepted backup branches untouched.
