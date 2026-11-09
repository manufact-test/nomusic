# Android source-selection smoke — OWN app, 2026-11-09

A short on-device experiment testing Pause/Seek/Next, fallback and installation with Play Protect left ON. This is NOT Yandex and is NOT the CELIKOM product.

Package: pro.celikom.armv7loaderhost.audio, independent of official ru.yandex.music and both previous CELIKOM test apps.

- Xposed is scoped only to .witness and .audio test packages.
- Module intercepts own AudioSmokeSource.chooseA(), changes 0 to 1 before MediaPlayer.setDataSource() and prepareAsync().
- Synthetic 8-second WAV tones entirely in memory: A original 440Hz, A alternative 660Hz, B original 330Hz.
- ONE platform MediaPlayer, generation fences old callbacks.
- Controls: Start A; Pause/Resume; Seek +3 seconds; Next B; Fallback A; Stop. Screen shows hook, chosen source, playback state, counts.
- No network, files, permissions, Yandex code, account or access tokens. No root, no Play Protect bypass.
- If Play Protect blocks APK, stop and send screenshot. No override.

Success here does NOT prove that the real Yandex FileInfoDto or native decoder will accept source substitution.
CI workflow: .github/workflows/android-native-armv7-audio-smoke.yml.
Never distribute patched Yandex APKs.

## Exact successful CI and owner APK (09.11.2026)

- CI SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/42652387877
- Built from commit 504cf3e6ff1fbd6567b292b964a40c8f3a836b7b; signed ephemeral lab APK, separate app ID pro.celikom.armv7loaderhost.audio. No installed user app was modified.
- Signed APK: CELIKOM-ARMv7-AUDIO-SMOKE-Test.apk; size 3,068,955 bytes; SHA256 d2f759f2e5fcb2a79620ace007182315621775c49d072eddddebbc292fd44ea8.
- CI artifact: https://github.com/manufact-test/nomusic/actions/runs/42652387877/artifacts/13690607138; same APK uploaded to user's personal ChatGPT Library at /CELIKOM-ARMv7-AUDIO-SMOKE-Test.apk.
- CI gate: pinned original LSPatch 1.2, sigbypass=0, 1 exact-scope own-source libxposed module, 32-bit ARMv7, no Android app permissions or Yandex components, no Play Protect bypass.
- **Runtime status: NOT TESTED ON HONOR**. Neither Play Protect result nor actual sound, pause, seek, Next, fallback or live Xposed pre-prepare selection have been confirmed. Full audio sound test required manually.
- Owner check: install alongside original official Yandex and previous OWN lab apps, never uninstall or update official ru.yandex.music. Open CELIKOM Audio Smoke Test, test Start A (660Hz if source hook), Pause/Resume, Seek +3s, Next B (330Hz), Fallback A (440Hz). Report screenshot with hook armed/source changed/Prepare/Pause/SeekComplete/Next/Errors counters. If Play Protect blocks, stop and report without bypass.
- A green own MediaPlayer test is NOT proof of compatibility with the native Yandex ExoPlayer/eed decoder; do not treat it as audio replacement on the actual Yandex app.

## Owner device screenshot — runtime counters PASS (2026-11-09 19:33 device time)

Owner submitted `Screenshot_20261109_193331.jpg` from HONOR 50. Visible results:
```
Module hook ARMED: YES
Source changed BEFORE PREPARE: YES
Track: A
Source: ORIGINAL A 440Hz
Prepared: NOT YET
Playing: NO
Fallback: YES
Prepare=3  Pause=1  Resume=1
SeekComplete=1  Next=1  Errors=0
Last: STOPPED
```

**Proven on actual phone:** owned libxposed module loaded and intercepted a source-selection result before MediaPlayer.prepareAsync; asynchronous prepare callback was counted 3 times, Pause/Resume, Seek completion, Next and manual original-source Fallback have nonzero counters, 0 registered errors. The photo shows final STOPPED state; `Prepared: NOT YET` and `Playing: NO` are expected once the player has been released. `Fallback: YES` corresponds to the owner's manual Fallback button, **not proof of an automatic decoder-error recovery**. No verbal confirmation of audible tone quality, gaps or clicks yet.

**Limits:** This is a CELIKOM-owned synthetic `MediaPlayer` test, not Yandex's private player or decoder; it cannot prove compatibility with Yandex FileInfoDto/eed, timing, DRM, radio/playlist race conditions, Play Protect distribution decisions, or sound without artifacts. User's installed `ru.yandex.music` and its offline downloads remain untouched.

**Next:** stop repeating own-source laboratory stages. The next implementation gate must use a lawful, safe, separated *native Yandex* test environment / version with single original player and version-pinned read-only FileInfoDto hook before making any audio mutation. Never ask to uninstall the owner's official Yandex. No current native-Yandex audio PASS.

## ФИНАЛЬНЫЙ owner-аудио PASS — 09.11.2026

После скриншота (19:33) владелец подтвердил на слух: три синтетических звука воспроизводились, Pause/Resume/Seek/Next работали корректно. Это заменяет прежние статусы 'real audio not tested' и 'verbal confirmation pending' **только для собственного Audio Smoke APK**. Полной native Yandex аудиоподмены пока нет; отсутствие щелчков в native Яндексе не подтверждено. Fallback YES на скрине — ручной выбор оригинала, не автоматический fallback при ошибке. Повторять own-audio испытания не требуется; дальнейший фокус — реальный native Yandex. См. ANDROID-NATIVE-CURRENT-HANDOFF-2026-11-09.md.
