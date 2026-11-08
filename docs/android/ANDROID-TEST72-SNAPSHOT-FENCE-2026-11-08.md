# CELIKOM Android — Test.72 (HONOR stale Media3 snapshot fence)
**Дата:** 2026-11-08. **Статус:** отдельная подписанная APK, CI PASS, **ожидает телефонной проверки**, НЕ заявлять исправление всех проблем управления.
 
## Происхождение и границы
- Ветка: `feature/android-0385-test72-source-snapshot-consistency-20261108`, создана **напрямую** от Test.70 `feature/android-0385-test70-safe-rollback-source-buffer-status-20261108` (НЕ от Test.71).
- Исходник подписанной APK: `ed9ade1a4ed695ae94ecda6bb760515b1894d959`.
- Test.71 `NativeTransportWitness`, дополнительный legacy MediaBrowser retry, защитное выключение на спорных паузах **не переносились**. Исходный звук и функции управления от Test.70.
- APK: `CELIKOM-Android-0.3.85-TEST-72-SOURCE-SNAPSHOT-SIGNED.apk`, package `pro.celikom.nativeprobe.test`, version `0.3.85-test.72`, code `86158`, размер 8,870,041 байт; SHA256 `279230811ce22d781267b65dee7aee7899fa6ae6b95b530d1dbabdfe391b3ec6`. Сертификат SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`, v3 verified, original certificate matched.
- APK в ChatGPT Library: [Test.72](https://chatgpt.com/library?file_id=libfile_0cb46b47275481918d4b268be75cb0eb&account_id=personal). Рядом доступны `verification.json` и `RECEIPT.json`.

## Воспроизведённая регрессия Test.71
Диагностика `CELIKOM-combined-20261108-211554.txt` + `SVID_20261108_211432_1.mp4`, анализ: [ANDROID-TEST71-HONOR-211554-FAIL-2026-11-08.md](../android/ANDROID-TEST71-HONOR-211554-FAIL-2026-11-08.md) в ветке Test.71.

При переходе RASKOL→«Дым» Test.71 Яндекс оставался в BUFFERING и не прислал READY; альтернативный источник состояния отсутствовал. После перехода на «Розовое вино» и Back экран Яндекса показывал «Дым», но внешний Media3 с тем же alias `978` передал прежние название/исполнителя «Розового вина» и **длительность `219660 ms` от «Дыма» вместо `246810 ms`**. Это вызывало ошибочный `source_track_transition` (previousAlias=nextAlias=978), замена сбрасывалась, `no_unique_candidate` ошибочно трактовалось как отсутствие версии. Данных, что библиотека потеряла замену «Дыма», **нет**.

## Реализация Test.72
- `SourceSnapshotConsistency.java`: детерминированный контроллер целостности идентичности без таймеров и внешних вызовов. Сравнивает текущие alias, title, artist, cover, duration с ранее согласованным снимком того же трека и, если доступно и правдоподобно, `com.yandex.music.media.metadata.duration` из MediaMetadata extras. Значимое расхождение >4000 ms — **целостность данных, а не коррекция аудиотайминга**.
- `ProbeService.sample()`: проверка выполняется **до** `PlaybackSource`, `AlbumProbe.observe` и `ReplacementEngine.update(current)`. При первом противоречии `source_snapshot_mixed_identity` — один `replacement.suspend`, немедленный возврат оригинала и блокировка дальнейшего использования противоречивой идентичности. Не обманывать UI `нет замены` ошибочными метаданными. Старый alias с новой длительностью остаётся заблокированным до нового согласованного media item; для ранее не подтверждённого нового alias разрешается восстановление при согласовании данных. Действия в Яндекс НЕ отправляются.
- При согласовании лог `source_snapshot_consistency_restored`. При отсутствии конфликтов поведение Test.70 не меняется.
- Сброс проверки выполняется при **новом** Media3 controller; старый controller не переподключается насильно и не уничтожается из-за BUFFERING.

## Регрессия и CI
- `Test72SourceSnapshotConsistency.java`: полный Dym 929/219660 → RoseWine 978/246810 → Back (978 + 219660) → stale old alias → новому coherent Dym разрешено возобновление. Дополнительно контрольные 10AGE, без метаданных, кратковременные согласующиеся изменения длительности, новый alias с временным несовпадением, отсутствие повторной авторизации старой песни.
- Полный host suite, архитектурные проверки, frozen owner-approved seek baseline, Android API36 javac/D8 и тестовый sign/receipt контракт: **SUCCESS** [GitHub run 42511253216](https://github.com/manufact-test/nomusic/actions/runs/42511253216).
- Сборка только side-by-side, stable Android 0.3.92, OTA и прод не публиковались; pinned base APK и актуальный каталог читались с Hostinger без записи.

## Критически важные ограничения
Этот patch закрывает **обнаруженное загрязнение полей идентичности**. Он не исправляет зависание внутреннего плеера Яндекса в BUFFERING и не предоставляет PCM-часы чужого декодера. Поэтому нельзя обещать, что RASKOL↔«Дым» и нативная пауза станут мгновенными. Телефонного результата на HONOR пока нет.

## Следующая проверка
Установить Test.72 поверх Test.71 (code выше, подпись та же) без принудительной установки Test.70. Проверить в официальной Яндекс Музыке: RASKOL → «Дым»; далее Next → Back; пауза, перемотка, возврат на обычную песню, отдельно обычные контрольные треки. Передать combined diagnostic и видео. Смотреть `source_snapshot_mixed_identity`, `source_snapshot_consistency_restored`, `source_track_transition` (особенно same alias), `no_unique_candidate`, source buffering/ready. Не считать CI подтверждением звука. Если проблема осталась, исправлять по новой диагностике, не перекладывать откат на пользователя.
