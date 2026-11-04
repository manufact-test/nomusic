# CELIKOM Android — Test.18 принят; акустический разбор и изолированный Test.19
Дата: 2026-11-04 (Europe/Moscow). Не переносить ничего из этого исследования в стабильное приложение без отдельного принятия владельцем.

## Неприкосновенные контрольные точки

- **Основное приложение:** CELIKOM Android `0.3.85/code86`, его release, подписанный APK, Hostinger OTA, stable.json, PR #37 и permissions не менять.
- **Лучшая принятая тестовая основа:** CELIKOM Test `0.3.85-test.18/code86103`; immutable backup `backup/android-0385-test18-best-owner-20261103` SHA `1a19ccec674d41b7417f29715d853eb693595687`; рабочий функциональный SHA `19ebf98344b02ec8a8088595ee8dca7740c0396c`. Signed artifact: https://github.com/manufact-test/nomusic/actions/runs/41704016656/artifacts/13265222571 .
- Прежний backup Test.15 `backup/android-0385-test15-best-owner-20261103` SHA `6fde1e48179ecb812f1def16067f18bf0d9c3003` не менять.
- **Разработка** — только `feature/android-0385-test15-permissionless-recovery-20261103`; без второго MediaController/наблюдателя, без Accessibility, NotificationListener, root, новых разрешений, параллельных аудио-владельцев и сетевых «обходов».
- Владелец Test.18 называет уже заметно лучшей на многих треках, но слышит короткий пропуск первой мгновенной ноты на некоторых. Важны сохранение хорошей перемотки, pause/resume и отсутствие наложения двух источников. Не выдавать host CI за проверку телефоном.

## Новое прочтение того же приватного прогона

Только Test.18-сегмент `run_start` 23:25:47+03 из приватного `CELIKOM-combined-20261103-232845.txt` и видео `SVID_20261103_232559_1.mp4`; сырьё и приватные списки в репозиторий не загружать.

1. Сопоставлены запись экранного звука и `replacement_transition_complete` (видео примерно соответствует `log elapsed seconds - 13.25`). Среди 24 первых joins **13** имеют начало очень тихого участка в ~150 мс от стыка, **17** имеют наложение участка тишины на ±180 мс вокруг стыка. Это статистика корреляции, **не доказательство причины**: AudioPlaybackCapture может прерываться при смене приложения-владельца звука.
2. Пример «Биг сити лайф»: транспортное обнаружение→join 348 мс, `replacement_join_guard_verified` source 343 мс vs decoder 266 мс (drift 77 мс, в пределах порога 100 мс), затем `exclusive_single_turn` с ramp 0 мс. На записи около join — короткий участок 206 мс ниже -54 dB, включая ~60–80 мс буквальных цифровых нулей. Нельзя трактовать транспортное совпадение как совпадение фаз PCM; запись экрана — не физический микрофон.
3. Собственный `MediaPlayer.getTimestamp()` **уже интегрирован** через `OutputClockEvidence.java`; добавлять второй такой же механизм бессмысленно. Даже хороший timestamp собственного декодера не показывает фазу/PCM исходного Яндекса или акустический задержанный путь Bluetooth.
4. На фоне этого есть паузы, когда CELIKOM вообще не заменяет музыку (например, после `cannot_mute_original`): ошибка источника или захвата возможна независимо от CELIKOM. Нельзя вслепую менять порядок `source mute → replacement unmute` на одновременные слышимые выходы или возвращать 160 ms crossfade без фазового доказательства.
5. В Test.18 найден конкретный **системный дефект живучести**: на одной песне `mute()` при любом `RuntimeException` вызывает `stop("cannot_mute_original")`, навсегда выключая автозамену на **всех следующих песнях** текущего запуска. Фактически так и случилось до «Дым»: её плавная перемотка принадлежала оригиналу Яндекса. В журнале нет этапа отказа эффекта (`session / DSP create / hasControl / prepare`). Это реальная точка для узкого обратимого исправления, не требующая наблюдателя.
6. RASKOL: внешний UI Яндекса менял координату, Media3 snapshot остался старым, callback seek не пришёл. Internal seek/ACK замены уже работает при приходе новых координат: frozen path не менять. Johnyboy «Метамир» 1634 мс из-за ещё не завершённого файла prefetch: это другой класс задержек. Для каждого случая нужен отдельный системный класс, **не** patch по trackId.

## Состав единого следующего эксперимента Test.19

- **Сохранение одного владельца.** `AudioOwnership` остаётся единственным авторитетом звука, только текущая Media3-сессия, не создаём второго listener/controller, не даём original и replacement одновременно ненулевые слышимые gains вне legacy SAME_SONG_BLEND.
- **Stage-aware fail-closed DSP recovery.** Из `mute()` логировать точный этап отказа без private exception message/stack. При preflight-ошибке недостоверной сессии сохранять ручное восстановление. При transient `DynamicsProcessing` creation/control/enable failure — строго выключить вторичный decoder и вернуть оригинал, **пропустить только текущий трек** и оставить подтверждённое ручное включение автозамены для следующего трека. Никакого бесконечного retry-loop посреди одной песни, никаких «двух звуков».
- **Измеримые этапы:** сохранить output-clock pre/post и дополнить лог аудио-команд одного exclusive grant; они подтверждают командный порядок, не гарантируют физическую акустическую бесшовность.
- **Регрессии:** synthetic host fallback при DSP отказе, next-track recovery, отсутствие слышимого наложения, single-owner, frozen HONOR local seek/ACK golden hashes, pause/resume, подписанный side-by-side Test APK. Отдельный apk `0.3.85-test.19/code86104`, тот же `pro.celikom.nativeprobe.test`, **обновляет только CELIKOM Test**, не стабильное приложение.
- Если Test.19 на телефоне хуже Test.18, вернуться к уже подписанной Test.18 и backup-ветке без откатов stable. После одного успешного CI Test.19 — **не объявлять** first-note или RASKOL исправленными до фактического прогона.

## Текущие критерии будущей проверки владельцем

Сначала убедиться `replacementArmed=true` и реально произошёл `replacement_transition_complete` именно для проверяемой песни; иначе «Дым работает» относится только к Яндексу. На живой замене проверить «Дым» отдельно пальцем и кнопкой Pause→Play, RASKOL с наблюдением source position, жёсткие первые ноты, по меньшей мере три перехода после имитированной невозможности DSP mute. При ухудшении — Test.18 сохранена как эталон.

## Test.19 — реальный результат изолированной CI-сборки (2026-11-04)

- **Функциональный SHA:** `39c4abf5c369772adc9f8864fe546b8df7c75642`; только рабочая экспериментальная ветка. Test.18 backup и stable не изменялись.
- **Полный CI SUCCESS:** https://github.com/manufact-test/nomusic/actions/runs/41719786549 . Host regression `TestSourceEffectRecovery`: **PASS 33 проверок**, в том числе transient `create / control / enable` failure, source-only после отказа, отсутствие повторов на той же песне, auto-resolve и новый DSP на следующей; обязательный frozen HONOR seek/ACK, архитектурные проверки, Android API36, D8, подпись и упаковка прошли.
- **Подписанный side-by-side APK ZIP:** https://github.com/manufact-test/nomusic/actions/runs/41719786549/artifacts/13270969005 ; имя архива `CELIKOM-Test-0.3.85-test.19-code-86104.zip`, внутри `CELIKOM-Android-0.3.85-TEST-19-RECOVERABLE-EFFECT-SIGNED.apk`, `verification.json`, `RECEIPT.json`.
- **Проверенный APK SHA256:** `5d6fed766ec1b5a35515e0f01ffb8a1f8ce0636e7203bcc15a1d73f1e2b78b5b`; совпадает с исходным сертификатом, Android v3 подпись валидна. Пакет `pro.celikom.nativeprobe.test`, ярлык CELIKOM Test, нет OTA и новых разрешений.
- **Принятие владельцем ещё НЕ получено.** Test.19 намеренно не обещает устранить 200ms acoustic capture gap, Johnyboy cold download или невидимый RASKOL seek; внедрено recoverable DSP с диагностикой failure stage. В случае ухудшения — откат к сохранённому signed Test.18; публиковать новую stable нельзя.
