# CELIKOM Android — Test.50 seek-timeout fail-open: проверка всех четырёх путей (10.11.2026)

**Статус: CI GREEN, только экспериментальный исходник, не APK и не доказательство звучания на HONOR.**

## Точная контрольная точка

- Рабочая ветка: `experiment/android-test50-repeated-seek-failopen-20261110`.
- Последний проверенный **кодовый** SHA: `ca22fc91fc2658a2f3aed597cd128caf1b9c285f`.
- Точный откат: `backup/android-test50-seek-timeout-four-paths-ci-green-20261110` → этот же SHA.
- До изменений зафиксирован отдельный откат: `backup/android-test50-pre-seek-failopen-audit-20261110` → `7552a8255b654037849c4772609c0d67cca8e9ed`.
- **Полный Android CI [#42847799573 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42847799573)**. Никакого release, OTA, подписанного Test APK, выдачи пользователю или установки.
- Принятая владельцем Test.50 `backup/android-test50-exact-source-owner-accepted-20261106` @ `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1` сохранена. Windows и production не менялись.

## Что исправлено на базе предыдущего fail-open

1. **Нельзя сбросить защёлку посторонним тайм-аутом.** Старый `SeekTimeoutCircuitBreaker.timeout(null/empty/invalid)` вызывал `reset()` и снимал original-only с A, если после двух ошибок A пришёл поздний callback уже при неизвестном источнике. Теперь такие вызовы не меняют состояние. Если защёлкнута A, тайм-аут B не разблокирует A и не учитывается как ошибка B. Сброс защёлки допускается только штатным `boundary()` при подтверждённой границе или Stop.
2. **Поздний и WARM ACK не стирают историю ошибок.** В `AudioOwnership` добавлено чтение `seekFlightCurrentOperation`; обёртка `ReplacementEngine.onDecoderSeekComplete` очищает серию только для действительно активного `ALIGNMENT` seek того же текущего operation epoch, завершившегося aligned без нового in-flight seek. Пауза увеличивает epoch и отменяет право ACK обнулять счётчик. У Android `MediaPlayer` сам callback НЕ несёт sequence ID — никакого доказательства декодера Яндекса из этого не следует.
3. **Учтён четвёртый путь зависания.** Ранее были покрыты три `suspend("seek_timeout",retryDelay())` — два из `update` и отложенный сторож `seek`. Но `startHotCachedSeek` имел отдельный `suspend("hot_cached_seek_timeout",retryDelay())`, который не увеличивал счётчик. Теперь оба вида native seek timeout проходят один и тот же двухошибочный fail-open.
4. **Диагностика стала пригоднее для поля.** Событие `replacement_seek_timeout_failopen` включает `reason`, `trackId`, `sourceItemGeneration`, `replacementGeneration`, `timeoutCount`, `originalUntilBoundary`, `sameCurrentSource`. Это наблюдения о CELIKOM, не измерение PCM и не подтверждение команды паузы в самом Яндексе.

## Подтверждённые проверки

- `TestSeekTimeoutCircuitBreaker`: **106 025** модельных assertions, включая поздние null/empty/foreign/invalid-clock после latch.
- `TestRepeatedSeekTimeoutRecovery`: **36** проверок реального `ReplacementEngine` с fake Android MediaPlayer для обычного и hot-cached timeout, оригинального аудио, Next, backward seek, неверного источника и старого pause-epoch ACK.
- Полный Android native host regression (`21` addon host suites), Java Android API36 compile, D8, release-contract/provenance negative cases и packaging validation — SUCCESS.
- Golden source/seek/ACK baseline Test.50 **не менялся**, прежняя регрессия `check_0385_seek_baseline.py` — PASS. `seek()` и `completeSeek()` не редактировались.
- Все проверки — CI/model/fake; **«Дым», «Раскол», пауза/Seek и выбранный Yandex Lemb на настоящем HONOR НЕ проверены**.

## Оставшаяся задача и граница релиза

Не повторять тупиковые DEX/x86/ARM-эмулятор циклы. При отдельном разрешении на тестовую сборку сделать **изолированную подписанную Test-кандидатку**, НЕ изменяя эталон Test.50 и stable. На HONOR проверить «Раскол» `42884423`, «Дым» `39949113`: обычная пауза, Seek вперёд/назад, два неподтверждённых seek за 60 с, возврат оригинала без бесконечного переподключения, повторный rewind не снимает защиту, Next сбрасывает её, радио и обычные песни остаются без регрессии. Анализировать события `replacement_seek_timeout_failopen` вместе с trace до подтверждения результата. 

**Эта защита прекращает только повторные попытки нашего вторичного декодера; она не чинит зависший транспорт Яндекса и не даёт native source-first FileInfo hook.** Физический Android звук, Play/Pause/Seek в Яндексе и отсутствующий доступ к его выбранному `Lemb` пока остаются нерешёнными. Без акустического подтверждения Test.51 не продвигать в основную.

Строго не трогать: owner-accepted Test.50, основной HONOR/установленный Яндекс, Windows 0.24.x, расширение, API, production, БД, подписи/DRM/Play Protect.
