# CELIKOM Android A1 — owner-device onboarding exit triage (13 Nov 2026)

## Current observed result

- Device: owner's existing HONOR 50 / Android 13.
- Diagnostic APK: `CELIKOM-A1-Native-ReadOnly-Diagnostic.apk`, package `pro.celikom.yandex.nativeclonelab`, Yandex Music 2025.10.4 clone.
- Installation succeeded; Google Play Protect raised no block or warning. App is installed separately beside original Yandex.
- First launch waited approximately 15–20 seconds, then displayed Yandex My Wave/personal recommendations and introductory navigation screens.
- At the fourth of four intro indicators/pages, owner pressed the next arrow. Loading began, then the app closed to Android launcher.
- Owner cannot reach login, track playback, pause/seek/Next, or any audio path. This is the entire report; no further steps were completed.
- The owner uses their existing Yandex account on this same phone if/when the clone reaches authentication. No separate test account is available or required.

## Correct interpretation of prior CI

Workflow [#43450303301](https://github.com/manufact-test/nomusic/actions/runs/43450303301) passed original-first co-install and 25/25 idle MAIN foreground samples over 75 seconds. The test calls `am start` for `MainScreenActivity` and checks PID/resumed activity. It does **not** automate or verify the four intro pages, the next arrow, authentication, track selection, audio, controls, or MediaDataSource calls.

Thus:
- APK packaging/signing/install and original+clone side-by-side are verified.
- Idle main-screen survival is verified in CI.
- Owner-device onboarding navigation is **FAILED**.
- Actual audio path and playback are **NOT TESTED**.
- The APK is not ready for audio testing or release. No root cause is yet proven.

## Replacement on-device diagnostic APK — READY

The replacement build is available after successful Android 13 ARM13 validation.

- Workflow [#43461955113](https://github.com/manufact-test/nomusic/actions/runs/43461955113) **SUCCESS**: original publisher installed first and remained stable 25/25 for 75 seconds; CELIKOM clone installed alongside it and remained stable 25/25; no Metrica fatal suppression observed.
- Separate clone-only control [#43461955329](https://github.com/manufact-test/nomusic/actions/runs/43461955329) **SUCCESS**, clone 25/25.
- Artifact ID `14057522148`, name `CELIKOM-A1-OnDevice-Diagnostic-20261113`, 7-day retention.
- APK `CELIKOM-A1-Native-ReadOnly-Diagnostic.apk`, package `pro.celikom.yandex.nativeclonelab`, Yandex Music 2025.10.4, size 71,430,124 bytes, SHA-256 `9fe9c0139564ead9b499e059065006e4097e833db7c06e7d453fd45f1d75cfe4`.
- The module stores finite CELIKOM diagnostic events in the clone's private files directory, reads Android 13 historical process-exit reason categories on next launch, and adds a small in-window `Сохранить диагностику` button. On tap, it copies the TXT to `Downloads/CELIKOM A1` using MediaStore. No storage permission, USB, PC, ADB or BAT is needed.
- The build and paired startup gate passed. **The button's actual tap/export flow has not yet been exercised on the owner's handset**; owner confirmation is still required. No onboarding tap-through, authentication, playback, readAt calls, or audio substitution was tested. This APK remains diagnostic-only, not a release.

### One owner action

1. Uninstall only the previous diagnostic clone installed from the earlier CELIKOM test APK. Its temporary signing key is different, so Android cannot update it in place. **Do not uninstall the original Yandex Music app** (`ru.yandex.music`).
2. Install the new APK.
3. Repeat the already-described four intro pages and final arrow until it returns to the Android launcher.
4. Reopen the CELIKOM clone. Tap `Сохранить диагностику`.
5. Attach the TXT from `Downloads/CELIKOM A1` to this ChatGPT conversation.

No extra Yandex account is needed; use the existing account only if/when the clone reaches sign-in. Do not send credentials, SMS codes, tokens, screenshots of account pages, or general logs.

If the button is absent or saving fails, do not reinstall or clear data. Tell us exactly what happened and send a screenshot of the app screen without personal information.

## Engineering next steps

1. Inspect the returned finite event report and Android exit reason category.
2. If it proves a Java fatal, explicit exit/kill, native crash, or ANR, trace that exact cause and reproduce the same intro navigation in disposable ARM13 CI.
3. If the app simply finishes an Activity without a process exit, add a narrowly scoped lifecycle witness.
4. Fix only the CELIKOM clone; keep original Yandex, Test.50, Windows, production and the A1 architecture untouched.
5. Re-run the four intro pages, then verify login. Only after that return to actual MediaDataSource/MediaExtractor playback observation and B42 integration.

No second player. No architecture change. Do not claim audio or full app acceptance from idle 25/25 startup tests.
