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
