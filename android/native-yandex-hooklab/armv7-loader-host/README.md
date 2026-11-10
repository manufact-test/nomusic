# CELIKOM own-source ARMv7 native loader host

Independent app: pro.celikom.armv7loaderhost. No Yandex code, audio,
network, account, files or Android permissions. A 32-bit ARMv7 library
makes this app an ARMv7-only test host, matching the original #170gpr
Yandex library ABI. It does not hook or modify Yandex.

For diagnosing LSPatch on real ARM hardware only. A signed patched
standalone app can be installed alongside official Yandex, never over it.
Play Protect must remain ON. If it blocks installation, STOP.
A successful launch is not proof of native Yandex hook or audible CELIKOM.


## Same-track Start/Stop source reload — W60 principle (OWN WAV only, 10.11.2026)

Experimental OWN-only ARMv7 audio app now includes **Start CELIKOM** and **Stop CELIKOM** for the same current synthetic A song. If our scoped own-module provides alternative 660 Hz, Stop reloads original 440 Hz and Start reloads the alternative. It uses **one** platform MediaPlayer; before any rebuild the old player is released, and the new one restores the pre-toggle play/pause state and current position after seek completes. If the audio module isn't available, it leaves original 440 Hz unchanged. Track B stays original; rapid toggles fence stale callbacks. No production Yandex/API, no user phone, account or files; no claim of gapless or audible Android Yandex replacement.

Sources: `OwnSameTrackReloadPlan.java`, `AudioSmokeScreen.java`. 50,020 synthetic test assertions, own ARMv7 build [#42830966825](https://github.com/manufact-test/nomusic/actions/runs/42830966825) SUCCESS and ARM64 Linux source-plan [#42831135970](https://github.com/manufact-test/nomusic/actions/runs/42831135970) SUCCESS. Code `a7f83f0ab836bbeeb12538c6a389c9569d326610`, backup `backup/android-windows-w60-owned-reload-armv7-arm64-ci-green-20261110`.


## Android API33 real OWN MediaPlayer runtime PASS (10.11.2026)

Exact source `bb26aca9652850c69fbd0896a26bec22601826b0`, rollback `backup/android-own-api33-real-mediaplayer-source-reload-pass-20261110`, [CI #42835181030 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42835181030). `-PcelikomOwnEmulator=true` creates an OWN x86_64 Android 13 emulator APK without unused JNI/NDK; normal ARMv7 JNI continues on default. `OwnAndroidMediaRuntimeProbe` only runs via exact OWN package + explicit adb `celikom_own_probe`. `ci/run_own_android_emulator_probe.sh` performs one-shell ADB launch. The real Android MediaPlayer callbacks verified synthetic same-track A 440↔660 Hz source reload with Pause/Seek/position and Next B, using `OwnSameTrackReloadPlan.decide`, no extra player. **No user-visible/audible Yandex audio proved**: test uses empty x86_64 emulator, noaudio, own WAV only, no account, permissions, signatures or vendor modification. Full explanation: `docs/android/ANDROID-OWN-API33-MEDIAPLAYER-RUNTIME-PASS-2026-11-10.md`.
