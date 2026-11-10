## VERIFIED GREEN CHECKPOINT 2026-11-10 / cross-platform Windows W57

- **Current Android native hooklab code SHA**: 4166b3f5f75df45b717308356995af22e1babc3c. [GitHub Actions CI #42800426147 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42800426147): full synthetic native source, event order and playback-state tests; Android libxposed module debug APK compiles and signature/module metadata validates. **No actual Android Yandex audio hook or source replacement proven**.
- New passive Android framework MediaSession.setPlaybackState observer tracks published enum and aggregate rapid Play/Pause/Buffering/Error reports. It reads **ONLY public enum** and cannot know track or user intent; multiple MediaSessions and normal user pause can look like quick state flips. Never connect to source replacement or decoder admission.
- Windows **0.24.7** owner-verified first real audible approved replacement inside real Yandex desktop. Native audio GET 206 (2), 403 (0). W56 root cause is **desktop-specific** vendor-added second ?vsid query corrupting signed source URL sid, fixed without HMAC bypass. Android has no verified equivalent, so DO NOT port the desktop URL padding blindly. Full review at docs/android/ANDROID-WINDOWS-W57-TRANSFERABILITY-2026-11-10.md.
- **Rollback exact tested code:** backup/android-native-w57-review-playback-state-ci-success-20261110 (same SHA as above); pre-review baseline backup/android-native-before-windows-breakthrough-review-20261110 at 22d5ef25. Do not touch stable Android Test.50, owner's HONOR or Yandex, Windows 0.24.7 or production server. No APK suitable for user installation.

---
## 10.11.2026 IMPORTANT: verified CELIKOM Windows W57 audio breakthrough reviewed

**Windows 0.24.7 real replacement audio heard by owner, real HTTP206, 0 HTTP403.** Desktop Yandex DownloadInfoSource appended its own second ?vsid query to already signed audio URL and Windows team fixed the resultant session-field corruption with a narrow media-only trailing guard. This is DESKTOP Electron-specific; not evidence the native Android player also does that. See docs/android/ANDROID-WINDOWS-W57-TRANSFERABILITY-2026-11-10.md.

Experimental native Android observer has new public playback state *aggregate-only* witness and synthetic JVM tests; no audio source swap and no actual patched native Yandex ARM run yet. Windows accepted baseline, Android Test.50 and HONOR unchanged.

---
## VERIFIED CHECKPOINT: 10.11.2026 — CI SUCCESS / NO NATIVE AUDIO CLAIM

**Latest verified CODE SHA:** `c5f76316f8a00e8b30c2cdae402fe0ec64dfeea2` on `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
**[CI #42798290760 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42798290760):** pure-Java `NativeEventOrderProbeTest`, Python categorical/redaction tests and existing source/identity tests passed; Android observer APK built, metadata and signing structure verified. A previous CI #42798154589 failed only because its guard still expected an old log phrase; the guard was corrected and entire CI reran green.

**What changed from pre-experiment SHA `1ad5870f`:** pure-Java bounded FileInfo/metadata temporal classifier, native read-only hook observer integration, distinct FileInfo vs MediaSession counter categories, aggregate logs, updated safe emulator log parser and unit tests. There is no source mutation. Every real audio source comparison still requires a physically valid native-Yandex host; metadata temporal proximity is **not** trackId+edition proof. Do not use it in `NativePrePrepareAdmission`.

**Backups:** `backup/android-native-before-temporal-event-probe-20261110` at `1ad5870f`; `backup/android-native-temporal-event-probe-ci-passed-20261110` at `518dd07d`. Owner Test.50 baseline unchanged. No APK for manual Yandex testing, no production, no HONOR changes, no ChromaSync purchase.

---

## UPDATE 10.11.2026 — temporal diagnostic CI green + meaningful log summaries

**CI [#42797745570](https://github.com/manufact-test/nomusic/actions/runs/42797745570): SUCCESS 2/2**: >36k synthetic rapid Next/prefetch/privacy assertions, ARM source-only Xposed observer APK compiles and signature metadata passes. NO real Yandex host/runtime or source replacement.

Follow-up fixes: `NativeHookEntry.safeCount` now uses **metadata update** vs **FileInfo conversion** labels correctly, and every 20 metadata updates prints **only aggregate categories** (one nearby source, ambiguous multiple, none, clock discontinuity). `diagnose_emulator.py` recognizes distinct `CONVERSION_WITNESSED`, `METADATA_WITNESSED` and `TEMPORAL_ORDER_AGGREGATE` without exposing raw log lines. New categorical-parser unit tests; no song/account data processed. Snapshot backup `backup/android-native-temporal-event-probe-ci-passed-20261110` (code from green CI).

This does NOT prove the correct track / edition, is NOT plugged into `NativePrePrepareAdmission`, and cannot replace audio. Still requires a verified compatible native ARM Android host, not an x86 test or user HONOR installation.

---

## UPDATE 10.11.2026 — Native FileInfo / MediaSession temporal witness (NEWEST)

**Previous checkpoint and rollback:** `backup/android-native-before-temporal-event-probe-20261110` at `1ad5870f05105ffc5f9a105a052aca211ebaa6a7`.

Implemented `NativeEventOrderProbe.java`: a bounded, pure-Java diagnostic, now connected to the existing read-only FileInfo converter hooks (modern and legacy) and platform `MediaSession.setMetadata` observer in `NativeHookEntry`. Every method proceeds unmodified. Classifier records only monotonic event ordering, not absolute timestamps, IDs, editions, URLs, source responses, accounts or metadata values.

Diagnostic categories: one nearby FileInfo (temporal coincidence only), multiple nearby FileInfo (ambiguity/prefetch), metadata without recent FileInfo, clock discontinuity. Source event queue saturates at 2 and is consumed once for each metadata callback. The 12-second window is a provisional upper diagnostic bound, NOT a performance benchmark. `SINGLE_RECENT_FILEINFO_TEMPORAL_ONLY` is explicitly NOT a verified track-to-source match and may never authorize replacement. `NativePrePrepareAdmission` remains disconnected from real native decoder.

`NativeEventOrderProbeTest.java` exercises duplicate metadata, 12,000 Next/radio bursts, 20,000 prefetch events, expiry and clock reversal. Hooklab CI compiles/runs it as well as the Android libxposed module build. No user APK yet: actual runtime Yandex hook and native audio replacement still UNVERIFIED. Owner HONOR, stable Test.50, server and production untouched. ChromaSync paid/manual patcher rejected, no outreach.

---

## UPDATE: open-source native playback event evidence (10.11.2026)

Owner personally confirmed ChromaSync Android requires payment and manual patcher; **do not ask for it**, do not claim it free. No candidate outside CELIKOM was installed or paid for.

Checked actual public code, **not marketing alone**:
- [windyx0/YaMusicLsposed](https://github.com/windyx0/YaMusicLsposed/blob/main/app/src/main/java/io/github/windyx0/yamusiclsposed/MainHook.kt) (MIT): hooks Android framework `android.media.session.MediaSession.setMetadata` from within Yandex process; its sample reads/logs metadata, **we intentionally DO NOT**.
- [daanqq/YaMusicTabs](https://github.com/daanqq/YaMusicTabs) (source available): modern libxposed `onPackageReady` with the Yandex host classloader to hook native UI. No audio source swap.
- [errorman-awful/YMDownloaderXposed](https://github.com/errorman-awful/YMDownloaderXposed): public GitHub repository has README/demo, **no Android source**, not a reusable implementation.
- ChromaSync Android still has only README publicly; exact paywalled module source unavailable.

**Implemented in our native FileInfo module:** passive, version-locked `MediaSession.setMetadata` observer with only throttled integer counter and immutable original call path. Does not inspect MediaMetadata fields, track IDs, titles, URLs, queues, accounts or audio. It can later establish whether a native Android host process emits media metadata changes, *independently* of our already present FileInfo converter counters. A media session event DOES NOT confirm trackId+edition+generation identity or decoder source. Never use it to select alternate audio.

This is a concrete open-source-informed engineering improvement, not a full working native source replacement; must verify module build CI separately and real Yandex runtime only on suitable isolated ARM hardware. Primary HONOR, Test.50, other branches, Windows, extension, server/DB/production unchanged. Backup `backup/android-native-before-open-source-metadata-20261110` before these changes.

---

## UPDATE 10.11.2026 — signed native ExoPlayer implementor truth (LATEST)

**Verified code commit:** `fcd7550b86ee93082ff3a8b119e38b29d02482d8`. **Rollback backup:** `backup/android-native-real-media-implementation-evidence-20261110`.

- [Native original media engine CI #42791262439](https://github.com/manufact-test/nomusic/actions/runs/42791262439) **SUCCESS**: standard class `ExoPlayerImpl` absent, `ExoPlayer` interface defined.
- [Exact DEX type hierarchy #42791641169](https://github.com/manufact-test/nomusic/actions/runs/42791641169) **SUCCESS**: 4 obfuscated concrete implementors `Lfxc;`, `Lro7;`, `Lwxc;`, `Lyzt;`, not necessarily player/decoder for current audio.
- [Inherited prepare body scan #42791829407](https://github.com/manufact-test/nomusic/actions/runs/42791829407) **SUCCESS**: no `prepare()V` bodies in those classes or their scanned parent chains. **Do not blindly hook named `ExoPlayerImpl.prepare`**.
- [Existing read-only hooklab #42791829435](https://github.com/manufact-test/nomusic/actions/runs/42791829435) **SUCCESS** module build/synthetic only.
- [Native AArch64 Linux GitHub runner #42792130918](https://github.com/manufact-test/nomusic/actions/runs/42792130918) **SUCCESS probe** but `/dev/kvm` unavailable; **not** usable native ARM Android guest.

Full bounded evidence `docs/android/ANDROID-NATIVE-REAL-PLAYER-IMPLEMENTOR-EVIDENCE-2026-11-10.md`. All code only on native hooklab branch. No real Yandex source/decoder/runtime hook proven; no Android CELIKOM APK to install. NO Yandex outreach. Primary device/Test.50 untouched. Next requirement remains a safe real native ARM Android test host, then trackId+edition+generation→decoder pre-prepare witness. Do not repeat stale x86/AМetrica experiments.

---

# CELIKOM Android — НАЧНИ ЗДЕСЬ (10.11.2026, проверенный текущий статус)

**GitHub:** `manufact-test/nomusic`.
**Рабочая ветка:** `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
**Кодовый HEAD, CI SUCCESS:** `18e0d1126187a2c2a26eeb7df7a25de935e19a54`.
**Точный бэкап исходников с рабочим кодом:** `backup/android-native-hook-classloader-verified-20261110`.
Любой более новый HEAD после этого — это документационные изменения; сначала проверить ref.

## 1. Что требует владелец. Не менять без его решения

**Один нативный проигрыватель Яндекс Музыки.** Пользователь входит только в самом Яндексе, пользуется родными плейлистами, радио, паузой, перемоткой и Next. CELIKOM выбирает подтверждённый альтернативный аудиоисточник только если он безопасно связывается с *текущими* trackId + edition + generation до decoder prepare. Иначе оригинал. Никакого второго MediaPlayer, WebView, отдельного fake player, чужих OAuth/Passport токенов или обхода DRM/Play Protect/подписей. Разрешённая модель установки в будущем может использовать **совместимую патченную нативную Яндекс Музыку, как ChromaSync**, но не поверх официальной подписи без осознанной смены установки.

**Яндексу ничего не отправлять**. Идею партнёрского письма владелец категорически отверг. Старый `ANDROID-NATIVE-YANDEX-PARTNER-INQUIRY-2026-11-10.md` — только архив, НЕ отправлять.

**Не трогать:** стабильную эталонную Android Test.50 `backup/android-test50-exact-source-owner-accepted-20261108`; Яндекс Музыку и локальные загрузки владельца на HONOR 50; Windows, расширение, API, БД, production. Не предлагать владельцу тесты синтетического APK вместо проверки подмены в настоящем Яндексе.

## 2. Фактическая архитектура конкурента

[ChromaSync-Mobile](https://github.com/Desai0/ChromaSync-Mobile) заявляет native in-process модуль:
- **Без root:** совместимый оригинальный APK + патчер на устройстве + модуль; может требоваться удаление официального Яндекса из-за разных подписей.
- **С root:** LSPosed + модуль внутри Яндекса.
- В публичном Android-репозитории только README. Прямого исходного audio hook нет. Нельзя выдавать README за подтверждённую реализацию или обещать аналогичные результаты.
- Успех конкурента не делает безопасным наш параллельный клон с другим packageId. Именно этот путь уже потерпел неудачу.

Ещё один исходный пример [daanqq/YaMusicTabs](https://github.com/daanqq/YaMusicTabs) использует modern libxposed `onPackageReady` / classloader для **UI**, не для аудио. Это подтверждает полезность lifecycle-подхода, но не FileInfo->decoder.

## 3. Что реально подтверждено CELIKOM

- **Свой ARMv7 libxposed in-process witness на HONOR:** скрин владельца `Module hook armed=YES`, `onCreate intercepted=YES`, [CI 42643802887](https://github.com/manufact-test/nomusic/actions/runs/42643802887). Это ТОЛЬКО собственное приложение, не Яндекс.
- **Подписанный издателем Яндекс `2026.10.3 #170gpr`** (5 splits, 6 DEX) запускается в чистом изолированном Android 11 x86 с ARM translation. Из его DEX статически найдены `FileInfoApi/OldFileInfoApi @Query("trackId")` как param 0, `sw7.y0/z0(FileInfoDto,boolean):eed`. Реальная текущая edition+generation к конкретному decoder prepare ещё НЕ доказана.
- **Параллельный clone другого packageId**: MAIN `EXIT_SELF status 0`, вспомогательный `:AppMetrica` остаётся. Точная причина самозавершения не определена, **это не доказанный anti-tamper или несоответствие подписи**. См. `ANDROID-NATIVE-MAIN-EXIT-AUDIT-2026-11-10.md`.
- **Same-package LSPatch на x86/ARM-translation AVD**: и с модулем, и без модуля раньше падал в загрузчике `liblspatch.so` / `UnsatisfiedLinkError` ДО нашего hook; [42622523007](https://github.com/manufact-test/nomusic/actions/runs/42622523007), [42622723034](https://github.com/manufact-test/nomusic/actions/runs/42622723034). Это не проверка настоящего ARM. **Не повторять эти x86 тесты.** `.github/workflows/android-native-yandex-emulator.yml` переведён на manual-only.
- Уже реализованы *синтетические* `NativePrePrepareAdmission`, `NativeSourceGate`, `NativeTrackIdentityGate`: точные edition/generation/ready/expiry проверки. Ни один из них не включён в настоящий decoder.

## 4. Новый реальный код в этой сессии

`android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeHookEntry.java`:
- После exact-version проверки сохраняет только host Context, а при `onPackageReady` повторно пытается установить **read-only** хуки, если на `Application.attach` split-классы ещё не были готовы.
- Частично установленные хуки не дублируются: `modernHooked`, `legacyHooked`, `accessorHooked`.
- `HookSpec.findConversionPair(preferred, fallback)` требует **обе** точные сигнатуры `sw7.y0/z0` из **одного** classloader. Если preferred loader ещё не готов, пробует validated Context loader. Нет смешивания моделей из двух loader и нет fuzzy fallback.
- `HookSpecTest` проверяет точный version gate, пару, отказ при неподходящем loader и fallback.
- **[CI #42790028152](https://github.com/manufact-test/nomusic/actions/runs/42790028152) SUCCESS 2/2:** Java-policy и Android libxposed module APK build. Это НЕ тест реального Yandex hook. Исходники в `18e0d1126187a2c2a26eeb7df7a25de935e19a54`, отдельный бэкап `backup/android-native-hook-classloader-verified-20261110`.

**Изменений источника звука нет.** Модуль по-прежнему считает конвертации без чтения trackId, URL, ключей, токенов. НЕ продавать это владельцу как работающий Android CELIKOM.

## 5. Точный следующий рубеж

1. Нужна воспроизводимая **гостевая нативная ARM-среда** с совместимым same-package подготовленным Яндексом и без риска для основной установки; отдельный аппарат/разрешённая cloud ARM с допустимой установкой. Старые x86 AVД/clone нельзя выдавать за ARM proof.
2. Только после успешного native MAIN UI/login **в Яндексе**, Play Protect и hook witness: получить read-only runtime связь `current trackId + edition + generation -> FileInfoDto -> фактический source/decoder BEFORE prepare`. Не собирать пользовательские токены или чужие аудиопотоки.
3. Только после такого доказательства связывать `NativePrePrepareAdmission` с реальным нативным входом и затем тестировать «Раскол» `42884423`, «Дым» `39949113`, начало без «пшика», Next, radio, seek/pause. Никаких выдуманных CI green.

**Сейчас** без такого разрешённого native ARM runtime `NO-GO` для установки/теста владельцем; не требовать от него удалить официальный Яндекс и не запускать бесконечные emulator/DEX/AМetrica эксперименты. Если появится настоящий тестовый кандидат, обращаться к владельцу **один раз, только для реальной ручной проверки**, заранее называя риск удаления/подписей.

## 6. Исторические материалы

Старый разросшийся NEXT-CHAT с устаревшими и частично противоречивыми решениями сохранён **только для истории**: `docs/android/ARCHIVE-NEXT-CHAT-ACCUMULATED-20261110.md`.

Контекст: `docs/android/ANDROID-NATIVE-COMPETITOR-PATH-CORRECTION-2026-11-10.md`, `docs/android/ANDROID-NATIVE-LSPATCH-EMULATOR-ROOT-CAUSE-2026-11-09.md`, `docs/android/ANDROID-NATIVE-FINAL-ADMISSION-HANDOFF-2026-11-10.md`. Во всех спорных местах приоритет у настоящего документа и новых подтверждённых результатов CI, не у старых прогнозов.
