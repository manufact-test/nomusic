# CELIKOM Android 0.3.60 / code61 — root-cause checkpoint · 31.10.2026

**Релиз опубликован автоматически, но по звуку на HONOR ещё НЕ ПРИНЯТ.** Это инженерная контрольная точка, не заявление об акустическом исправлении. Только Android ветка `feature/android-unified-preparation-seek-gate`; desktop, `feature/api-range`, каталог, backend, реклама и Hostinger-настройки не менялись.

## Основания: реальный журнал 0.3.59

Источник: [AUDIO-0359-HONOR-DIAGNOSTIC-2026-10-30.md](AUDIO-0359-HONOR-DIAGNOSTIC-2026-10-30.md), третий `run_start` `0.3.59` личного файла `CELIKOM-combined-20261030-234700.txt` (не копировать сырые логи в GitHub). HONOR NTH-NX9, Android 13. Автор категорически отклонил 0.3.59: старые seek/next лаги и новая pause/resume регрессия.

- 25 `commanded_silence` после seek (43–556 мс), но `sourceMutedCommand=false`; это **не** запись реальной тишины.
- 49 `replacement_seek_complete`, в том числе 548/551 мс. На hardware это может продолжаться; новый код **не уменьшает длительность системного MediaPlayer.seekTo**.
- Пример pause 20942/20949 → resume 21870 → re-seek 21875 при drift 126мс → fade100мс → handover/ramp ~145мс → 22161: окно 291мс после resume. Не приписывать ему акустическую тишину без записи.

## Воспроизведённая причина и изменение кода

1. **Провал энергии во время handover (фактический дефект алгоритма):** `ReplacementEngine.fade()` в 0.3.59 плавно снижал усиление исходного аудиосеанса до примерно –100dB за 100мс, пока replacement gain оставался 0. Поздний 32мс/145мс подъём замены не мог заполнить этот участок. Теперь оригинал с исходным gain продолжает играть во время подготовки, seek и ожидания clock; `AudioOwnership.grantReplacement` и `applyVolume(1f)` выполняются последовательно в **одном** main-handler turn после проверки clock/ticket/identity. Никакого 100мс source fade и последующего 32мс ramp. Двойная ненулевая громкость запрещена; физический DSP/device output этим не измеряется.
2. **Ложная длина `commanded_silence`:** `seek()` восстанавливал source gain, но не вызывал `traceAudioCommands()`. Следующее наблюдение через 551мс записывало фантомный интервал. Добавлен command sampling сразу после восстановления оригинала.
3. **Security после удаления старого fade timer:** отменённый fade callback больше не мог автоматически увидеть смену аккаунта до следующего Media3 update. `NativeApi` теперь уведомляет Android audio owner о каждом login/verify/logout через main handler, чтобы старый lease немедленно отзывался.
4. **Не исправлено/не доказано:** на паузе drift 126мс всё ещё может превышать `PAUSE_ALIGN_TOLERANCE_MS=85` и запускать decoder re-seek; незнакомое физическое звучание instant switch на HONOR/Bluetooth; повторный seek до 551мс; качество next-track timing. Не повышать допуски и не добавлять prefetch/таймеры без красного теста по новой физической жалобе.

## Воспроизводящие тесты и доказательства

- `android/native-companion/tests/TestHonor059Journal.java`: red-before / green-after для pause/resume, удержания одного слышимого владельца до decoder-clock и telemetry seek. Подключён к `tests/run_engine.py`.
- Актуализированы устаревшие ожидания fade в `TestEngine.java`, `TestHandoverClock.java`, `TestStreamingEngine.java`, `TestUnifiedAudioTransactions.java`; сохранены stale seek/track/account fences.
- `tests/check_audio_architecture.py` теперь отвергает повторное включение `fadeSourceBeforeGrant`, `rampDuration=32`, positive gain до owner grant, отсутствие немедленного source trace и account-change callback.
- Android tests + Java API36 + D8 + provenance + подписанная упаковка: [GitHub Actions run 41131756964](https://github.com/manufact-test/nomusic/actions/runs/41131756964), **SUCCESS обоих jobs**. Предыдущий полный regression run code60: [41131428988](https://github.com/manufact-test/nomusic/actions/runs/41131428988), SUCCESS.
- Код кандидата `0.3.60/code61`: `4c9e730047fb73eeeb8fe06807feefea27cf433d`; изменены только Android native companion и тесты (и затем этот документ).
- Оригинальная точка восстановления до правок: branch `backup/android-0359-rootcause-red-20261031` на `17d26686836a3bbc82b87851779f4cb308c762cb`. Не удалять.
- Published manifest: `versionName=0.3.60`, `versionCode=61`, `apkSha256=0676a58eacdbe890318517b6b0a754eaad333cf64d7ddbfdea447b01ccef015f`, size `8722505`, signer SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. Публичный `stable.json` прочитан после release, versioned APK проверен HEAD 200 / `application/vnd.android.package-archive` / correct Content-Length.
- Постоянная страница: https://lemonchiffon-narwhal-791953.hostingersite.com/download/android/ . Встроенное обновление должно показать 0.3.60 с 0.3.59. Не перенастраивать CI, signer, Hostinger.

## Следующая проверка

Владелец устанавливает **одну** 0.3.60 и слушает на том же HONOR: (a) ручная перемотка, (b) короткая и длинная пауза, (c) 2–3 последовательных перехода. Просим субъективную оценку и один экспорт диагностики после этих действий. При новом баге разделить `run_start.version=0.3.60`, локализовать timeline и добавить красный replay **до** следующего release. Зелёный CI не эквивалентен принятию аудио.
