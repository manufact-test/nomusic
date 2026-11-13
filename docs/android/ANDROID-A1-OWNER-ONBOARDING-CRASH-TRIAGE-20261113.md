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

## Existing diagnostic capture

The module already emits privacy-limited finite events for hook registration and fatal/exit witnesses, including:
- `ARMED`, `FATAL_HOOK`
- `FATAL_DISPATCH` and finite throwable categories
- `SYSTEM_EXIT`, `RUNTIME_EXIT`, `PROCESS_KILL`
- existing AppMetrica and native audio hook registration events

The included `capture-diagnostics.bat` filters only the CELIKOM observer tag and lines containing `event=`. It is suitable for the immediate first pass; it does not collect full logcat, raw stack traces, audio, credentials, account tokens, or URLs.

### One requested owner action

1. Connect the same phone to the existing Windows PC by USB; enable USB debugging and authorize that PC if not already done.
2. Extract the previously supplied diagnostic bundle and run `capture-diagnostics.bat` **before** opening the clone.
3. Open the CELIKOM diagnostic clone and reproduce exactly the already-described intro sequence through the fourth indicator/page and next arrow until it returns to launcher.
4. Wait about 5 seconds, then press Ctrl+C in the capture window.
5. Send only `CELIKOM-A1-Audio-Diagnostics.txt`. No passwords, SMS codes, tokens, screenshots of account pages, or general logcat.

Do not uninstall the clone, clear its data, disable Play Protect, or modify/remove original Yandex. Do not attempt music playback; it is currently unreachable.

## Engineering next steps

1. Inspect the finite observer events: confirm module armed/fatal hooks registered; determine whether a Java fatal dispatch, explicit exit/kill, or no process-level event was observed.
2. If events are insufficient, add a narrow privacy-safe Android 13 MAIN-process `ApplicationExitInfo` + crash-buffer classifier (fixed enums only; no raw message, stack, paths, IDs or tokens exported).
3. Reproduce the same onboarding UI path in disposable ARM13 CI. Existing idle-only 75-second test is insufficient.
4. Identify the actual root cause before changing code. Any fix must be clone-only and narrowly scoped, with a fresh backup and paired original-first tests.
5. Re-run onboarding through the final arrow, then verify login and only then begin real audio source observation / B42 integration.

No second player. No architecture change. Do not touch Test.50, Windows, production, original Yandex or the proven Firebase startup baseline. Do not claim audio or full app acceptance based on the prior 25/25 idle test.
