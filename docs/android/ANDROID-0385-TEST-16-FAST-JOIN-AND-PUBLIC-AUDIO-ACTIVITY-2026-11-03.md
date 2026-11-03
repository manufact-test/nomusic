# CELIKOM Android · Test.15 полевой эталон и безопасная Test.16
Дата: 2026-11-03. Репозиторий manufact-test/nomusic. Рабочая ветка feature/android-0385-intro-join-investigation-20261102.

## Неприкосновенный лучший результат
- **Test.15** 0.3.85-test.15/code86100: владелец на HONOR оценил её лучшей из всех испытанных; ориентировочно 70% переходов без заметного стыка, присоединение в ту же секунду. Остаточный шов слышен у песен с резким началом.
- Backup: **backup/android-0385-test15-best-owner-20261103**, SHA **6fde1e48179ecb812f1def16067f18bf0d9c3003**. Functional Test.15 SHA 4838ccee4aa4628dce68437ebbf00d4dfc30ce27, signed artifact https://github.com/manufact-test/nomusic/actions/runs/41674369584/artifacts/13248949184.
- Никакая Test.16 не становится эталоном до подтверждения владельца. Стабильная 0.3.85/code86, Hostinger/stable.json, backup и PR #37 неизменны.

## «Дым» — независимая проблема источника
- Новая запись: SVID_20261103_194429_1.mp4, лог CELIKOM-combined-20261103-194654.txt, не помещать приватные медиа/лог в Git.
- «Дым» Лёша Свик, catalogueTrackId 39949113, mediaAlias 397, duration 219660ms. После начала source в elapsed_ms 133723 замена вступила в elapsed_ms 133937 (214ms); measured replacement duration 220029ms.
- На видео около 2:02–2:15 палец переводит UI Яндекса к 1:46, 3:21, 3:38, назад 1:57. Но с 133937 до перехода на новую песню в 147121 доступный Media3 controller *не сообщает* ни SAME_ITEM_SEEK, ни pause, source остаётся isPlaying:true и монотонно движется ~0–10s. Поэтому CELIKOM продолжает независимый decoder; её подтверждённый механизм user seek здесь не получает события.
- Ранее добавленный passive MediaBrowser читает platform media session, но в этом эпизоде также не даёт доверенного seek. Не объявлять исправленным.
- Официально разрешённая без дополнительной permission Android API26 AudioManager.getActivePlaybackConfigurations / AudioPlaybackCallback отдаёт только **анонимизированные активные конфигурации** других плееров, с их аудио usage. Согласно AOSP PlaybackActivityMonitor.anonymizeForPublicConsumption, нельзя получить чужой UID, trackId, playback position и надёжно приписать событие Яндексу. Нельзя на одном счётчике останавливать/двигать звук; ложные положительные события повредят удачные песни.
- Test.16 добавляет только change-only trace **platform_audio_activity_observed** (счётчик media/other + Media3/наш decoder в момент события, чёткое observationOnly=true). Не делает stop/pause/seek, не требует никакого нового permission. Из сопоставления видео и лога станет ясно, отражает ли Android native pause данного трека независимо от Media3.

## Единственное изменение времени склейки Test.16
- При уже готовом decoder fast read-only sampling source прежний INITIAL_MS=35, STEP_MS=60 -> **15/30ms**; бюджет 1200ms и guards (armed, same identity, trusted session, source playing, ready decoder, no attached effect) сохранены.
- Это может сокращать выборку на десятки миллисекунд, когда событие приходит между предыдущими 60ms опросами. **Не** меняется native seek, seek-ACK, owner grant, effect source gain, handover 40ms advancing decoder, strict drift 100ms, 0ms exclusive output, cache-prime, 1100ms speculative enqueue и единый audioWork.
- Светлая резкая атака по-прежнему может выдавать различие исходной редакции и replacement: без PCM фазы источника «идеальный бесшовный» не гарантирован. Не реанимировать длинные fades, которые уже вызывали провалы.
- Host gate теперь исполняет TestFastJoinPollPolicy; check_audio_architecture охраняет read-only observer. Отдельная signed Test.16 versionCode 86101 и маркировка CELIKOM Test.
- **Полный CI SUCCESS**: https://github.com/manufact-test/nomusic/actions/runs/41679911010 . **Подписанный Test.16 APK в ZIP**: https://github.com/manufact-test/nomusic/actions/runs/41679911010/artifacts/13251069084, artifact 13251069084, имя `CELIKOM-Test-0.3.85-test.16-code-86101`. Functional SHA `66dfa4eb5b4ca05b0c26abb8e629131de1ac64e4`. Stable publisher job **SKIPPED**. Проверка на телефоне: **PENDING**.

## Одно тестирование владельца
В Test.16 проверить серию знакомых ярких начал против Test.15, затем «Дым» паузой и несколькими seek; далее обычные seek/pause на 2–3 других песнях. Приложить один combined и видео. Если хуже, немедленно считать Test.15 эталоном и не переносить код в stable.
