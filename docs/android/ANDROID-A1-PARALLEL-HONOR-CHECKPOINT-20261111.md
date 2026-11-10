# CELIKOM Android A1 — parallel clone / owner HONOR checkpoint (11.11.2026)

## Approved goal and no-damage contract

Keep original Yandex Music on the owner's HONOR 50 (NTH-NX9, Android 13) fully intact. The trial CELIKOM must have an INDEPENDENT package name / signer, install alongside official Yandex and ultimately expose the same native UI/player in one user-facing APK. No WebView, second player, DRM/Passport spoofing, disabling Play Protect or data migrations. No user APK is ready yet.

Working branch: `feature/android-parallel-clone-runtime-preflight-20261111`, derived from prior native A1. Frozen base: `backup/android-parallel-clone-pre-arttrace-20261111`; owner HONOR read-only gate backup `backup/android-parallel-honor-readonly-gate-ci-green-20261111`. The accepted Test.50, stable Android, Windows 0.24.9, extension and production remain unchanged.

## Verified code and runtime observations

- Previously installed 5 publisher-signed `ru.yandex.music` splits + five separately signed `pro.celikom.yandex.nativeclonelab` splits simultaneously on isolated translated Android 11 emulator. Separate package and certificate prevent INSTALL conflict, no original phone touched.
- Strong UI validation correctly FAILS: clone main exits `EXIT_SELF(0)` before Activity resume; the surviving `:AppMetrica` helper MUST NEVER be interpreted as functional Yandex UI. Publisher original main works.
- [CI run 42909721665](https://github.com/manufact-test/nomusic/actions/runs/42909721665) independently reconfirmed 5+5 install and original running, but clone main EXIT_SELF(0); standard Android shell profiling opt-in on LAB clone did not produce ART trace. It is not proof of an anti-tamper/permission cause.
- Added stricter MAIN-PID-only Throwable-class extraction from `E/F` log lines without emitting user/private log messages. This is follow-up diagnosis, not live audio mutation. A valid runtime conclusion must be taken only from the subsequent completed CI.
- Added `android/native-yandex-hooklab/probe_parallel_honor.py`: now OWNER HONOR 50 is deliberately accepted for READ-ONLY eligibility checks. Old `probe_arm_device.py` remains restricted to disposable devices for direct same-package LSPatch builds; NEVER install those over the owner's original. The new tool only checks version, ABI, installed original and separate clone package, never modifies anything, never guesses Play Protect verdict. [Synthetic/no-device CI 42910170271](https://github.com/manufact-test/nomusic/actions/runs/42910170271) SUCCESS.

## Competitor learning — source provenance caveat

Earlier analysis of owner-provided `ChromaSync-Clone-3.0.1.apk` (not repeatable in this chat: raw bytes unavailable) reported `app.chromasync.yamclone`, native `ru.yandex.music.YMApplication`, embedded original APK, MyWave injector and LSPatch `sigBypassLevel=2`. That last setting is **not an authorized technique for CELIKOM**: our master requirements prohibit bypassing publisher signing, Play Protect, DRM or authentication. Do not treat ChromaSync as a reliable no-bypass blueprint. Its own native login/audio and absence of credential exfiltration remain unverified by us.

## Honest current gates

1. Distinct installable package: **pass only on disposable Android 11 emulator, five splits**, not yet final one APK.
2. Native clone MAIN/foreground: **FAIL**, root reason unproven.
3. Exact native trackId+edition+generation through selected pre-prepare decoder: **not established**.
4. CELIKOM in-process source mutation / one audio clock / pause-seek-Next-MyWave: **not established**.
5. One APK + own stable signing + Google Play Protect ON and real HONOR install: **not established**.
6. Server entitlement, 3-day trial, safe login integration: existing server/client code exists but **not wired/tested in new native clone**.

NO user APK until at least a reliable native clone launch with independent package identity and safe installation checks. Do not change architecture to WebView or secondary MediaPlayer to make metrics green.

## Non-negotiable follow-up

After the owner audibly confirms stable LSPatch single-player substitutions and exact backup/artifact is frozen, the developer **must proactively remind the owner to begin Stage B: own independent injection adapter in place of LSPatch** before other feature work.
