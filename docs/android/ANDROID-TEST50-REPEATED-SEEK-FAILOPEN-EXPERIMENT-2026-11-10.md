# CELIKOM Android — отдельный эксперимент Test.50: повторные seek timeout → оригинал до Next

**10 ноября 2026.** Это **не** выпуск APK и **не** изменение принятой Test.50.

## Контрольная точка

- **Эксперимент:** `experiment/android-test50-repeated-seek-failopen-20261110`.
- **Проверенный исходник:** `7440d70be0e0584fde12bff2c1fc43725717475e`.
- **Точный бэкап эксперимента:** `backup/android-test50-repeated-seek-failopen-ci-green-20261110` → тот же SHA.
- **Неприкосновенная Test.50:** `backup/android-test50-exact-source-owner-accepted-20261106` → `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`.
- [**Полный Android CI 42843272827 — SUCCESS**](https://github.com/manufact-test/nomusic/actions/runs/42843272827). `native-android` SUCCESS; jobs подписания Test APK / stable / OTA **SKIPPED**, никаких production публикаций.
- Параллельная source-first лаборатория **не сливалась**: `experiment/android-native-yandex-fileinfo-hooklab-20261109`, её Android 13 OWN-only runtime проверки были успешны, но live источник Яндекса по-прежнему не установлен.

## Зачем это сделано

Владельцу Test.50 показалась лучшей на настоящем HONOR, однако «Дым»/«Раскол» и некоторые перемотки зависали либо игнорировали паузу. В существующем коде `ReplacementEngine` был механизм `suspend("seek_timeout",retryDelay())`: он освобождал вторичный декодер, восстанавливал оригинальный источник, затем **снова разрешал попытку** того же трека. Несколько проблемных `MediaPlayer.seekTo` могли давать замкнутую повторную подготовку. Это **возможный механизм ухудшения**, не доказанная по полевым диагностическим логам причина зависания самого Яндекса.

## Реальное экспериментальное изменение

- `addon/src/.../identitydiag/SeekTimeoutCircuitBreaker.java` — счётчик **только для точного текущего source key**, два невыполненных native seek в пределах 60 с активируют защёлку original-only. Один медленный seek допускается как обычно. Настоящий успешный текущий ACK обнуляет ещё не защёлкнутую серию. Поздний чужой ACK не обнуляет. Защёлка не снимается до настоящего `sourceBoundary/Stop`.
- `ReplacementEngine.suspend("seek_timeout",...)` теперь **центральная точка** для всех трёх существующих путей: timeout при `audioOwner.seekExpired`, timeout по `seeking/seekBudget`, и **отложенный Runnable в `seek()`**, который нельзя забывать. После второго вызова полностью выполняется **прежний безопасный** `release` (тишина вторичного декодера, возврат исходного усиления), затем `completedKey=текущий`, `audioOwner.unsupported("repeated_seek_timeout")`, статус «играет оригинал до следующей песни». Никаких команд `play/pause/seek` к самому Яндексу этот механизм не отправляет.
- Отдельный guard в `ReplacementEngine.update` запрещает при перемотке назад той же песни убрать original-only. Оригинальный `completedKey` вообще-то снимается при возвращении текущей позиции более чем на 1,5 с назад; эта особенность исходного движка не должна повторно запускать уже дважды упавший native decoder.
- Вызов native `OnSeekComplete` оборачивается `onDecoderSeekComplete`: только ACK **действительно in-flight** seek, завершившийся подтверждённым aligned-состоянием текущего ключа, очищает ещё не защёлкнутый streak. **Сам `completeSeek()` и `seek()` сохранены побайтно**, SHA freeze `check_0385_seek_baseline.py` проходит. Production Test.50 и подписанный APK не менялись.

## Проверки

CI `#42843272827` на данном коде:

- **106 018** чистых модельных проверок `TestSeekTimeoutCircuitBreaker`: двойные задержки/окна/ACK/clock rollback, 50 000 обычных новых треков, Stop/Next и сохранение защёлки.
- **17** тестов `TestRepeatedSeekTimeoutRecovery` на самом `ReplacementEngine` с mock Android `MediaPlayer`: первая попытка восстанавливает оригинал и допускает обычный retry, вторая незавершённая native seek блокирует вторичный вывод, перемотка назад не разблокирует, настоящий Next обнуляет.
- **21** независимый `addon/Test*.java` host-gate, полный Java Android API36 compile и D8 native `classes.dex`, прежние тесты аудио/Next/streaming.
- `check_0385_seek_baseline.py` PASS: старые seek submission / callback / full-local-file source selection побайтно совпадают с принятой моделью.
- Все стандартные release-contract negative cases и DEX/provenance проверки SUCCESS.

Указанные результаты — **host/CI**, не доказательство физического исправления звука, паузы или перемотки на HONOR. Не объявлять «Дым»/«Раскол» исправленными без отдельного слушания и диагностики.

## Ограничения и следующие действия

- Механизм **fail-open**: он не заставляет сам Яндекс выйти из настоящей паузы и не ускоряет загрузку отсутствующих sparse ranges. Он прекращает только повторные попытки нашего вторичного аудио, оставляя оригинал.
- Следующий осмысленный шаг: сравнить тайм-ауты и источник на реальной **отдельной тестовой версии** и уже потом решать, разрешать ли сборку подписанной Test.51 для владельца. **Не публиковать/не устанавливать APK автоматически.**
- Source-first Windows 0.24.9 и Android 13 own-only MediaPlayer остаются независимыми: ни один не доказывает выбранный `Lemb` в настоящем Android-Яндексе.
- **Не менять** принятую Test.50, стабильный Android, HONOR, установку Яндекса, Windows, расширение, сервер/API/БД, подпись, DRM и Play Protect.

**Статус:** экспериментальный код **CI GREEN**, физическое устранение прежних зависаний **НЕ ПРОВЕРЕНО**.
