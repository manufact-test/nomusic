# CELIKOM Android — Test.23 selective Test.16/17 recovery on immutable Test.15
Дата 2026-11-04. Статус: эксперимент, физическое прослушивание владельцем PENDING.

## Почему отдельная ветка
- Test.15 0.3.85-test.15/code86100, backup branch `backup/android-0385-test15-best-owner-20261103` SHA `6fde1e48179ecb812f1def16067f18bf0d9c3003`, собственная signed APK в библиотеке владельца. На HONOR исторически лучшая (~70% стыков), но не идеальна: быстрое перелистывание оставляет очереди загрузок, холодные подключения 8–10 секунд.
- Test.16/Test.17 оригинальные APK были отвергнуты владельцем; 16 — звуковая регрессия, 17 — пауза/seek/старт. Поэтому нельзя cherry-pick всего коммита либо объявлять их как принятые. Исходные commits 66dfa4eb5b4ca05b0c26abb8e629131de1ac64e4, b24c6d9b527fd5810ba9ef8287c730147acbd3b1 сохранены отдельно.
- Test.18–Test.22 не служат основой. Test.22 Range downloader вызвал многосекундные ожидания и отвергнут. Подписанная оригинальная Test.18 также сейчас даёт плохую работу на HONOR. Стабильное основное приложение CELIKOM 0.3.85/code86 и OTA/Hostinger untouched.

## Что точно объединено из Test.16
1. FastJoinPollPolicy: 15/30 ms (вместо 35/60) только внутри 1200 ms ограниченного read-only окна при готовом muted decoder. Не снижены guard drift/owner/seek; это частота наблюдений, не новая перемотка.
2. Анонимизированный Android AudioManager.AudioPlaybackCallback change-only: `platform_audio_activity_observed` для расследования пропущенной Яндекс-паузы. Не получает позицию, trackId/UID чужого приложения, не посылает play/pause/seek, не требует новых разрешений. Отключается при finish/onDestroy.

## Что точно объединено из Test.17
3. `replacement_lookahead_cache_reused`: при новом fresh API resolve и проверке exact descriptor key уже скачанный полный файл для следующего трека берётся из ограниченного 8 entry / 96MiB cache вместо повторной загрузки.
4. `replacement_interrupted_file_retained`: полностью скачанный файл, прерванный сменой трека до decoder prepared, может попасть в тот же bounded cache только для track_changed/identity_changed. Partial/failed/auth/logout/Stop не сохраняются.

## Что категорически НЕ включать
- DirectSessionObserver / дополнительный Media3 controller Test.17: он не смог подключиться к проверенному TYPE_SESSION на HONOR и совпал с регрессией пользовательской паузы. Код его нигде не используется.
- Test.18 aggressive cancellation, Test.19 DSP restart, Test.20 medium drift correction, Test.22 FastAudioTransfer multi-range. Весь старый audio owner, source gain, seek arbitration, auth, update policy и streaming/full-file path Test.15 остаются.
- Не выдавать false-positive match при смене edition; не сохранять неполные файлы.

## Verification
Изолированный package `pro.celikom.nativeprobe.test`, label CELIKOM Test, version 0.3.85-test.23/code86108 (можно обновить более старую Test.15 без удаления). Host + Native CI, signed Android API36/D8 test APK, certificate original verified, stable publish jobs SKIPPED.
Тесты: existing TestFastJoinPollPolicy, TestLookaheadPrefetchHandoff + 4 Test17 cache cases, structural rejects DirectSessionObserver and FastAudioTransfer, Test15 seek/ACK regression. Успех CI доказывает только контракт, **не улучшение звука на телефоне**.

## Acceptance
Один совместный field run: первая неизвестная песня, 5 быстрых Next, возврат к уже прослушанному треку, обычная пауза, пауза из Android controls и палец seek на «Дым»/«Нас не понимают вообще». Смотреть combined diagnostic: cache_reused, interrupted_file_retained, download queue waits, replacement_transition_complete, platform_audio_activity_observed; сравнить без ухудшения относительно Test.15. Если любое значимое ухудшение: возвращаемся к сохранённой Test.15 без перепаковки.
