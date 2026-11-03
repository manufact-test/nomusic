# CELIKOM Android — Test.18 single-lane foreground download preemption
Дата: 2026-11-03. Статус: **экспериментальная сборка, акустическая приёмка владельца не выполнена**.

## Неприкосновенная основа

Test.15 (`0.3.85-test.15/code86100`), backup `backup/android-0385-test15-best-owner-20261103` SHA `6fde1e48179ecb812f1def16067f18bf0d9c3003`. Test.16 и Test.17 отвергнуты. Этот эксперимент **не переносит** их код. Frozen seek/ACK, pauseSource, handover audio ownership, output gain, stable `0.3.85/code86`, Hostinger OTA, `stable.json`, PR #37 и разрешения Android не менялись.

## Проверяемая узкая проблема

В Test.15 все полнофайловые загрузки, включая lookahead, выполняет один `NativeApi.audioWork` worker. Задержка speculative enqueue на 1100 мс оставляет foreground возможность встать первым, **но не может отменить уже начавшуюся speculative скачку** в случае ручного переключения на другой, совсем новый трек. При этом `AudioTransfer.copy` умеет отменяться через `BooleanSupplier valid` и быстро закрывает HTTP соединение собственным watchdog; значит, не требуется второй конкурирующий сетевой канал или изменение seek.

## Изменения Test.18

- `AudioWorkPriority` считает **очередные foreground-задачи** (текущий трек) через thread-safe `AtomicInteger`.
- При появлении foreground download активный speculative `downloadLookahead` получает `valid=false`, его `AudioTransfer.copy` завершает передачу без повторов; **освободившийся тот же единственный audio worker** начинает текущую песню. Частичные файлы удаляются существующим fail-safe path.
- После завершения foreground callback lookahead снова разрешён, только если его старый identity/account/source lease остаётся действительным.
- Если lookahead был **промотирован в текущую песню**, прежний `ReplacementEngine.waitForLookaheadPrefetch` сохраняет single-flight (повторную foreground загрузку он не ставит), поэтому новый приоритет не должен отменять собственную подготавливаемую песню.
- Оставлены без изменений 1100мс delayed speculative enqueue, 340мс cached decoder prime grace, единая очередь, полный файл, accepted frozen seek/ACK и default gain. Никакого дополнительного разрешения.
- Добавлен отдельный Android host regression `TestAudioWorkPriority`, проверяющий отмену speculative и работу очередного foreground на **одной** executor lane; полный набор прежних Android/audio regression tests обязателен.

## Границы ожидаемого эффекта

**Это не исправление всех слышимых стыков и не обещание идеальной первой песни.** Оптимизация влияет только на случай, когда уже идёт (или стоит в очереди) speculative загрузка *другого* трека, и появляется новая текущая. Первый полностью холодный трек всё равно должен скачать файл (в свежем Test.17 на HONOR это было ~2423 мс). Треки «Дым» id39949113 и «Нас не понимают вообще» id42884423 могут не отдавать seek/pause в публичный Media3: никакой доказанной permission-free альтернативы не появилось. Test.17 direct-session experiment завершился `ExecutionException`, его код удалён.


## Проверенная поставка

- Финальный functional SHA `19ebf98344b02ec8a8088595ee8dca7740c0396c` (первый код-коммит `0f14f52a6a3e5c02714188627ebacf8ba1029627`; второй коммит исправил только имя APK в GitHub Actions и добавил отдельную проверку соответствия version spec).
- Полный [GitHub Actions #41704016656](https://github.com/manufact-test/nomusic/actions/runs/41704016656) — **SUCCESS**: native host regressions, Android 36/D8, golden seek freeze, isolated signed Test APK build, provenance, signer and package verification. Stable publish и все stable deployment jobs — **SKIPPED**.
- [ZIP с одним проверенным Test.18 APK и receipt](https://github.com/manufact-test/nomusic/actions/runs/41704016656/artifacts/13265222571) (artifact 13265222571; до 2026-11-10).
- Внутри ZIP `CELIKOM-Android-0.3.85-TEST-18-FOREGROUND-PRIORITY-SIGNED.apk`. APK SHA-256 `e0f4852ada7a6e4f2e9e499176149b7488d8861b6833e714804826663b826a8e`; package `pro.celikom.nativeprobe.test`, version `0.3.85-test.18/code86103`. V3 signer validated, signer SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` равен эталонному. Из-за 86103 Test.18 можно обновить поверх Test.17 без downgrade/uninstall.
- Предыдущий CI `#41703349929` был SUCCESS и подписал правильную Test.18, но вложенный APK ошибочно назывался `TEST-15`. **Не распространять этот первый ZIP**, для владельца предназначен только исправленный финальный `#41704016656`.
- До первого HONOR прогона улучшение переходов — инженерная гипотеза, акустически не подтверждена. Тестировать всю сборку одним проходом, не утверждать что проблемные seek/pause исправлены.

## Проверка и критерий приёмки

- Host CI должен подтвердить все старые regressions, golden seek freeze, Android API36/D8, изолированный Test APK, проверку signer и stable publisher SKIPPED.
- Сравнить Test.18 с Test.15 на HONOR одним общим прогоном с быстрыми переходами на совершенно новые песни, паузой, перемоткой, Bluetooth и прежними проблемными песнями. Не трактовать не подтверждённую источником позицию как исправленный seek.
- Если слышимый стык, пауза или seek ухудшатся, откатить **только экспериментальную ветку** к неизменной Test.15. Стабильную версию не трогать.
