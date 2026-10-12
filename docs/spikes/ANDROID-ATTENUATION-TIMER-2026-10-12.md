# Android 0.3.6: background attenuation deadline

Owner confirmed audible attenuation of real Yandex on Honor NTH-NX9, Android13 in 0.3.5. Report start1791811358628, attach1791811361696, finish1791811396021: attachment after3068ms, service elapsed37393ms, attenuation34325ms. Owner heard restoration only on reopening CELIKOM. This confirms session effect capability, not reliable seven-second release.

0.3.5 used main-looper Handler.postDelayed. Android documents that its uptime clock excludes deep sleep. The actual phone report cannot distinguish main-loop delay, sleep and manufacturer suspension. Do not label one of them a proven sole cause.

0.3.6 moves attach/release to a dedicated scheduled worker, synchronizes native effect ownership against service shutdown, and holds a non-reference-counted partial wake lock with a15-second maximum only during the10-second explicit probe. Every exit releases effect and lock; process death releases native resources. No battery-optimization exemption, exact-alarm permission or perpetual keepalive is requested. Ordinary WAKE_LOCK permission is added. Delay remains3seconds; maximum intended whole probe10seconds. Report adds monotonic attach_delay_ms, elapsed_ms, mute_elapsed_ms and wake-lock state. No assertion that manufacturer interference is impossible.

Emulator regression deliberately stalls the main/UI thread for10seconds after attachment while the service worker must finish near10seconds and release its lock. Owner must play music before launching, return to Yandex and leave CELIKOM closed until at least15seconds have passed, then provide report and audible observations. Physical test is pending. Track detection, pause/seek synchronization, alternate playback and full replacement remain unresolved.
