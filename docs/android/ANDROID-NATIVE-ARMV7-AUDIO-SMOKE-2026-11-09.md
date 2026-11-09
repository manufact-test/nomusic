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
